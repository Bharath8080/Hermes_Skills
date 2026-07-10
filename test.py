#!/usr/bin/env python
"""
Simple combined Hermes + S3 service.

This single file does two jobs:

1. Manage USER.md and MEMORY.md files in MinIO/S3.
2. Provide a chat completions endpoint that reads those files,
   injects them into the request, and forwards the request to Hermes.

Run from C:/Users/homeu/H:
  python test.py

Base URL:
  http://localhost:8003

Main endpoints:
  GET    /health
  POST   /users/create
  GET    /users/{user_id}
  PUT    /users/{user_id}/user
  PUT    /users/{user_id}/memory
  POST   /users/{user_id}/memory/add
  DELETE /users/{user_id}
  POST   /v1/chat/completions
  POST   /v1/runs
  GET    /v1/runs/{run_id}
  POST   /v1/runs/{run_id}/stop
  POST   /v1/runs/{run_id}/approval
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import boto3
import httpx
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Load environment configurations
load_dotenv()


# Hermes API Server settings
HERMES_BASE_URL = os.getenv("HERMES_BASE_URL", "").rstrip("/")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

# S3-compatible storage settings
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL") or None
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

USER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ENTRY_DELIMITER = "\n§\n"
USER_CHAR_LIMIT = 1375
MEMORY_CHAR_LIMIT = 2200


app = FastAPI(title="Simple Combined Hermes S3 User Memory Service", version="0.1")

# Small in-process map so GET /v1/runs/{id} can update memory after a run completes.
RUN_INPUTS: dict[str, tuple[str, str]] = {}

s3_kwargs: dict[str, Any] = {
    "region_name": S3_REGION,
}
if S3_ENDPOINT_URL:
    s3_kwargs["endpoint_url"] = S3_ENDPOINT_URL
if S3_ACCESS_KEY_ID:
    s3_kwargs["aws_access_key_id"] = S3_ACCESS_KEY_ID
if S3_SECRET_ACCESS_KEY:
    s3_kwargs["aws_secret_access_key"] = S3_SECRET_ACCESS_KEY

s3 = boto3.client("s3", **s3_kwargs)


class CreateUserBody(BaseModel):
    user_id: str
    user_md: str = ""
    memory_md: str = ""


class UpdateBody(BaseModel):
    content: str


class AddMemoryBody(BaseModel):
    fact: str


# -------------------------
# Small helper functions
# -------------------------

def clean_user_id(user_id: str | None) -> str:
    user_id = (user_id or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    if not USER_ID_RE.fullmatch(user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id. Use letters, numbers, _ or - only")
    return user_id


def user_key(user_id: str) -> str:
    return f"{clean_user_id(user_id)}/USER.md"


def memory_key(user_id: str) -> str:
    return f"{clean_user_id(user_id)}/MEMORY.md"


def object_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def get_text(key: str, default: str | None = None) -> str:
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return obj["Body"].read().decode("utf-8")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "NoSuchBucket", "404", "NotFound"} and default is not None:
            return default
        raise HTTPException(status_code=404, detail=f"Object not found: {key}")


def put_text(key: str, content: str) -> None:
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=(content.rstrip() + "\n").encode("utf-8"),
        ContentType="text/markdown",
    )


def delete_if_exists(key: str) -> None:
    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=key)
    except ClientError:
        pass


def require_user_exists(user_id: str) -> None:
    if not object_exists(user_key(user_id)) and not object_exists(memory_key(user_id)):
        raise HTTPException(status_code=404, detail=f"User '{clean_user_id(user_id)}' does not exist in S3")


def read_user_context(user_id: str) -> str:
    user_md = get_text(user_key(user_id), default="")
    memory_md = get_text(memory_key(user_id), default="")

    return (
        "You are answering for exactly one authenticated user.\n"
        "Use ONLY the profile and memory below for this request.\n"
        "Do not use private facts from any other user.\n\n"
        f"Authenticated user id: {user_id}\n\n"
        "===== USER.md from S3 =====\n"
        f"{user_md.strip() or '(empty)'}\n\n"
        "===== MEMORY.md from S3 =====\n"
        f"{memory_md.strip() or '(empty)'}\n"
    )


def latest_user_text(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "user":
            continue

        content = msg.get("content", "")

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(str(part.get("text", "")))
            return "\n".join(parts)

    return ""


MEMORY_UPDATE_PROMPT = """
You update a user's S3-backed long-term memory.

Use the same rules as Hermes Agent's built-in memory tool:
- Save durable facts that survive across sessions.
- Keep entries compact and high-signal.
- Save proactively when the user states a preference, correction, personal detail, or stable project/environment fact.
- Priority: user preferences and corrections > environment facts > procedures.
- target "user" = who the user is: name, role, preferences, communication style, timezone, stable profile details.
- target "memory" = notes: project facts, environment facts, conventions, tool quirks, lessons, useful long-term context.
- Skip greetings, one-off requests, temporary details, raw data dumps, task progress, completed-work logs, TODO state, passwords, API keys, tokens, and secrets.
- If new info conflicts with old info, use replace or remove. Do not keep both conflicting facts.
- Prefer one compact batch of operations. If memory needs cleanup, combine remove/replace/add in one response.

Actions:
- add: add a new entry. Requires content.
- replace: replace an existing entry. Requires old_text and content. old_text must be a short unique substring of the old entry.
- remove: remove an existing entry. Requires old_text. old_text must be a short unique substring of the old entry.

Return ONLY valid JSON:
{
  "operations": [
    {"target":"user", "action":"add", "content":"..."},
    {"target":"user", "action":"replace", "old_text":"short unique substring", "content":"..."},
    {"target":"memory", "action":"remove", "old_text":"short unique substring"}
  ]
}

If nothing should change, return {"operations": []}.
""".strip()


def char_limit_for_target(target: str) -> int:
    return USER_CHAR_LIMIT if target == "user" else MEMORY_CHAR_LIMIT


def split_memory_lines(text: str) -> list[str]:
    """Read either Hermes-style § entries or simple bullet/newline entries."""
    if not text.strip():
        return []
    if "§" in text:
        raw_entries = text.split("§")
    else:
        raw_entries = text.splitlines()

    entries = []
    for entry in raw_entries:
        entry = entry.strip().lstrip("- ").strip()
        if entry and entry not in entries:
            entries.append(entry)
    return entries


def render_memory_lines(lines: list[str]) -> str:
    """Hermes-style storage: entries separated by §, no bullet needed."""
    clean = []
    for line in lines:
        line = line.strip().lstrip("- ").strip()
        if line and line not in clean:
            clean.append(line)
    return ENTRY_DELIMITER.join(clean)


def looks_unsafe_memory(content: str) -> bool:
    """Small safety guard. Hermes has a full scanner; this proxy keeps a simple one."""
    lowered = content.lower()
    blocked = [
        "api key", "apikey", "password", "secret", "token=", "bearer ",
        "-----begin", "private key", "ignore previous instructions",
        "system prompt", "developer message",
    ]
    return any(term in lowered for term in blocked)


def find_one_line(lines: list[str], old_text: str) -> int | None:
    old_text = (old_text or "").strip().lower()
    if not old_text:
        return None
    matches = [i for i, line in enumerate(lines) if old_text in line.lower()]
    if len(matches) == 1:
        return matches[0]
    return None


def parse_memory_operations(text: str) -> list[dict[str, Any]]:
    """Parse model JSON and keep only valid memory operations."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return []
        try:
            data = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return []

    valid = []
    for op in data.get("operations", []) if isinstance(data, dict) else []:
        target = str(op.get("target", "memory")).strip().lower()
        action = str(op.get("action", "")).strip().lower()
        content = str(op.get("content") or "").strip().lstrip("- ").strip()
        old_text = str(op.get("old_text") or "").strip()

        if target not in {"user", "memory"} or action not in {"add", "replace", "remove"}:
            continue
        if action == "add" and content:
            valid.append({"target": target, "action": action, "content": content})
        elif action == "replace" and old_text and content:
            valid.append({"target": target, "action": action, "old_text": old_text, "content": content})
        elif action == "remove" and old_text:
            valid.append({"target": target, "action": action, "old_text": old_text})

    return valid[:10]


def apply_operations(old_text: str, operations: list[dict[str, Any]], target: str) -> str:
    """
    Apply Hermes-style add/replace/remove.
    Safer behavior: replace/remove only happen on one unique old_text match.
    If replace does not match uniquely, we do NOT append, because that can create conflicts.
    """
    lines = split_memory_lines(old_text)

    for op in operations:
        action = str(op.get("action", "")).strip().lower()
        content = str(op.get("content") or "").strip().lstrip("- ").strip()
        old = str(op.get("old_text") or "").strip()

        if content and looks_unsafe_memory(content):
            continue

        if action == "add":
            if content and content not in lines:
                lines.append(content)

        elif action == "replace":
            if not old or not content:
                continue
            idx = find_one_line(lines, old)
            if idx is not None:
                lines[idx] = content

        elif action == "remove":
            if not old:
                continue
            idx = find_one_line(lines, old)
            if idx is not None:
                lines.pop(idx)

    rendered = render_memory_lines(lines)
    limit = char_limit_for_target(target)
    if len(rendered) > limit:
        # Keep the old content if the proposed update overflows.
        return render_memory_lines(split_memory_lines(old_text))
    return rendered


async def get_memory_operations(user_id: str, user_text: str) -> list[dict[str, Any]]:
    user_text = user_text.strip()
    if not user_text:
        return []

    old_user = get_text(user_key(user_id), default="")
    old_memory = get_text(memory_key(user_id), default="")

    body = {
        "model": "hermes-agent",
        "stream": False,
        "messages": [
            {"role": "system", "content": MEMORY_UPDATE_PROMPT},
            {
                "role": "user",
                "content": (
                    f"CURRENT USER.md:\n{old_user.strip() or '(empty)'}\n\n"
                    f"CURRENT MEMORY.md:\n{old_memory.strip() or '(empty)'}\n\n"
                    f"LATEST USER MESSAGE:\n{user_text}"
                ),
            },
        ],
        "session_id": f"s3-memory-updater-{user_id}",
        "conversation": f"s3-memory-updater-{user_id}",
    }

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{HERMES_BASE_URL}/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {HERMES_API_KEY}",
                    "Content-Type": "application/json",
                    "X-Hermes-Session-Key": f"s3-memory-updater-{user_id}",
                },
            )
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        operations = parse_memory_operations(content)
        if not operations and content.strip() != '{"operations": []}':
            print(f"Memory update skipped for {user_id}: invalid/empty operations: {content!r}")
        return operations
    except Exception as exc:
        print(f"Memory update skipped for {user_id}: {exc}")
        return []


async def update_user_memory_from_message(user_id: str, user_text: str) -> None:
    operations = await get_memory_operations(user_id, user_text)
    if not operations:
        return

    user_ops = [op for op in operations if str(op.get("target", "memory")).lower() == "user"]
    memory_ops = [op for op in operations if str(op.get("target", "memory")).lower() != "user"]

    if user_ops:
        old_user = get_text(user_key(user_id), default="")
        new_user = apply_operations(old_user, user_ops, "user")
        if new_user.strip() != old_user.strip():
            put_text(user_key(user_id), new_user)

    if memory_ops:
        old_memory = get_text(memory_key(user_id), default="")
        new_memory = apply_operations(old_memory, memory_ops, "memory")
        if new_memory.strip() != old_memory.strip():
            put_text(memory_key(user_id), new_memory)


# -------------------------
# Health endpoint
# -------------------------

@app.get("/health")
async def health():
    s3_ok = False
    hermes_ok = False
    detail: dict[str, Any] = {}

    try:
        buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
        s3_ok = S3_BUCKET in buckets
        detail["buckets"] = buckets
    except Exception as exc:
        detail["s3_error"] = str(exc)

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{HERMES_BASE_URL}/health",
                headers={"Authorization": f"Bearer {HERMES_API_KEY}"},
            )
        hermes_ok = resp.status_code == 200
        try:
            detail["hermes"] = resp.json()
        except Exception:
            detail["hermes"] = resp.text
    except Exception as exc:
        detail["hermes_error"] = str(exc)

    return {
        "status": "ok",
        "proxy": "ok",
        "s3_ok": s3_ok,
        "hermes_ok": hermes_ok,
        "s3_endpoint": S3_ENDPOINT_URL,
        "bucket": S3_BUCKET,
        "hermes_base_url": HERMES_BASE_URL,
        "endpoints": [
            "GET /health",
            "POST /users/create",
            "GET /users/{user_id}",
            "PUT /users/{user_id}/user",
            "PUT /users/{user_id}/memory",
            "POST /users/{user_id}/memory/add",
            "DELETE /users/{user_id}",
            "POST /v1/chat/completions",
            "GET /v1/capabilities",
            "POST /v1/runs",
            "GET /v1/runs/{run_id}",
            "POST /v1/runs/{run_id}/stop",
            "POST /v1/runs/{run_id}/approval",
        ],
        "detail": detail,
    }


# -------------------------
# USER.md / MEMORY.md API
# -------------------------

@app.post("/users/create")
def create_user(body: CreateUserBody):
    user_id = clean_user_id(body.user_id)
    put_text(user_key(user_id), body.user_md)
    put_text(memory_key(user_id), body.memory_md)

    return {
        "created": True,
        "user_id": user_id,
        "bucket": S3_BUCKET,
        "user_key": user_key(user_id),
        "memory_key": memory_key(user_id),
    }


@app.get("/users/{user_id}")
def get_user(user_id: str):
    require_user_exists(user_id)
    user_id = clean_user_id(user_id)

    return {
        "user_id": user_id,
        "bucket": S3_BUCKET,
        "user_key": user_key(user_id),
        "memory_key": memory_key(user_id),
        "USER.md": get_text(user_key(user_id), default=""),
        "MEMORY.md": get_text(memory_key(user_id), default=""),
    }


@app.put("/users/{user_id}/user")
def update_user_md(user_id: str, body: UpdateBody):
    require_user_exists(user_id)
    user_id = clean_user_id(user_id)
    put_text(user_key(user_id), body.content)

    return {
        "updated": True,
        "user_id": user_id,
        "bucket": S3_BUCKET,
        "key": user_key(user_id),
    }


@app.put("/users/{user_id}/memory")
def update_memory_md(user_id: str, body: UpdateBody):
    require_user_exists(user_id)
    user_id = clean_user_id(user_id)
    put_text(memory_key(user_id), body.content)

    return {
        "updated": True,
        "user_id": user_id,
        "bucket": S3_BUCKET,
        "key": memory_key(user_id),
    }


@app.post("/users/{user_id}/memory/add")
def add_memory_fact(user_id: str, body: AddMemoryBody):
    require_user_exists(user_id)
    user_id = clean_user_id(user_id)

    fact = body.fact.strip().lstrip("- ").strip()
    if not fact:
        raise HTTPException(status_code=400, detail="fact cannot be empty")

    old_memory = get_text(memory_key(user_id), default="")
    new_memory = apply_operations(
        old_memory,
        [{"action": "add", "content": fact}],
        "memory",
    )
    put_text(memory_key(user_id), new_memory)

    return {
        "added": True,
        "user_id": user_id,
        "bucket": S3_BUCKET,
        "key": memory_key(user_id),
        "fact": fact,
    }


@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    require_user_exists(user_id)
    user_id = clean_user_id(user_id)

    delete_if_exists(user_key(user_id))
    delete_if_exists(memory_key(user_id))

    return {
        "deleted": True,
        "user_id": user_id,
        "bucket": S3_BUCKET,
    }


# -------------------------
# Hermes API forwarding helpers
# -------------------------

async def forward_to_hermes(method: str, path: str, body: dict[str, Any] | None = None, session_key: str | None = None):
    headers = {
        "Authorization": f"Bearer {HERMES_API_KEY}",
        "Content-Type": "application/json",
    }
    if session_key:
        headers["X-Hermes-Session-Key"] = session_key

    async with httpx.AsyncClient(timeout=None) as client:
        if method == "GET":
            return await client.get(f"{HERMES_BASE_URL}{path}", headers=headers)
        if method == "POST":
            return await client.post(f"{HERMES_BASE_URL}{path}", json=body or {}, headers=headers)
        raise HTTPException(status_code=500, detail=f"Unsupported method: {method}")


@app.get("/v1/capabilities")
async def capabilities():
    try:
        resp = await forward_to_hermes("GET", "/v1/capabilities")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Hermes API server is not reachable at {HERMES_BASE_URL}")
    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}
    return JSONResponse(status_code=resp.status_code, content=content)


@app.post("/v1/runs")
async def start_run(request: Request, x_user_id: str | None = Header(None)):
    user_id = clean_user_id(x_user_id)
    require_user_exists(user_id)

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    task = str(body.get("input") or body.get("task") or "").strip()
    if not task:
        raise HTTPException(status_code=400, detail="Body must contain input")

    user_context = read_user_context(user_id)
    old_instructions = str(body.get("instructions") or "").strip()
    body["instructions"] = (
        f"{user_context}\n\n"
        f"Additional instructions from client:\n{old_instructions or '(none)'}"
    )
    body["session_id"] = body.get("session_id") or f"s3-local-user-{user_id}"

    try:
        resp = await forward_to_hermes(
            "POST",
            "/v1/runs",
            body,
            session_key=f"s3-local-user-{user_id}",
        )
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Hermes API server is not reachable at {HERMES_BASE_URL}")

    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}

    run_id = content.get("run_id") or content.get("id")
    if run_id:
        RUN_INPUTS[str(run_id)] = (user_id, task)

    return JSONResponse(status_code=resp.status_code, content=content)


@app.get("/v1/runs/{run_id}")
async def get_run(run_id: str):
    try:
        resp = await forward_to_hermes("GET", f"/v1/runs/{run_id}")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Hermes API server is not reachable at {HERMES_BASE_URL}")

    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}

    # If the run is complete, update S3 memory from the original task once.
    if str(content.get("status", "")).lower() in {"completed", "complete", "done"}:
        saved = RUN_INPUTS.pop(run_id, None)
        if saved:
            user_id, task = saved
            await update_user_memory_from_message(user_id, task)

    return JSONResponse(status_code=resp.status_code, content=content)


@app.post("/v1/runs/{run_id}/stop")
async def stop_run(run_id: str):
    try:
        resp = await forward_to_hermes("POST", f"/v1/runs/{run_id}/stop", {})
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Hermes API server is not reachable at {HERMES_BASE_URL}")
    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}
    return JSONResponse(status_code=resp.status_code, content=content)


@app.post("/v1/runs/{run_id}/approval")
async def approve_run(run_id: str, request: Request):
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    try:
        resp = await forward_to_hermes("POST", f"/v1/runs/{run_id}/approval", body)
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Hermes API server is not reachable at {HERMES_BASE_URL}")
    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}
    return JSONResponse(status_code=resp.status_code, content=content)


# -------------------------
# Chat completions proxy API
# -------------------------

@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    x_user_id: str | None = Header(None),
):
    user_id = clean_user_id(x_user_id)

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    messages = body.get("messages")
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="Body must contain messages array")

    text = latest_user_text(messages)
    user_context = read_user_context(user_id)

    body["messages"] = [{"role": "system", "content": user_context}] + messages
    body["session_id"] = f"s3-local-user-{user_id}"
    body.setdefault("conversation", f"s3-local-user-{user_id}")

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{HERMES_BASE_URL}/v1/chat/completions",
                json=body,
                headers={
                    "Authorization": f"Bearer {HERMES_API_KEY}",
                    "Content-Type": "application/json",
                    "X-Hermes-Session-Key": f"s3-local-user-{user_id}",
                },
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail=f"Hermes API server is not reachable at {HERMES_BASE_URL}")

    try:
        response_content = resp.json()
    except Exception:
        response_content = {"raw": resp.text}

    # Memory write-back happens after the main answer.
    # Hermes decides add/replace/remove; this proxy only writes to S3.
    await update_user_memory_from_message(user_id, text)

    return JSONResponse(status_code=resp.status_code, content=response_content)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "8003"))

    print("Simple Combined Hermes S3 User Memory Service")
    print(f"  URL:      http://{host}:{port}")
    print(f"  S3 API:   {S3_ENDPOINT_URL}")
    print(f"  Bucket:   {S3_BUCKET}")
    print(f"  Hermes:   {HERMES_BASE_URL}")
    print("  Required chat header: X-User-Id")
    uvicorn.run(app, host=host, port=port)

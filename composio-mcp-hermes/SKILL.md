---
name: composio-mcp-hermes
description: "Use Composio MCP tools (mcp_composio_*) natively in Hermes Agent to connect 850+ apps — Gmail, Google Docs, Weather, WhatsApp, Hacker News, and more. Covers the standard 4-step workflow: search tools → check connections → get schemas → execute. User prefers using Composio for external integrations over manual API calls or web scraping."
---

# Composio MCP in Hermes Agent

Composio provides MCP-based tool access to 850+ apps. In Hermes Agent, these are available as native `mcp_composio_*` tools — no separate CLI or mcporter needed.

## User preference: always try Composio first

When the user asks to interact with an external service (email, weather, messaging, docs, news, calendar, etc.), **always search Composio tools first** via `mcp_composio_COMPOSIO_SEARCH_TOOLS` before falling back to manual API calls, web scraping, browser automation, or other approaches. The user has explicitly directed this workflow.

## Be concise ("lite" mode)

The user prefers **concise, direct responses** — skip explanations, avoid verbose formatting, get to the point. Present results in compact tables or bullet lists. No preamble or signposting.

## Standard 4-Step Workflow

### Step 1: Discover Tools

```python
mcp_composio_COMPOSIO_SEARCH_TOOLS(
    queries=[{
        "use_case": "normalized description of what the user wants",
        "known_fields": "key:value hints"
    }],
    session={"generate_id": True}
)
```

Key fields in the response:
- **`recommended_plan_steps`** — follow these in order
- **`primary_tool_slugs`** — which tools to call
- **`toolkit_connection_statuses`** — `has_active_connection: true/false`
- **`session.id`** — **save this** and pass it to all subsequent meta tool calls
- **`known_pitfalls`** — read these before executing

### Step 2: Handle Connection (if needed)

If `has_active_connection: false`:

```python
mcp_composio_COMPOSIO_MANAGE_CONNECTIONS(
    toolkits=[{"name": "toolkit_slug", "action": "add"}],
    session_id="<session_id>"
)
```

Show the `redirect_url` as a clickable link, then:

```python
mcp_composio_COMPOSIO_WAIT_FOR_CONNECTIONS(
    toolkits=["toolkit_slug"],
    mode="any",
    session_id="<session_id>"
)
```

Some toolkits are **always active** with no auth needed:
- `composio_search` (web search, news, trends)
- `weathermap` (current weather via OpenWeatherMap)

### Step 3: Get Schemas (if schemaRef)

Some tools have `hasFullSchema: false` with a `schemaRef`. Load their schema:

```python
mcp_composio_COMPOSIO_GET_TOOL_SCHEMAS(
    tool_slugs=["TOOL_SLUG"],
    session_id="<session_id>"
)
```

### Step 4: Execute Tools

Batch independent operations together:

```python
mcp_composio_COMPOSIO_MULTI_EXECUTE_TOOL(
    tools=[{
        "tool_slug": "TOOL_SLUG",
        "arguments": {...}
    }],
    current_step="STEP_NAME",
    current_step_metric="progress",
    session_id="<session_id>",
    sync_response_to_workbench=False
)
```

## Common Tool Quick Reference

### Gmail (`gmail` toolkit)
| Task | Tool | Key args |
|------|------|----------|
| Inbox listing | `GMAIL_FETCH_EMAILS` | `label_ids=["INBOX"]`, `max_results=N`, `verbose=True` |
| Send email | `GMAIL_SEND_EMAIL` | `recipient_email="..."`, `subject="..."`, `body="..."` |
| Full message | `GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID` | `message_id="..."`, `format="full"` |
| Mark as read | `GMAIL_BATCH_MODIFY_MESSAGES` | `messageIds=[...]`, `removeLabelIds=["UNREAD"]` |

**Pitfalls**: Hard cap 500/page. `nextPageToken` may appear even with small `max_results`. Null-check `data.messages` before iterating. Bodies are base64url-encoded. For `GMAIL_SEND_EMAIL`, at least one of `to`/`recipient_email`, `cc`, or `bcc` must be provided; either `subject` or `body` must be provided. Use `is_html=True` for HTML bodies.

### Reddit (`reddit` toolkit)
| Task | Tool | Key args |
|------|------|----------|
| Search posts | `REDDIT_SEARCH_ACROSS_SUBREDDITS` | `search_query="..."`, `limit=N`, `sort="relevance"` |
| Get comments | `REDDIT_RETRIEVE_POST_COMMENTS` | `article="base36_id"` (from URL, no `t3_` prefix) |

**Pitfalls**: Response shape varies — may be `posts[]` array or `data.children[].data`. Use `data.after` for pagination; stop when null/empty. Comments are in `comments_listing.data.children[].data` with nested `replies`. Filter out `[deleted]`/`[removed]` bodies. Rate limit ~1-2 req/s; HTTP 429 = throttle.

### Weather (`weathermap` toolkit — always active)
| Step | Tool | Example |
|------|------|---------|
| Geocode | `WEATHERMAP_GEOCODE_LOCATION` | `q="Srikakulam,IN"` |
| Current | `WEATHERMAP_WEATHER` | `location="Srikakulam,IN"` |

Temps in **Kelvin** by default. Convert: `°C = K - 273.15`. Timezone offset in seconds.

### WhatsApp (`whatsapp` toolkit)
| Task | Tool | Key args |
|------|------|----------|
| Send text | `WHATSAPP_SEND_MESSAGE` | `phone_number_id`, `to_number` (no +), `text` |
| List numbers | `WHATSAPP_GET_PHONE_NUMBERS` | `limit=N` |

**Cannot list contacts** — WhatsApp contacts are stored on the phone, not the API. Recipient must have initiated conversation in last 24h or use template messages. **Pitfall**: WABA ID must be configured correctly or phone number listing fails.

### Google Docs (`googledocs` toolkit)
| Task | Tool | Key args |
|------|------|----------|
| Search docs | `GOOGLEDOCS_SEARCH_DOCUMENTS` | `query="name contains 'term'"`, `max_results=20` |
| Read content | `GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT` | `document_id="..."` |
| Create doc | `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN` | `title="..."`, `markdown_text="..."` |

### News / Hacker News (`composio_search` toolkit — always active)
| Task | Tool | Key args |
|------|------|----------|
| News search | `COMPOSIO_SEARCH_NEWS` | `query="topic"`, `when="m"` (d/w/m/y) |
| Web search | `COMPOSIO_SEARCH_WEB` | `query="site:news.ycombinator.com topic"` |
| Fetch content | `COMPOSIO_SEARCH_FETCH_URL_CONTENT` | `urls=["..."], summary=True, max_characters=3000` |

**Pitfalls**: Successful calls can return empty `news_results` — broaden query or `when` window. Per-URL fetch failures can hide behind overall success — check `statuses`.

## Handling Large Responses (Remote File Pattern)

When COMPOSIO_MULTI_EXECUTE_TOOL returns a large response (over ~15K tokens), it auto-saves to a remote sandbox file. The inline response includes `structure_info` (schema) and `data_preview` (samples) — use these to understand the shape before processing.

**Workflow:**
1. Set `sync_response_to_workbench=True` to save to sandbox
2. Read `structure_info` from inline response to know the data shape
3. Use `COMPOSIO_REMOTE_WORKBENCH` to parse the file:
   ```python
   file_data = json.load(open("/mnt/files/mex/<file>.json"))
   # Access results: file_data['results'][i]['response']['data']
   ```
4. Or use `COMPOSIO_REMOTE_BASH_TOOL` with `jq` for quick inspection

**Pitfall**: Data paths vary by tool. Always check `structure_info.data_structure` first — some have `data.messages`, others have `data.data.posts`. Don't hardcode.

### Autype (Document/PDF Generation)

Autype renders Markdown to pixel-perfect PDFs, DOCX, and ODT. Added as an MCP server with API key header in config.yaml. See `references/autype-pdf-generation.md` for full workflow.

Key tools:
- `render_markdown` — one-shot Markdown → PDF (preferred)
- `render_document` — full JSON document schema render
- Builder tools — iterative multi-step document assembly

**Tip**: For production PDFs, use `render_markdown` with `content` (full Markdown), `document` (A4, portrait, margins 2cm), and `defaults` (styling). Download via `curl -L -o output.pdf <downloadUrl>`.

## MCP Server Configuration

Adding an HTTP MCP server with custom headers requires editing `config.yaml` directly under `mcp_servers:`:

```yaml
mcp_servers:
  server_name:
    connect_timeout: 60
    timeout: 180
    type: http
    url: https://example.com/mcp
    headers:
      X-API-Key: key_value_here
```

The `hermes mcp add` command does NOT support `--headers` for HTTP servers — it only supports `--url`, `--auth {oauth|header}`, and `--env` (for stdio servers). For HTTP servers with API key headers, edit config.yaml directly.

After adding, reload with `/reload-mcp` in session or `hermes mcp list` to verify.
---
name: serper-web-search
description: Search web, images, news, maps, reviews, shopping, videos, places via Google Serper API
version: 1.2
author: Bharath Munakala
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [search, web, images, news, maps, shopping, api]
    related_skills: [tavily-web-search]
    fallback_for_toolsets: [search]
    config:
      - key: serper-web-search.default_gl
        description: Default country code for search results
        default: "in"
        prompt: Default country code (e.g., in, us, uk)
      - key: serper-web-search.default_location
        description: Default city/location for geo-specific searches
        default: "Srikakulam"
        prompt: Default search location (city name)
required_environment_variables:
  - name: SERPER_API_KEY
    prompt: Serper API key
    help: Get one at https://serper.dev
    required_for: All search operations
---

# Serper API — Google Search via API

## When to Use
- **Web search** with structured JSON (knowledge graph + organic results)
- **Image search** (Google Images)
- **News articles** with dates, source, thumbnails
- **Maps/Places** — restaurants, hotels, local businesses
- **Reviews** — business ratings & customer feedback
- **Shopping** — e-commerce product prices & availability
- **Videos** — YouTube & video content search
- **Local business info** — address, hours, phone
- **Fallback** when the native `web_search` tool or a search MCP (Tavily) is unavailable or insufficient

## Quick Reference

| Endpoint | Path | Use Case |
|----------|------|----------|
| `search` | `/search` | Web search + knowledge graph |
| `images` | `/images` | Google Image search |
| `news` | `/news` | News articles with dates & sources |
| `maps` | `/maps` | Maps, places, local business |
| `reviews` | `/reviews` | Business reviews & ratings |
| `shopping` | `/shopping` | E-commerce & product prices |
| `videos` | `/videos` | Video search results |
| `places` | `/places` | Local business info |

## Procedure

### 1. Set the API key
Ensure `SERPER_API_KEY` is exported in the session environment.

### 2. Invoke the CLI tool

The bundled script lives at:

    ${HERMES_SKILL_DIR}/scripts/search.py

Use it with the endpoint name as the first argument and the query as the second:

```bash
python ${HERMES_SKILL_DIR}/scripts/search.py search "query" --gl in --pretty
```

### 3. Examples by endpoint

**Web search** — general queries, knowledge graph:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py search "apple stock price" --gl us --num 10 --pretty
```

**Images** — people, products, landmarks:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py images "Max Verstappen Red Bull" --gl us --num 8 --pretty
```

**News** — current events with dates:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py news "KL Rahul IPL" --gl in --page 2 --num 10 --pretty
```

**Maps** — restaurants, hotels, places:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py maps "restaurants" --location "Srikakulam" --gl in --pretty
```

**Reviews** — business ratings:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py reviews "taj hotel" --gl in --pretty
```

**Shopping** — e-commerce prices:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py shopping "mechanical keyboard" --gl in --num 20 --pretty
```

**Videos** — YouTube search results:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py videos "python tutorial" --gl us --pretty
```

**Places** — local business info:
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py places "coffee shops" --gl in --pretty
```

**List all endpoints:**
```bash
python ${HERMES_SKILL_DIR}/scripts/search.py help
```

### 4. CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--gl` | `in` | Country code |
| `--page` | `1` | Page number |
| `--num` | `10` | Results per page |
| `--location` | — | City for geo-specific search |
| `--pretty` | — | Pretty-print JSON output |

### 5. Direct curl (alternative)

```bash
curl -s -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "query", "gl": "in", "page": 1}' | jq .
```

## Response Structure

```json
{
  "searchParameters": { "q": "query", "gl": "in", "page": 1 },
  "knowledgeGraph": {
    "title": "Entity name",
    "type": "Category",
    "description": "Summary",
    "attributes": {"Key": "Value"}
  },
  "organic": [
    { "title": "Result", "link": "https://...", "snippet": "Desc", "position": 1 }
  ],
  "images": [],
  "news": [],
  "shopping": []
}
```

## Pitfalls
- `X-API-KEY` header is required — not a query param or URL
- Free tier: ~100 searches/month (check https://serper.dev dashboard)
- Country code (`gl`) must be valid: `in`, `us`, `uk`, `au`, `de`, etc.
- Vague queries → check `knowledgeGraph` first for instant answers
- Pagination starts at page=1; increment for next page
- `location` param only works with `/maps` endpoint
- 403 = invalid/expired API key; 429 = rate limit hit

## Verification
- `python ${HERMES_SKILL_DIR}/scripts/search.py help` lists all 8 endpoints
- `python ${HERMES_SKILL_DIR}/scripts/search.py search "test" --gl us --pretty` returns valid JSON with `organic` array
- Each endpoint returns its own data type (images in `/images`, news in `/news`, etc.)
- Knowledge graph appears for brands, people, and organizations
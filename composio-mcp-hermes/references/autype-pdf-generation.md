# Autype MCP — Document & PDF Generation

Autype is an MCP server for generating pixel-perfect PDFs, DOCX, and ODT documents. Supports Markdown input, template variables, and iterative builder workflows. EU-hosted, AI-native.

## Adding the MCP Server

**Config edit required** — `hermes mcp add` does NOT support `--headers` for HTTP servers with API keys.

Edit `config.yaml` under `mcp_servers:`:

```yaml
mcp_servers:
  autype:
    connect_timeout: 60
    timeout: 180
    type: http
    url: https://mcp.autype.com/mcp/
    headers:
      X-API-Key: <your_api_key_here>
```

Reload with `/reload-mcp` in session or run `hermes mcp list` to verify. 17 tools discovered.

## Two Workflows

### Quick: `render_markdown` (preferred for most cases)

Render Extended Markdown directly to PDF/DOCX/ODT in one call:

Parameters:
- `content` — full Markdown string (headings, tables, lists, math, code, charts)
- `document` — settings object (must include `type`, optional: `size`, `orientation`, margins, `filename`)
- `defaults` — global styling (fontFamily, fontSize, color, lineHeight, spacing, styles, header, footer)
- `variables` — key-value pairs for `{{varName}}` substitution

Key style schema differences from HTML/CSS intuition:
- **fontWeight** ("normal"|"bold") not "bold" boolean
- **Header/footer** use object format: `{type: "text", content: [{text: "..."}]}`
- **Inline styles** not supported on text elements — use `styles` in defaults
- **Spacer** takes only `{type: "spacer", height: N}` (no `text` property)

### Iterative: Builder Workflow (multi-step document assembly)

1. `builder_create_session` — create session with document settings
2. `builder_update_defaults` — set global styling
3. `builder_add_section` — add content sections (type="flow" for multi-page, type="page" for single positioned)
4. `builder_render` — render and get download URL
5. `builder_delete_session` — cleanup

## Table Styling in Defaults

```yaml
styles:
  table:
    borders:
      outer: {width: 1, color: "#cccccc", style: solid}
      inner: {width: 0.5, color: "#dddddd", style: solid}
    cellPadding: {top: 4, bottom: 4, left: 6, right: 6}
    header:
      backgroundColor: "#0f3460"
      color: "#ffffff"
      fontSize: 9
      fontWeight: bold
    rows:
      alternateBackgroundColor: "#f0f0f5"
      fontSize: 9
```

## Example: Full PDF Generation Pipeline

```
1. Research data (via COMPOSIO_SEARCH_WEB or other sources)
2. Compose Markdown with tables, headings, and structured content
3. Call render_markdown with content + document settings + defaults
4. Download PDF via the returned downloadUrl (curl -L -o output.pdf)
5. Result is a production-ready, multi-page professional PDF
```

## Response Schema

```json
{
  "jobId": "uuid",
  "status": "COMPLETED",
  "downloadUrl": "https://api.autype.com/.../download?token=...",
  "filename": "document.pdf"
}
```

Jobs complete near-instantly for Markdown renders. Download URL expires after ~1 hour.
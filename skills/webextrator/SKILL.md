---
name: webextrator
description: Render and extract web page content via AceDataCloud's WebExtrator API. Use when scraping a page's final rendered HTML, or extracting typed structured data (Article, Product, Recipe, Video, Discussion, Job) plus clean markdown/text from any URL. Real headless Chromium with schema.org + LLM extraction.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-webextrator for tool-use.
---

# WebExtrator Web Render & Extract

Render and extract web content through AceDataCloud's WebExtrator API — real headless Chromium plus a three-tier extraction pipeline (schema.org JSON-LD mapper → LLM typed extractor → Readability/markdown fallback).

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/webextrator/extract \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "expected_type": "general"}'
```

Returns synchronously in seconds — no task polling needed.

## Endpoints

| Path | Purpose |
|------|---------|
| `POST /webextrator/render` | Headless Chromium render → raw HTML + clean text + title |
| `POST /webextrator/extract` | Render + structured extraction (schema.org + LLM types) + markdown |
| `POST /webextrator/tasks` | Look up historical render/extract task envelopes (7-day retention, free) |

## Workflows

### 1. Extract typed content

```json
POST /webextrator/extract
{
  "url": "https://example.com",
  "expected_type": "general"
}
```

Real response (trimmed):

```json
{
  "success": true,
  "task_id": "604b1cfb-6c5a-42c9-b900-a281e1b9c3c5",
  "trace_id": "f2a7c0b0-c17c-4bc9-b6e7-9c59746dd366",
  "elapsed": 0.003,
  "data": {
    "kind": "extract",
    "url": "https://example.com",
    "finalUrl": "https://example.com/",
    "contentType": "general",
    "title": "Example Domain",
    "description": "This domain is for use in documentation examples without needing permission. Avoid use in operations.",
    "language": "en",
    "images": [],
    "links": [],
    "markdown": "...",
    "text": "...",
    "structured": { "schemaOrg": {}, "openGraph": {}, "jsonLd": [] }
  }
}
```

### 2. Render raw HTML

```json
POST /webextrator/render
{
  "url": "https://example.com",
  "wait_until": "networkidle",
  "block_resources": ["image", "media", "font"]
}
```

Returns `data.html`, `data.text`, `data.title`, `data.status`, `data.finalUrl`.

### 3. Look up a task

```json
POST /webextrator/tasks
{
  "action": "retrieve",
  "id": "604b1cfb-6c5a-42c9-b900-a281e1b9c3c5"
}
```

## Parameters

### Render & Extract (shared)

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | Yes | Page URL to render (`http(s)://`) |
| `wait_until` | No | `load` / `domcontentloaded` / `networkidle` / `commit` (default `networkidle`) |
| `timeout` | No | Navigation timeout in seconds (default 30) |
| `delay` | No | Extra wait in seconds after `wait_until` (for SPAs) |
| `wait_for_selector` | No | CSS selector to wait for before ready |
| `block_resources` | No | Drop `image`/`font`/`media`/`stylesheet`/`xhr`/`fetch` |
| `headers` | No | Extra request headers for the target site |
| `cookies` | No | Cookies to install before navigation |
| `mode` | No | `sync` (default) or `async` (returns job id) |
| `callback_url` | No | Posted the final envelope when `mode=async` |
| `bypass_cache` | No | Skip the Redis result cache for this request |
| `cache_ttl_seconds` | No | Override cache TTL; `0` disables caching |

### Extract-only

| Parameter | Required | Description |
|-----------|----------|-------------|
| `expected_type` | No | `product` / `article` / `general` — skips the heuristic |
| `enable_llm` | No | Allow LLM extractor when schema.org found nothing (default false) |

### Tasks

| Parameter | Required | Description |
|-----------|----------|-------------|
| `action` | Yes | `retrieve` (single) or `retrieve_batch` (many) |
| `id` / `trace_id` | one of | For `retrieve` |
| `ids` / `trace_ids` | one of | For `retrieve_batch` |

## Gotchas

- Parameters use **snake_case** (`wait_until`, `block_resources`), not camelCase
- Cache hits are still billed; identical URLs return in ~0.003s
- `expected_type` only allows `product`/`article`/`general` — typed kinds (recipe/video/job) are detected automatically from schema.org
- `enable_llm` has no effect when the page ships schema.org JSON-LD — the deterministic mapper wins for free
- Tasks API is free and retains records for 7 days only
- `cache_ttl_seconds: 0` means "do not cache" — use `bypass_cache` to skip read

> **MCP:** `pip install mcp-webextrator` | Hosted: `https://webextrator.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

---
name: webextrator
description: Extract structured content or render web pages via AceDataCloud WebExtrator API. Use when scraping product pages, articles, or any web content; rendering JavaScript-heavy pages; or retrieving previously created tasks. Supports async callbacks and resource blocking for speed.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# WebExtrator — Web Render & Extract

Extract structured content from web pages or render JavaScript-heavy pages through AceDataCloud's WebExtrator API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/webextrator/extract \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amazon.com/dp/B0C1234567", "expected_type": "product"}'
```

## Workflows

### 1. Extract Structured Content

Parse a web page and return structured data (title, description, markdown, images, links, and type-specific fields like price or rating).

```json
POST /webextrator/extract
{
  "url": "https://www.amazon.com/dp/B0C1234567",
  "expected_type": "product",
  "enable_llm": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "kind": "extract",
    "url": "https://www.amazon.com/dp/B0C1234567",
    "contentType": "product",
    "title": "Acme Widget",
    "markdown": "# Acme Widget\n...",
    "structured": { "price": 19.99, "currency": "USD", "rating": 4.5 }
  }
}
```

### 2. Render a Web Page

Load a URL in a headless browser and return the fully rendered HTML and text content.

```json
POST /webextrator/render
{
  "url": "https://example.com",
  "wait_until": "networkidle",
  "block_resources": ["image", "font"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "kind": "render",
    "url": "https://example.com",
    "title": "Example Domain",
    "html": "<!DOCTYPE html>...",
    "text": "Example Domain ..."
  }
}
```

### 3. Async with Callback

For slow pages, provide a `callback_url` to receive the result asynchronously.

```json
POST /webextrator/extract
{
  "url": "https://example.com/heavy-page",
  "callback_url": "https://your.server.com/webhook"
}
```

### 4. Query Task Status

Retrieve a previously created task by its ID.

```json
POST /webextrator/tasks
{
  "action": "retrieve",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Retrieve multiple tasks at once:

```json
POST /webextrator/tasks
{
  "action": "retrieve_batch",
  "ids": ["id-1", "id-2"]
}
```

## Parameters

### `/webextrator/extract`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `url` | string | URL of the web page to extract (required) |
| `expected_type` | `"product"`, `"article"`, `"general"` | Page type hint to optimize extraction |
| `enable_llm` | `true` / `false` | Enable LLM-based semantic normalization (default: false) |
| `wait_until` | `"load"`, `"domcontentloaded"`, `"networkidle"`, `"commit"` | Page load wait condition (default: networkidle) |
| `timeout` | number | Total timeout in seconds (default: 30) |
| `delay` | number | Extra delay in seconds after page load, before extraction |
| `wait_for_selector` | string | CSS selector to wait for before extracting |
| `block_resources` | array | Resource types to block: `"image"`, `"font"`, `"media"`, `"stylesheet"`, `"xhr"`, `"fetch"` |
| `headers` | object | Extra HTTP headers to send with the request |
| `user_agent` | string | Override the User-Agent header |
| `callback_url` | string | If set, processes asynchronously and POSTs result here |

### `/webextrator/render`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `url` | string | URL of the web page to render (required) |
| `wait_until` | `"load"`, `"domcontentloaded"`, `"networkidle"`, `"commit"` | Page load wait condition (default: networkidle) |
| `timeout` | number | Total timeout in seconds (default: 30) |
| `delay` | number | Extra delay in seconds after page load, before capturing HTML |
| `wait_for_selector` | string | CSS selector to wait for before capturing |
| `block_resources` | array | Resource types to block (same options as extract) |
| `headers` | object | Extra HTTP headers to send with the request |
| `user_agent` | string | Override the User-Agent header |
| `callback_url` | string | If set, processes asynchronously and POSTs result here |

### `/webextrator/tasks`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"retrieve"`, `"retrieve_batch"` | Operation type (required) |
| `id` | string | Task UUID — used by `retrieve` |
| `trace_id` | string | Trace UUID — alternative lookup for `retrieve` |
| `ids` | array | List of task UUIDs — used by `retrieve_batch` |
| `trace_ids` | array | List of trace UUIDs — used by `retrieve_batch` |
| `offset` | number | Pagination offset for `retrieve_batch` (default: 0) |
| `limit` | number | Pagination limit for `retrieve_batch` (default: 12) |

## Gotchas

- A `429` response means the backend queue is busy — retry later or use `callback_url` for async processing
- A `504` response means the operation exceeded the timeout — increase `timeout` or use `callback_url`
- `block_resources: ["image", "font"]` significantly speeds up page load for text-heavy extraction
- `enable_llm: true` adds an extra LLM normalization step — use for complex or noisy pages where default extraction is insufficient
- `wait_for_selector` is useful for single-page apps that render content after the initial load event

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

---
name: webextrator
description: Extract structured content or render full HTML from any web page via AceDataCloud's WebExtrator API. Use when scraping product data, articles, or any web content; rendering JavaScript-heavy pages; or retrieving page HTML for downstream processing.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# WebExtrator — Web Render & Extract

Scrape and render web pages through AceDataCloud's WebExtrator API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/webextrator/extract \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amazon.com/dp/B0C1234567", "expected_type": "product"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Pass `callback_url` to process asynchronously; poll task status via `POST /webextrator/tasks` with `{"action": "retrieve", "id": "<task_id>"}`.

## Workflows

### 1. Extract Structured Content

Parse a web page and return structured data (title, description, images, links, markdown, and type-specific fields).

```json
POST /webextrator/extract
{
  "url": "https://www.amazon.com/dp/B0C1234567",
  "expected_type": "product",
  "enable_llm": true
}
```

**Response:**

```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "kind": "extract",
    "url": "https://www.amazon.com/dp/B0C1234567",
    "contentType": "product",
    "title": "Acme Widget",
    "description": "A widget that does things.",
    "markdown": "# Acme Widget\n...",
    "structured": {
      "price": 19.99,
      "currency": "USD",
      "brand": "Acme",
      "rating": 4.5
    }
  }
}
```

### 2. Render Page HTML

Load a JavaScript-heavy page and return fully-rendered HTML.

```json
POST /webextrator/render
{
  "url": "https://example.com",
  "wait_until": "networkidle"
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
    "status": 200,
    "html": "<!DOCTYPE html><html>...</html>",
    "text": "Example Domain ..."
  }
}
```

## Parameters

### `/webextrator/extract`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `url` | string (required) | URL of the web page to extract content from |
| `expected_type` | `"product"`, `"article"`, `"general"` | Hint to optimize extraction for a known page type |
| `enable_llm` | `true` / `false` | Enable LLM-based semantic normalization (default: false) |
| `wait_until` | `"load"`, `"domcontentloaded"`, `"networkidle"`, `"commit"` | Page load wait condition (default: `networkidle`) |
| `timeout` | number | Total timeout in seconds (default: 30) |
| `delay` | number | Extra delay in seconds after page load, before extraction |
| `wait_for_selector` | string | CSS selector to wait for before extracting |
| `block_resources` | array | Resource types to block: `"image"`, `"font"`, `"media"`, `"stylesheet"`, `"xhr"`, `"fetch"` |
| `headers` | object | Extra HTTP headers to send with the page request |
| `user_agent` | string | Override the User-Agent header |
| `callback_url` | string | If provided, processes asynchronously and POSTs the result to this URL |

### `/webextrator/render`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `url` | string (required) | URL of the web page to render |
| `wait_until` | `"load"`, `"domcontentloaded"`, `"networkidle"`, `"commit"` | Page load wait condition (default: `networkidle`) |
| `timeout` | number | Total timeout in seconds (default: 30) |
| `delay` | number | Extra delay in seconds after page load, before HTML is captured |
| `wait_for_selector` | string | CSS selector to wait for before capturing HTML |
| `block_resources` | array | Resource types to block: `"image"`, `"font"`, `"media"`, `"stylesheet"`, `"xhr"`, `"fetch"` |
| `headers` | object | Extra HTTP headers to send with the page request |
| `user_agent` | string | Override the User-Agent header |
| `callback_url` | string | If provided, processes asynchronously and POSTs the result to this URL |

### `/webextrator/tasks`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"retrieve"`, `"retrieve_batch"` (required) | Single or batch task lookup |
| `id` | string | Task UUID — used with `retrieve` |
| `trace_id` | string | Trace UUID — alternative lookup for `retrieve` |
| `ids` | array | List of task UUIDs — used with `retrieve_batch` |
| `trace_ids` | array | List of trace UUIDs — used with `retrieve_batch` |
| `offset` | number | Pagination offset for `retrieve_batch` (default: 0) |
| `limit` | number | Pagination limit for `retrieve_batch` (default: 12) |

## Gotchas

- Use `block_resources` to speed up extraction by preventing images, fonts, or stylesheets from loading
- Set `wait_until: "networkidle"` for SPAs and JavaScript-rendered pages; use `"domcontentloaded"` for simpler pages
- If the queue is busy, the API returns `429` — retry later or use `callback_url` for async processing
- A `504` response means the operation exceeded its timeout; increase `timeout` or simplify `wait_until`
- `enable_llm: true` adds a final LLM pass for semantic normalization — useful for product/article pages

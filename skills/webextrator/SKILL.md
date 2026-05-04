---
name: webextrator
description: Extract structured content or render web pages via AceDataCloud WebExtrator API. Use when scraping product details, articles, or any web content, or when you need the fully rendered HTML of a JavaScript-heavy page.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# WebExtrator Web Render & Extract

Render JavaScript-heavy web pages and extract structured content through AceDataCloud's WebExtrator API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/webextrator/extract \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amazon.com/dp/B0C1234567", "expected_type": "product"}'
```

> **Async:** Pass `callback_url` to receive the result via webhook instead of waiting. Poll past tasks via `POST /webextrator/tasks`.

## Workflows

### 1. Extract Structured Content

Parse a page and return clean, structured data (title, markdown, images, links, etc.).

```json
POST /webextrator/extract
{
  "url": "https://example.com/product/123",
  "expected_type": "product"
}
```

Response includes:
- `data.title`, `data.description`, `data.byline`, `data.siteName`
- `data.markdown` — full page content as Markdown
- `data.images` — image URLs found on the page
- `data.links` — links found on the page
- `data.structured` — domain-specific fields (e.g. `price`, `brand`, `rating` for products)

### 2. Render a Web Page

Fetch the fully rendered HTML of a page (after JavaScript execution).

```json
POST /webextrator/render
{
  "url": "https://example.com",
  "wait_until": "networkidle"
}
```

Response includes:
- `data.html` — full rendered HTML
- `data.text` — plain text version
- `data.title`, `data.status`, `data.finalUrl`

### 3. LLM-Enhanced Extraction

Use an LLM post-processing step for semantic normalization.

```json
POST /webextrator/extract
{
  "url": "https://shop.example.com/item/123",
  "expected_type": "product",
  "enable_llm": true
}
```

### 4. Async Extraction with Callback

For slow pages, provide a `callback_url` — the result is POSTed when ready.

```json
POST /webextrator/extract
{
  "url": "https://slow-page.example.com",
  "callback_url": "https://your.server.com/callback"
}
```

## Parameters

### `/webextrator/extract`

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string **(required)** | The URL of the web page to extract content from |
| `expected_type` | string | Page type hint: `"product"`, `"article"`, `"general"` |
| `enable_llm` | boolean | Enable LLM-based semantic normalization (default: false) |
| `wait_until` | string | Page load wait condition: `"load"`, `"domcontentloaded"`, `"networkidle"` (default), `"commit"` |
| `timeout` | number | Total timeout in seconds (default: 30) |
| `delay` | number | Extra delay in seconds after page loads, before extraction |
| `wait_for_selector` | string | CSS selector to wait for before extracting |
| `block_resources` | array | Resource types to block: `"image"`, `"font"`, `"media"`, `"stylesheet"`, `"xhr"`, `"fetch"` |
| `headers` | object | Extra HTTP headers to send with the page request |
| `user_agent` | string | Override the User-Agent header |
| `callback_url` | string | Webhook URL — triggers async mode; result POSTed here when complete |

### `/webextrator/render`

Same parameters as `/webextrator/extract` except `expected_type` and `enable_llm` are not applicable.

### `/webextrator/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string **(required)** | `"retrieve"` (single) or `"retrieve_batch"` (multiple) |
| `id` | string | Task UUID — used by `retrieve` |
| `trace_id` | string | Trace UUID — alternative lookup for `retrieve` |
| `ids` | array | List of task UUIDs — used by `retrieve_batch` |
| `trace_ids` | array | List of trace UUIDs — used by `retrieve_batch` |
| `offset` | number | Pagination offset for `retrieve_batch` (default: 0) |
| `limit` | number | Pagination limit for `retrieve_batch` (default: 12) |

## Response Structure

```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440001",
  "started_at": "2025-05-02T10:30:00.123Z",
  "finished_at": "2025-05-02T10:30:08.789Z",
  "elapsed": 8.666,
  "data": {
    "kind": "extract",
    "url": "https://www.amazon.com/dp/B0C1234567",
    "contentType": "product",
    "title": "Acme Widget",
    "description": "A widget that does things.",
    "markdown": "# Acme Widget\n...",
    "images": ["https://example.com/widget.jpg"],
    "links": ["https://example.com/related"],
    "structured": {
      "price": 19.99,
      "currency": "USD",
      "brand": "Acme",
      "rating": 4.5
    }
  }
}
```

## Gotchas

- `429` responses mean the backend queue is busy — retry later or switch to `callback_url` async mode
- `504` responses mean the page exceeded the configured `timeout`
- `block_resources` can significantly speed up extraction on media-heavy pages
- `enable_llm` adds latency but improves accuracy for `"product"` and `"article"` types
- `wait_for_selector` is useful for pages with lazy-loading or skeleton screens

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

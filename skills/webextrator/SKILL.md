---
name: webextrator
description: Extract structured content or render web pages via AceDataCloud's WebExtrator API. Use when scraping product data, articles, or general web content, or when rendering JavaScript-heavy pages to get the final HTML. Supports async callback for long-running jobs.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-webextrator for tool-use.
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

Parse a web page into structured data (title, description, markdown, links, images, and type-specific fields like price or article body).

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
  "elapsed": 8.666,
  "data": {
    "kind": "extract",
    "url": "https://www.amazon.com/dp/B0C1234567",
    "contentType": "product",
    "title": "Acme Widget",
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

### 2. Render a Web Page

Load a URL in a headless browser and return the fully rendered HTML and page text.

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
  "elapsed": 5.333,
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

### 3. Async Mode (Callback URL)

For long-running jobs, pass a `callback_url`. The API returns a `task_id` immediately and POSTs the result to your URL when done.

```json
POST /webextrator/extract
{
  "url": "https://example.com/article",
  "callback_url": "https://your.server.com/callback"
}
```

### 4. Query Task Results

Retrieve previously created render or extract tasks.

```json
POST /webextrator/tasks
{
  "action": "retrieve",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Batch retrieval:

```json
POST /webextrator/tasks
{
  "action": "retrieve_batch",
  "ids": ["task-id-1", "task-id-2"]
}
```

## Parameters

### `/webextrator/extract`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | **required** | URL of the web page to extract |
| `expected_type` | `"product"`, `"article"`, `"general"` | — | Page type hint to optimize extraction |
| `enable_llm` | boolean | `false` | Enable LLM-based semantic normalization as a final step |
| `wait_until` | `"load"`, `"domcontentloaded"`, `"networkidle"`, `"commit"` | `"networkidle"` | Page load wait condition |
| `timeout` | number | `30` | Total timeout in seconds |
| `delay` | number | — | Extra delay in seconds after page load, before extraction |
| `wait_for_selector` | string | — | CSS selector to wait for before extracting |
| `block_resources` | array | — | Resource types to block: `image`, `font`, `media`, `stylesheet`, `xhr`, `fetch` |
| `headers` | object | — | Extra HTTP headers to send with the page request |
| `user_agent` | string | — | Override the User-Agent header |
| `callback_url` | string (URL) | — | Async callback URL — enables non-blocking mode |

### `/webextrator/render`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | **required** | URL of the web page to render |
| `wait_until` | `"load"`, `"domcontentloaded"`, `"networkidle"`, `"commit"` | `"networkidle"` | Page load wait condition |
| `timeout` | number | `30` | Total timeout in seconds |
| `delay` | number | — | Extra delay in seconds after page load, before capturing HTML |
| `wait_for_selector` | string | — | CSS selector to wait for before capturing |
| `block_resources` | array | — | Resource types to block |
| `headers` | object | — | Extra HTTP headers |
| `user_agent` | string | — | Override the User-Agent header |
| `callback_url` | string (URL) | — | Async callback URL |

### `/webextrator/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | `"retrieve"`, `"retrieve_batch"` | Operation type |
| `id` | string | Task UUID — used with `retrieve` |
| `trace_id` | string | Trace UUID — alternative lookup for `retrieve` |
| `ids` | array | Task UUIDs — used with `retrieve_batch` |
| `trace_ids` | array | Trace UUIDs — used with `retrieve_batch` |
| `offset` | number | Pagination offset for `retrieve_batch` (default: 0) |
| `limit` | number | Pagination limit for `retrieve_batch` (default: 12) |

## Gotchas

- Use `expected_type: "product"` for e-commerce pages and `"article"` for blog/news content to improve extraction accuracy
- `enable_llm: true` adds an LLM normalization step — more accurate but slower and more expensive
- Use `callback_url` for pages that take more than a few seconds to load (avoids 429 queue-busy errors)
- `block_resources` (e.g., `["image", "font"]`) speeds up page load significantly for text-only extractions
- The 504 timeout error means the page exceeded the configured `timeout`; increase it or switch to async mode
- Rendered HTML is the post-JavaScript DOM — use `/render` when the content you need is built by client-side JS

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

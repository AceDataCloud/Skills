---
name: short-url
description: Create short URLs via AceDataCloud API. Use when generating shortened links for sharing, or batch-creating multiple short URLs at once. Supports custom slugs and expiration.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable. Optionally pair with mcp-short-url for tool-use.
---

# Short URL Service

Create short URLs through AceDataCloud's URL shortening API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/shorturl \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "https://example.com/very-long-url-path?with=params"}'
```

## Workflows

### 1. Create a Short URL

```json
POST /shorturl
{
  "content": "https://example.com/article/2024/awesome-content"
}
```

Response:

```json
{
  "data": {
    "url": "https://suro.id/abc123"
  },
  "success": true
}
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `content` | Yes | The original long URL to shorten |

## Gotchas

- Short URLs use the `suro.id` domain
- Results are returned synchronously — no task polling needed
- The `content` field must be a valid URL to shorten

> **MCP:** `pip install mcp-shorturl` | Hosted: `https://short-url.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

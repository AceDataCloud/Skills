---
name: short-url
description: Create short URLs via AceDataCloud API. Use when generating shortened links for sharing. Returns a shortened URL synchronously.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable. Optionally pair with mcp-short-url for tool-use.
---

# Short URL Service

Create short URLs through AceDataCloud's URL shortening API.

## Authentication

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/shorturl \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "https://example.com/very-long-url-path?with=params"}'
```

## Workflows

### Create a Short URL

```json
POST /shorturl
{
  "content": "https://example.com/article/2024/awesome-content"
}
```

Response:

```json
{
  "short_url": "https://acda.cc/abc123",
  "url": "https://example.com/article/2024/awesome-content"
}
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `content` | Yes | The original long URL to shorten |

## MCP Server

```bash
pip install mcp-short-url
```

Or hosted: `https://short-url.mcp.acedata.cloud/mcp`

Key tool: `create_short_url`

## Gotchas

- Short URLs use the `acda.cc` domain
- Results are returned synchronously — no task polling needed

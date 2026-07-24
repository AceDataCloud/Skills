---
name: turnstile
description: Solve Cloudflare Turnstile captcha challenges and retrieve tokens via AceDataCloud API. Use when automating Cloudflare Turnstile verification — provide the site key and page URL to receive a solved token ready for form submission.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Cloudflare Turnstile Captcha Solver

Solve Cloudflare Turnstile captcha challenges through AceDataCloud's API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/captcha/token/turnstile \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"website_key": "0x4AAAAAAADnPIDROrmt1Wwj", "website_url": "https://example.com"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /captcha/tasks` with `{"id": "..."}`.

## Workflow

1. Identify the `website_key` (also called `sitekey`) from the target page's HTML or JavaScript
2. Submit the key and page URL to `/captcha/token/turnstile`
3. Receive the solved `token` in the response
4. Submit the token in the form or API request as the Turnstile response field

## Endpoint

### Solve Token (`POST /captcha/token/turnstile`)

```json
POST /captcha/token/turnstile
{
  "website_key": "0x4AAAAAAADnPIDROrmt1Wwj",
  "website_url": "https://react-turnstile.vercel.app"
}
```

**Response:**

```json
{
  "token": "0.zScW-EiocHwwpwqtk1QXlJnGnU......",
  "started_at": "2026-07-24T09:34:13+00:00",
  "finished_at": "2026-07-24T09:34:50+00:00",
  "elapsed": 12.4
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `website_key` | Yes | string | The Turnstile site key from the target page |
| `website_url` | Yes | string | Full URL of the page presenting the captcha |
| `action` | No | string | Optional `action` parameter passed to the Turnstile widget |
| `cdata` | No | string | Optional `cdata` parameter passed to the Turnstile widget |
| `async` | No | boolean | Return immediately with a `task_id`; poll `/captcha/tasks` for the solved token |

## Response Fields

| Field | Description |
|-------|-------------|
| `token` | Solved Turnstile token — submit this as the captcha response |
| `started_at` | Timestamp when solving began |
| `finished_at` | Timestamp when solving completed |
| `elapsed` | Time taken in seconds |

## Gotchas

- `website_key` is the public site key embedded in the page — find it in the `data-sitekey` attribute or JavaScript config
- The returned `token` is single-use and expires quickly — submit it immediately after receiving it
- Use `async: true` for non-blocking operation; then poll `POST /captcha/tasks` with the returned `task_id`
- Billing only occurs when a token is successfully solved

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

---
name: turnstile
description: Solve Cloudflare Turnstile CAPTCHAs via AceDataCloud API. Use when you need to bypass or solve a Cloudflare Turnstile challenge by providing the site key and page URL to get back a valid token. Supports synchronous and asynchronous modes.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Cloudflare Turnstile CAPTCHA Solver

Solve Cloudflare Turnstile CAPTCHA challenges through AceDataCloud's captcha API. Submit the site key and target URL to receive a valid `cf-turnstile-response` token.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/captcha/token/turnstile \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "website_key": "0x4AAAAAAADnPIDROrmt1Wwj",
    "website_url": "https://react-turnstile.vercel.app"
  }'
```

A successful synchronous response:

```json
{
  "token": "0.mNQ2f9uP6mQ0y3H5Q8bqO7iM...",
  "started_at": 1753350853.0,
  "finished_at": 1753350865.4,
  "elapsed": 12.4
}
```

Use the returned `token` as the `cf-turnstile-response` value when submitting forms to the target site. The token is single-use with a ~120s validity — use it within 60s.

## How to Find `website_key`

1. Open the target page in a browser and press F12 to open DevTools
2. In the Elements panel, search for `cf-turnstile`
3. Find the container element — the `data-sitekey` attribute value is the `website_key`

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `website_key` | ✓ | The Turnstile site key (`data-sitekey`) from the target page |
| `website_url` | ✓ | The full URL of the page containing the Turnstile widget |
| `action` | | Custom `action` value — only needed when the target page sets a custom action |
| `cdata` | | Custom `cData` value — only needed when the target page sets a custom cData |
| `async` | | When `true`, return immediately with a `task_id`; poll `POST /captcha/tasks` to retrieve the token |

## Response Fields

| Field | Description |
|-------|-------------|
| `token` | The solved Turnstile token to submit as `cf-turnstile-response` |
| `started_at` | Unix timestamp (seconds, float) when solving began |
| `finished_at` | Unix timestamp (seconds, float) when solving completed |
| `elapsed` | Total solving time in seconds |

## Async Mode

Pass `async: true` to return a `task_id` immediately instead of blocking:

```json
POST /captcha/token/turnstile
{
  "website_key": "0x4AAAAAAADnPIDROrmt1Wwj",
  "website_url": "https://react-turnstile.vercel.app",
  "async": true
}
```

Then poll `POST /captcha/tasks` with the returned `task_id`:

```json
POST /captcha/tasks
{"id": "<task_id>"}
```

> **Async:** See [async task polling](../_shared/async-tasks.md) for the full polling contract.

## Using the Token

Submit the token to the target site as `cf-turnstile-response`:

```python
import requests

token = "0.mNQ2f9uP6mQ0y3H5Q8bqO7iM..."
response = requests.post(
    "https://react-turnstile.vercel.app",
    data={"cf-turnstile-response": token}
)
```

## Gotchas

- Both `website_key` and `website_url` are **required**
- The token is single-use and valid for ~120s — use within 60s for best results
- `action` and `cdata` are optional and only required when the target site explicitly uses them
- You are billed only when a token is successfully solved
- Synchronous mode blocks until the token is ready (typically 10–30s); use `async: true` for non-blocking operation

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

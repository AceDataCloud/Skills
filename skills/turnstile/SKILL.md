---
name: turnstile
description: Solve Cloudflare Turnstile challenges via AceDataCloud API. Use when obtaining a Cloudflare Turnstile bypass token for automated form submission on sites protected by Cloudflare Turnstile (the successor to CAPTCHA).
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Cloudflare Turnstile Solving

Obtain Cloudflare Turnstile tokens through AceDataCloud's Turnstile API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/captcha/token/turnstile \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://example.com/login", "website_key": "0x4AAAAAAABB..."}'
```

## Workflow

Submit the target page's `website_url` and `website_key` to receive a Turnstile token. Submit the token to the target site as `cf-turnstile-response`.

```json
POST /captcha/token/turnstile
{
  "website_url": "https://example.com/page-with-turnstile",
  "website_key": "0x4AAAAAAABB..."
}
```

**Response:**

```json
{
  "token": "0.Q1...",
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:05Z",
  "elapsed": 4.7
}
```

Submit the returned `token` as the `cf-turnstile-response` field in the target form or API request.

## Parameters

### POST /captcha/token/turnstile

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `website_key` | Yes | string | Cloudflare Turnstile site key from the target page |
| `website_url` | Yes | string | URL of the page containing the Turnstile widget |
| `action` | No | string | Optional `action` parameter configured on the Turnstile widget |
| `cdata` | No | string | Optional `cData` (custom data) parameter configured on the Turnstile widget |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

## Gotchas

- Tokens are **single-use** — submit promptly after receiving
- Find `website_key` in the page source (look for `data-sitekey` attribute on the Turnstile widget `<div>`)
- The `action` and `cdata` parameters are optional and must match the widget configuration if the site validates them
- Use `async: true` for non-blocking calls; billing occurs only on a successful token

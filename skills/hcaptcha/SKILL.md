---
name: hcaptcha
description: Solve hCaptcha challenges via AceDataCloud API. Use when bypassing hCaptcha verification for image recognition (click-based challenges) or obtaining bypass tokens (protocol-based, for automated form submission). Provides both image recognition and protocol token endpoints.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# hCaptcha Solving

Solve hCaptcha challenges through AceDataCloud's hCaptcha API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/captcha/token/hcaptcha \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://accounts.hcaptcha.com/demo", "website_key": "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2"}'
```

## Workflows

### 1. Token (Protocol-Based Bypass)

Obtain a bypass token by submitting the target website's `website_key`. No image processing required. The returned `token` can be submitted to the target site as `h-captcha-response`.

```json
POST /captcha/token/hcaptcha
{
  "website_url": "https://example.com/page-with-hcaptcha",
  "website_key": "your-site-key-here"
}
```

**Response:**

```json
{
  "token": "P1_eyJ...",
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:31Z",
  "elapsed": 31.6
}
```

Use the token within **60 seconds** (valid for up to 120 s).

### 2. Image Recognition

Identify which small images to click in an hCaptcha grid challenge. Provide a Base64-encoded screenshot of the challenge and the question text.

```json
POST /captcha/recognition/hcaptcha
{
  "queries": ["<base64-encoded-captcha-image>"],
  "question": "Please click on the UNIQUE object among the others."
}
```

**Response:**

```json
{
  "solution": {
    "label": "Please click on the UNIQUE object among the others",
    "box": ["360", "276"],
    "confidences": 0.635
  },
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:02Z",
  "elapsed": 1.8
}
```

## Parameters

### POST /captcha/token/hcaptcha

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `website_key` | Yes | string | hCaptcha site key from the target page |
| `website_url` | Yes | string | URL of the page containing the hCaptcha |
| `proxy` | No | string | Custom proxy (`scheme://[user:pass@]host:port`). Supports `http`, `https`, `socks4`, `socks5`. Omit to use platform default. |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

### POST /captcha/recognition/hcaptcha

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `queries` | No | array of strings | Base64-encoded captcha image(s). Keep image size under 100 KB. |
| `question` | No | string | Challenge question text (English or Chinese). |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

## Gotchas

- Tokens are **single-use** and valid for up to 120 s — use within 60 s for best results
- For image recognition, compress the screenshot to under 100 KB before Base64-encoding
- The `proxy` field in token mode lets you control the exit IP — useful if the target site blocks public proxy IPs
- Find `website_key` by inspecting the page source (look for `data-sitekey` in an hCaptcha widget element)
- Use `async: true` for long-running solves to avoid HTTP timeouts; billing occurs only on a successful solve

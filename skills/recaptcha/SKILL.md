---
name: recaptcha
description: Solve Google reCAPTCHA v2 and v3 challenges via AceDataCloud API. Use when bypassing reCAPTCHA v2 image challenges (click-based), obtaining reCAPTCHA v2 bypass tokens, or generating reCAPTCHA v3 score-based tokens for automated form submission.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# reCAPTCHA Solving

Solve Google reCAPTCHA v2 and v3 challenges through AceDataCloud's reCAPTCHA API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/captcha/token/recaptcha2 \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://www.google.com/recaptcha/api2/demo", "website_key": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"}'
```

## Workflows

### 1. reCAPTCHA v2 Token (Protocol-Based Bypass)

Obtain a `g-recaptcha-response` token by submitting the target website's `website_key`. Submit the token to the target site as `g-recaptcha-response`.

```json
POST /captcha/token/recaptcha2
{
  "website_url": "https://example.com/page-with-recaptcha",
  "website_key": "your-site-key-here"
}
```

**Response:**

```json
{
  "token": "03AGdBq...",
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:25Z",
  "elapsed": 25.0
}
```

### 2. reCAPTCHA v3 Token

Generate a reCAPTCHA v3 score-based token. Requires `page_action` (the action name used on the target page).

```json
POST /captcha/token/recaptcha3
{
  "website_url": "https://example.com/login",
  "website_key": "your-v3-site-key",
  "page_action": "login"
}
```

### 3. reCAPTCHA v2 Image Recognition

Solve a reCAPTCHA v2 image challenge (e.g., "select all images with traffic lights"). Provide a Base64-encoded screenshot of the challenge image and the question text.

```json
POST /captcha/recognition/recaptcha2
{
  "image": "<base64-encoded-captcha-image>",
  "question": "Select all images with traffic lights."
}
```

**Response:**

```json
{
  "solution": {
    "label": "traffic light",
    "box": ["120", "240"]
  },
  "elapsed": 2.1
}
```

## Parameters

### POST /captcha/token/recaptcha2

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `website_key` | Yes | string | reCAPTCHA v2 site key from the target page |
| `website_url` | Yes | string | URL of the page containing the reCAPTCHA |
| `proxy` | No | string | Custom proxy (`scheme://[user:pass@]host:port`). Supports `http`, `https`, `socks4`, `socks5`. |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

### POST /captcha/token/recaptcha3

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `page_action` | Yes | string | The `action` parameter used by the target page (e.g., `"login"`, `"submit"`) |
| `website_key` | Yes | string | reCAPTCHA v3 site key from the target page |
| `website_url` | Yes | string | URL of the page containing the reCAPTCHA v3 |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

### POST /captcha/recognition/recaptcha2

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image` | Yes | string | Base64-encoded screenshot of the reCAPTCHA image challenge |
| `question` | Yes | string | Challenge question text describing what to select |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

## Gotchas

- Tokens from `/captcha/token/recaptcha2` are single-use and time-limited — submit them promptly
- reCAPTCHA v3 returns a score (0.0–1.0); the platform generates a realistic high-score token
- Find `website_key` in the page source (look for `data-sitekey` attribute or `grecaptcha.execute('KEY', ...)`)
- The `page_action` for v3 must match exactly what the target page uses — mismatch can cause verification failure
- Use `async: true` for long-running solves to avoid HTTP timeouts; billing occurs only on a successful solve

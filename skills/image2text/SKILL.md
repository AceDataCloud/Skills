---
name: image2text
description: Recognize English alphanumeric text from CAPTCHA images via AceDataCloud API. Use when solving simple text-based CAPTCHAs (image-to-text) that contain numbers and/or letters, returning the recognized string.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Image-to-Text CAPTCHA Recognition

Recognize alphanumeric text from CAPTCHA images through AceDataCloud's Image2Text API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/captcha/recognition/image2text \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64-encoded-captcha-image>"}'
```

## Workflow

Submit a Base64-encoded CAPTCHA image. The API recognizes and returns the text string.

```json
POST /captcha/recognition/image2text
{
  "image": "<base64-encoded-captcha-image>"
}
```

**Response:**

```json
{
  "solution": {
    "text": "X4B7K"
  },
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:01Z",
  "elapsed": 0.8
}
```

Use the returned `solution.text` to fill in the CAPTCHA field on the target form.

## Parameters

### POST /captcha/recognition/image2text

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image` | Yes | string | Base64-encoded CAPTCHA image |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

## Gotchas

- Designed for simple English alphanumeric (text) CAPTCHAs — not for click-based or puzzle CAPTCHAs
- Keep the image size small (compress before Base64-encoding) for faster recognition
- Use `async: true` for non-blocking calls; billing occurs only on a successful recognition

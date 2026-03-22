---
name: qr-art
description: Generate artistic AI-powered QR codes via AceDataCloud API. Use when creating stylized QR codes that embed links, text, emails, phone numbers, or SMS into beautiful AI-generated artwork. Supports multiple artistic presets and fine-tuned control over QR readability.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable.
---

# QR Art — Artistic QR Code Generation

Generate beautiful AI-powered QR codes through AceDataCloud's QR Art API.

## Authentication

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/qrart/generate \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "link", "content": "https://example.com", "prompt": "a magical forest with glowing mushrooms"}'
```

## Supported Content Types

| Type | Content Format | Example |
|------|---------------|---------|
| `link` | URL | `https://example.com` |
| `text` | Plain text | `Hello World` |
| `email` | Email address | `user@example.com` |
| `phone` | Phone number | `+1234567890` |
| `sms` | Phone number | `+1234567890` |

## Artistic Presets

| Preset | Style |
|--------|-------|
| `sunset` | Warm sunset tones |
| `floral` | Flower and botanical motifs |
| `snowflakes` | Winter/snow aesthetics |
| `feathers` | Feather textures |
| `raindrops` | Water/rain effects |
| `ultra-realism` | Photorealistic style |
| `epic-realms` | Fantasy landscapes |

## Workflows

### 1. Basic QR Code with Preset

```json
POST /qrart/generate
{
  "type": "link",
  "content": "https://example.com",
  "prompt": "beautiful ocean waves",
  "preset": "ultra-realism"
}
```

### 2. Custom Artistic QR

Fine-tune the generation with detailed prompts and parameters.

```json
POST /qrart/generate
{
  "type": "link",
  "content": "https://example.com",
  "prompt": "a Japanese zen garden with cherry blossoms, watercolor style",
  "ecl": "H",
  "qrw": 2.0,
  "steps": 18,
  "seed": 42
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `type` | Yes | `"link"`, `"text"`, `"email"`, `"phone"`, `"sms"` | Content type |
| `content` | Yes | string | The content to encode |
| `prompt` | Yes | string | Artistic style description |
| `preset` | No | See presets table | Predefined artistic style |
| `ecl` | No | `"L"`, `"M"`, `"Q"`, `"H"` (default: `"H"`) | Error correction level |
| `qrw` | No | 1.5–3.0 (default: 1.5) | QR code weight (higher = more scannable) |
| `steps` | No | 10–20 (default: 16) | Generation iterations (more = better quality) |
| `seed` | No | integer | Seed for reproducible results |

## Task Polling

```json
POST /qrart/tasks
{"task_id": "your-task-id"}
```

## Response

```json
{
  "task_id": "abc123",
  "image_url": "https://cdn.example.com/qr.png",
  "image_width": 768,
  "image_height": 768,
  "seed": 42
}
```

## Gotchas

- **Error correction level (ecl)**: Use `"H"` (highest) for QR codes that must be reliably scannable. Lower levels (`L`, `M`) allow more artistic freedom but may reduce scan reliability.
- **QR weight (qrw)**: Balance between art and functionality — `1.5` is more artistic, `3.0` prioritizes scannability
- Higher `steps` values produce better quality but take longer
- Always **test scan** the generated QR code before using in production
- The `seed` value in the response lets you reproduce the exact same result

---
name: grok-video
description: Generate AI videos with Grok Imagine via AceDataCloud API. Use when creating text-to-video or image-to-video clips, guiding output with reference images, or needing Grok's longer 30-second video mode. Supports grok-imagine-video and grok-imagine-video-1.5-preview.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok Imagine (xAI) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a cinematic shot of a kitten chasing a butterfly in a sunlit garden","model":"grok-imagine-video","resolution":"480p","duration":8}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Type | Best For |
|-------|------|----------|
| `grok-imagine-video` | Text+Image-to-Video | Default model; supports text-only or image-guided video, up to 30 seconds |
| `grok-imagine-video-1.5-preview` | Image-to-Video | Higher-end preview model; requires `image_url`, up to 15 seconds |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "grok-imagine-video",
  "resolution": "480p",
  "duration": 8
}
```

### 2. Image-to-Video

```json
POST /grok/videos
{
  "prompt": "the character slowly turns around and smiles at the camera",
  "model": "grok-imagine-video-1.5-preview",
  "image_url": "https://cdn.acedata.cloud/5hmkdg.jpg",
  "resolution": "720p",
  "duration": 8
}
```

### 3. Reference-Image Guidance

```json
POST /grok/videos
{
  "prompt": "a character dancing in the same art style",
  "model": "grok-imagine-video",
  "reference_image_urls": [
    "https://cdn.acedata.cloud/vunnjf.png"
  ]
}
```

### 4. Async Callback

```json
POST /grok/videos
{
  "prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "grok-imagine-video",
  "duration": 8,
  "callback_url": "https://your-domain.com/callback/grok"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | For text-to-video | string | Video description; required when generating from text only |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model (default: `grok-imagine-video`) |
| `image_url` | For `grok-imagine-video-1.5-preview` | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Reference images to guide style or content |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `480p`) |
| `duration` | No | `1`–`30` for `grok-imagine-video`; `1`–`15` for `grok-imagine-video-1.5-preview` | Output duration in seconds (default: `8`) |
| `callback_url` | No | string | Async webhook URL |
| `async` | No | boolean | Return a task ID immediately and retrieve later via `/grok/tasks` |

## Billing Notes

- `grok-imagine-video` uses tiered duration pricing by range: `1–10`, `11–20`, and `21–30` seconds.
- `grok-imagine-video-1.5-preview` is billed per output second, and `1080p` costs more than `480p` / `720p`.

## Gotchas

- `grok-imagine-video` supports both text-to-video and image-to-video; `grok-imagine-video-1.5-preview` **requires** `image_url`
- `duration` is model-specific: `grok-imagine-video` allows `1–30` seconds, while `grok-imagine-video-1.5-preview` allows `1–15`
- `callback_url` is optional; `async: true` also works if you prefer polling instead of webhooks
- Poll async jobs via `POST /grok/tasks` with `{"id": "<task_id>"}`

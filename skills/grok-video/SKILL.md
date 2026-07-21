---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images. Supports text-to-video and image-to-video with aspect ratio and resolution control.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok (xAI) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a futuristic city skyline at dusk with flying vehicles", "model": "grok-imagine-video", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | General text-to-video and image-to-video (default) |
| `grok-imagine-video-1.5-preview` | Preview of next-generation Grok video model |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "time-lapse of northern lights dancing over a snowy forest",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image.

```json
POST /grok/videos
{
  "prompt": "gentle waves lapping at the shore",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/beach.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Image-to-Video with References

Use multiple reference images alongside the main image.

```json
POST /grok/videos
{
  "prompt": "character walks through a sunlit forest",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/character.jpg",
  "reference_image_urls": ["https://example.com/forest.jpg"]
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Video description |
| `model` | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model to use (default: `grok-imagine-video`) |
| `image_url` | string | Source image URL for image-to-video generation |
| `reference_image_urls` | array of strings | Additional reference image URLs |
| `aspect_ratio` | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Video aspect ratio |
| `resolution` | `"480p"`, `"720p"` | Output resolution (default: `480p`) |
| `duration` | integer (1–15) | Video duration in seconds (default: 8) |
| `callback_url` | string | Webhook URL for async result delivery |
| `async` | boolean | Force async mode |

## Task Polling

```json
POST /grok/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
}
```

For batch polling:

```json
POST /grok/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

## Gotchas

- Use `callback_url` to avoid HTTP timeout on long-running generations
- `image_url` is required for image-to-video; `prompt` alone is sufficient for text-to-video
- Default resolution is `480p`; use `720p` for higher quality output
- Default `duration` is 8 seconds; valid range is 1–15 seconds

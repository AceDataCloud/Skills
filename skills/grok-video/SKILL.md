---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts, animating images with a reference image, or using reference images for style/character consistency. Supports reverse-engineered and official Grok video models with resolution control.
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
  -d '{"prompt": "a futuristic city at night with neon lights reflecting in rain puddles"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Type | Notes |
|-------|------|-------|
| `grok-imagine-video-1.5-fast:reverse` | Text/Image-to-Video | Default — fastest generation |
| `grok-imagine-video:reverse` | Text/Image-to-Video | Reverse-engineered standard model |
| `grok-imagine-video:official` | Text/Image-to-Video | Official Grok API |
| `grok-imagine-video-1.5:official` | Text/Image-to-Video | Official Grok 1.5 API |
| `grok-imagine-video` | Text/Image-to-Video | Base model |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a golden retriever running on a beach at sunset",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "resolution": "720p",
  "duration": 6
}
```

### 2. Image-to-Video

Animate a still image using a prompt.

```json
POST /grok/videos
{
  "prompt": "the scene slowly comes to life with gentle motion",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "image_url": "https://example.com/photo.jpg",
  "resolution": "720p"
}
```

### 3. Reference Image Generation

Use one or more reference images to guide style or character consistency.

```json
POST /grok/videos
{
  "prompt": "the character walks through a futuristic city",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "reference_image_urls": [
    "https://example.com/character.jpg"
  ]
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | No | string | Text description of the video |
| `model` | No | see Models table | Model to use (default: `grok-imagine-video-1.5-fast:reverse`) |
| `image_url` | No | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Reference images for style/character consistency |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Video aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `480p`) |
| `duration` | No | integer | Video duration in seconds (default: `6`) |
| `callback_url` | No | string | Async webhook notification URL |
| `async` | No | boolean | Return immediately with a task ID instead of blocking |

## Task Polling

When `async` is `true` or the request times out, poll for results:

```json
POST /grok/tasks
{
  "id": "<task_id from response>"
}
```

## Gotchas

- Default resolution is `480p`; use `720p` or `1080p` for higher quality at increased cost
- `reference_image_urls` accepts an array of image URLs to guide consistency across the generation
- `:reverse` models use reverse-engineered access; `:official` models use the official xAI API
- Task polling uses `id` in the `/grok/tasks` request body

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

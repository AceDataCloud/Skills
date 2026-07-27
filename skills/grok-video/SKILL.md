---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or animating images using Grok's video generation models. Supports text-to-video and image-to-video with multiple models, aspect ratios, and resolutions.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Grok Video Generation

Generate AI videos through AceDataCloud's xAI Grok API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a futuristic city at night with neon lights reflecting on wet streets", "model": "grok-imagine-video", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | Standard video generation |
| `grok-imagine-video-1.5-preview` | Enhanced quality, v1.5 preview |
| `grok-imagine-video-1.5-fast:reverse` | Fast v1.5 generation (default, reverse-proxy route) |
| `grok-imagine-video:reverse` | Standard v1 via reverse-proxy route |
| `grok-imagine-video:official` | Standard v1 via official API |
| `grok-imagine-video-1.5:official` | V1.5 via official API |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a golden retriever playing fetch on a sunny beach",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 2. Image-to-Video

Animate a still image with a prompt.

```json
POST /grok/videos
{
  "prompt": "the scene slowly comes alive",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/scene.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Reference Image Video

Use multiple reference images to guide generation.

```json
POST /grok/videos
{
  "prompt": "a character walking through a park",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": [
    "https://example.com/character.jpg",
    "https://example.com/park.jpg"
  ]
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | No | string | Video description |
| `model` | No | see models above | Model to use (default: `grok-imagine-video-1.5-fast:reverse`) |
| `image_url` | No | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Reference images to guide generation |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | Output resolution |
| `duration` | No | integer | Duration in seconds |
| `callback_url` | No | string | Async callback URL |
| `async` | No | boolean | Return task ID immediately |

## Task Polling

```json
POST /grok/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
}
```

Batch polling:

```json
POST /grok/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

## Gotchas

- All generation is **async** — use `callback_url` or `async: true` and poll `/grok/tasks`
- `image_url` enables image-to-video; omit it for text-to-video
- `:reverse` model variants route through a reverse proxy; `:official` variants use the official xAI API directly
- `resolution: "1080p"` is only available for models via the grok.json endpoint (`grok-imagine-video:official`, `grok-imagine-video-1.5:official`, and `grok-imagine-video`)

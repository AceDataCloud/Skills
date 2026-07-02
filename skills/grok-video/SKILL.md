---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or reference images. Supports text-to-video and image-to-video with multiple aspect ratios and resolutions.
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
  -d '{
    "prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden",
    "model": "grok-imagine-video",
    "aspect_ratio": "16:9",
    "resolution": "720p"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Description |
|-------|-------------|
| `grok-imagine-video` | Default — standard quality video generation |
| `grok-imagine-video-1.5-preview` | Improved quality, preview version |

## Workflows

### 1. Text-to-Video

Generate a video from a text prompt.

```json
POST /grok/videos
{
  "prompt": "a futuristic city with neon lights reflecting on rain-slicked streets",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image using `image_url`.

```json
POST /grok/videos
{
  "prompt": "the scene slowly comes to life with gentle movement",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/landscape.jpg",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 3. Image-to-Video with Reference Images

Guide generation with additional reference images.

```json
POST /grok/videos
{
  "prompt": "dynamic motion with consistent style",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": [
    "https://example.com/style-ref1.jpg",
    "https://example.com/style-ref2.jpg"
  ],
  "aspect_ratio": "9:16",
  "resolution": "720p"
}
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `prompt` | No | string | Text description of the video to generate |
| `model` | No | string | Model to use (default: `grok-imagine-video`) |
| `image_url` | No | string (URL) | Source image for image-to-video |
| `reference_image_urls` | No | array of URLs | Additional reference images to guide style |
| `aspect_ratio` | No | string | Output aspect ratio (default: `16:9`) |
| `resolution` | No | string | Output resolution (default: `480p`) |
| `duration` | No | integer | Duration in seconds, 1–15 (default: 8) |
| `callback_url` | No | string (URL) | Webhook URL called when the task completes |
| `async` | No | boolean | Return a task ID immediately (default: true) |

### Aspect Ratios

`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`

### Resolutions

`480p`, `720p`

## Polling Tasks

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

- `prompt` is optional when `image_url` is provided, but a descriptive prompt generally improves quality
- Default resolution is `480p`; set `resolution: "720p"` for higher quality
- `duration` ranges from 1 to 15 seconds (default 8)
- Generation is async — poll `/grok/tasks` with the returned task ID

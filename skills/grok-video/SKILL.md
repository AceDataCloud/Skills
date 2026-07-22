---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts, animating images into video, or using reference images for style guidance. Supports text-to-video and image-to-video with multiple aspect ratios and resolutions.
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
  -d '{"prompt": "a golden eagle soaring over mountain peaks at sunrise", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | Standard video generation (default) |
| `grok-imagine-video-1.5-preview` | Preview of next-generation quality |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a timelapse of storm clouds rolling over a city skyline",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /grok/videos
{
  "prompt": "gentle waves wash over the rocky shore",
  "image_url": "https://example.com/shoreline.jpg",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9"
}
```

### 3. Image-to-Video with Reference Images

Guide video generation style with additional reference images.

```json
POST /grok/videos
{
  "prompt": "a sleek sports car races along a coastal road",
  "image_url": "https://example.com/car.jpg",
  "reference_image_urls": [
    "https://example.com/coast-style.jpg"
  ],
  "model": "grok-imagine-video-1.5-preview"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | For t2v | string | Text description of the video |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model (default: `grok-imagine-video`) |
| `image_url` | For i2v | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Reference images for style guidance |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"` | Output resolution (default: `"480p"`) |
| `duration` | No | 1–15 (integer) | Duration in seconds (default: 8) |
| `callback_url` | No | string | Webhook URL for async completion |
| `async` | No | boolean | Force async mode |

## Polling

```json
POST /grok/tasks
{
  "id": "<task_id>"
}
```

Response includes a `data` array with `state` field. Terminal states: `"succeeded"`, `"failed"`.

For batch polling:

```json
POST /grok/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

## Gotchas

- `prompt` is **required** for text-to-video; `image_url` is required for image-to-video
- Use `callback_url` to avoid HTTP timeout on long video generations
- Task states use `"succeeded"` — check for this value when polling
- `grok-imagine-video-1.5-preview` is a preview model and may have different availability

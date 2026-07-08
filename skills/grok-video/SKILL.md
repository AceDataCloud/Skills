---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images into video. Supports text-to-video and image-to-video with grok-imagine-video-1.5-fast and grok-imagine-video-1.5 models.
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
  -d '{"prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video-1.5-fast"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Type | Notes |
|-------|------|-------|
| `grok-imagine-video-1.5-fast` | Text-to-Video / Image-to-Video | Default; lower cost |
| `grok-imagine-video-1.5` | Image-to-Video only | Higher quality; `image_url` required |

## Workflows

### 1. Text-to-Video

Generate a video purely from a text description.

```json
POST /grok/videos
{
  "prompt": "a futuristic city at night with flying cars and neon lights",
  "model": "grok-imagine-video-1.5-fast",
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
  "prompt": "gentle waves roll across the beach",
  "model": "grok-imagine-video-1.5",
  "image_url": "https://cdn.acedata.cloud/5hmkdg.jpg",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 3. Image-to-Video with Reference Images

Guide style or content with additional reference images.

```json
POST /grok/videos
{
  "prompt": "bring the scene to life with dramatic motion",
  "model": "grok-imagine-video-1.5-fast",
  "image_url": "https://example.com/scene.jpg",
  "reference_image_urls": [
    "https://example.com/style-ref.jpg"
  ],
  "aspect_ratio": "16:9"
}
```

## Parameters

| Parameter | Required | Values | Default | Description |
|-----------|----------|--------|---------|-------------|
| `prompt` | Yes (text-to-video) | string | — | Text description of the video; optional when `image_url` is provided |
| `model` | No | `"grok-imagine-video-1.5-fast"`, `"grok-imagine-video-1.5"` | `"grok-imagine-video-1.5-fast"` | Model to use |
| `image_url` | Required for `grok-imagine-video-1.5` | string | — | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | — | Additional reference image URLs to guide style or content |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | — | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | `"480p"` | Output resolution |
| `duration` | No | integer 1–30 | `8` | Duration in seconds; billing is based on output seconds |
| `callback_url` | No | string | — | Async callback URL; returns `task_id` immediately |
| `async` | No | boolean | — | Force async mode |

## Task Polling

```json
POST /grok/tasks
{
  "id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "action": "retrieve"
}
```

Use `action: "retrieve_batch"` with `ids` (array) to poll multiple tasks at once.

## Gotchas

- `grok-imagine-video-1.5` is image-guided only — `image_url` is **required**
- `grok-imagine-video-1.5-fast` supports both text-to-video (pass `prompt` only) and image-to-video (pass `image_url`)
- Billing is based on output seconds — longer `duration` costs more
- Higher `resolution` costs more; default is `480p`
- Use `callback_url` to avoid polling for long-running generations

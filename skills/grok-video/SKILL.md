---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images with optional reference images. Supports text-to-video and image-to-video with two models and configurable resolution, aspect ratio, and duration.
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
  -d '{"prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video", "resolution": "480p", "duration": 8}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Type | Best For |
|-------|------|----------|
| `grok-imagine-video` | Text-to-Video / Image-to-Video | Default; supports both text and image input |
| `grok-imagine-video-1.5-preview` | Image-to-Video only | Higher quality; requires `image_url` |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a sweeping aerial view of a mountain range at golden hour",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image. `grok-imagine-video-1.5-preview` requires `image_url`.

```json
POST /grok/videos
{
  "model": "grok-imagine-video-1.5-preview",
  "image_url": "https://example.com/portrait.jpg",
  "prompt": "gentle wind blows hair, soft expression",
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "duration": 8
}
```

### 3. Reference-Guided Generation

Pass optional `reference_image_urls` to guide the style or content of the video.

```json
POST /grok/videos
{
  "prompt": "a character walking through a neon-lit city",
  "model": "grok-imagine-video",
  "reference_image_urls": [
    "https://example.com/style-ref.jpg"
  ],
  "aspect_ratio": "16:9",
  "resolution": "480p"
}
```

### 4. Async Generation

For long-running jobs, use async mode and poll for the result.

```json
POST /grok/videos
{
  "prompt": "time-lapse of a sunflower blooming",
  "model": "grok-imagine-video",
  "async": true
}
```

Then poll:

```json
POST /grok/tasks
{
  "id": "<task_id_from_response>"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | For text-to-video | string | Video description. Required when using `grok-imagine-video` without `image_url` |
| `model` | No | `"grok-imagine-video"` (default), `"grok-imagine-video-1.5-preview"` | Model to use |
| `image_url` | For `1.5-preview` | string | Source image URL. Required for `grok-imagine-video-1.5-preview`; optional for default model |
| `reference_image_urls` | No | string[] | Optional reference images to guide style or content |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"` (default), `"720p"` | Output resolution; higher costs more |
| `duration` | No | integer, 1–15 (default `8`) | Video duration in seconds; billed per second |
| `callback_url` | No | string | Async callback URL; returns `task_id` immediately |
| `async` | No | boolean | When `true`, returns `task_id` immediately without `callback_url` |

## Response

```json
{
  "success": true,
  "task_id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "trace_id": "fb751e1e-4705-49ea-9fd4-5024b7865ea2",
  "data": [
    {
      "id": "grok-imagine-video:41eb9a5f-3b2d-4d1e-9f5a-6c2f1a0b9e77",
      "video_url": "https://cdn.acedata.cloud/example.mp4",
      "state": "succeeded"
    }
  ]
}
```

## Gotchas

- `grok-imagine-video-1.5-preview` **requires** `image_url`; it does not support text-only generation
- For `grok-imagine-video` text-to-video, `prompt` is required
- `duration` range is 1–15 seconds; default is 8
- Resolution options are `480p` (default) and `720p`; `1080p` is not supported
- Billed by generated video duration (per second)

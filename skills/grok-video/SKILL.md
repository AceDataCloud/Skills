---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or animating images into video. Supports text-to-video, image-to-video, and reference-image-guided generation with multiple models and aspect ratios.
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
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a red fox leaping through a snowy forest at dawn", "model": "grok-imagine-video", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

Poll the returned `task_id`:

```bash
curl -X POST https://api.acedata.cloud/grok/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | General-purpose video generation |
| `grok-imagine-video-1.5-preview` | Latest preview, higher quality |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a surfer riding a massive wave at sunset with vibrant colors",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 2. Image-to-Video

Animate a still image into a video by providing `image_url`:

```json
POST /grok/videos
{
  "prompt": "the scene comes to life with gentle movement",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/scene.jpg",
  "aspect_ratio": "16:9",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 3. Reference-Image-Guided Generation

Provide one or more reference images to guide the style or content of the generated video:

```json
POST /grok/videos
{
  "prompt": "a peaceful mountain landscape in the same artistic style",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": ["https://example.com/style-ref.jpg"],
  "aspect_ratio": "16:9",
  "callback_url": "https://api.acedata.cloud/health"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Text description of the video (required for text-to-video) |
| `model` | see Models table | Model to use (default: `grok-imagine-video`) |
| `image_url` | string (URL) | Source image for image-to-video generation |
| `reference_image_urls` | array of strings (URLs) | Reference images for style/content guidance |
| `aspect_ratio` | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | `"480p"`, `"720p"` | Output resolution (default: `720p`) |
| `duration` | integer | Video duration in seconds |
| `callback_url` | string | Webhook URL for async delivery; returns `task_id` immediately |

## Response Structure

```json
{
  "success": true,
  "task_id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea",
  "trace_id": "fb751e1e-4705-49ea-9fd4-5024b7865ea2",
  "data": [
    {
      "id": "grok-imagine-video:41eb9a5f-3b2d-4d1e-9f5a-6c2f1a0b9e77",
      "video_url": "https://cdn.acedata.cloud/grok/example-video.mp4",
      "state": "succeeded"
    }
  ]
}
```

Task states: `pending`, `succeeded`, `failed`.

## Gotchas

- `prompt` is required for text-to-video; provide `image_url` for image-to-video generation
- Use `callback_url` or poll `/grok/tasks` — video generation is always asynchronous
- `reference_image_urls` is an array — always wrap the URL in `[...]` even for a single reference
- Task state uses `"succeeded"` (not `"completed"`) — check for this value when polling
- `grok-imagine-video-1.5-preview` is a preview model and may have limited availability

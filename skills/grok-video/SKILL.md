---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or reference images using Grok's video generation models. Supports text-to-video and image-guided video generation with multiple aspect ratios and resolutions.
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
  -d '{"prompt": "a golden retriever running through a field of sunflowers", "model": "grok-imagine-video-1.5-fast"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Type | Best For |
|-------|------|----------|
| `grok-imagine-video-1.5-fast` | Text-to-Video / Image-guided | Fast generation from text or reference images (default) |
| `grok-imagine-video-1.5` | Text-to-Video / Image-guided | Higher-quality generation from text or reference images |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a timelapse of storm clouds forming over a mountain range",
  "model": "grok-imagine-video-1.5-fast",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-guided Video

Provide a reference image to anchor the visual style and content.

```json
POST /grok/videos
{
  "prompt": "the scene comes to life with gentle motion",
  "model": "grok-imagine-video-1.5",
  "image_url": "https://example.com/scene.jpg",
  "aspect_ratio": "16:9",
  "resolution": "1080p"
}
```

### 3. Multi-reference Image Video

Supply multiple reference images to guide the generation.

```json
POST /grok/videos
{
  "prompt": "combining these scenes into a cohesive narrative",
  "model": "grok-imagine-video-1.5-fast",
  "reference_image_urls": [
    "https://example.com/ref1.jpg",
    "https://example.com/ref2.jpg"
  ],
  "aspect_ratio": "1:1"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Text description of the video to generate |
| `model` | `"grok-imagine-video-1.5-fast"`, `"grok-imagine-video-1.5"` | Model to use (default: `grok-imagine-video-1.5-fast`) |
| `image_url` | URL | Single reference image URL |
| `reference_image_urls` | array of URLs | Multiple reference image URLs |
| `aspect_ratio` | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Video aspect ratio |
| `resolution` | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `480p`) |
| `duration` | integer | Duration in seconds (default: `8`) |
| `callback_url` | string | Async callback URL |
| `async` | boolean | Return immediately with a task ID for polling |

## Gotchas

- `grok-imagine-video-1.5-fast` is the default model and faster; `grok-imagine-video-1.5` produces higher quality output; both support text and image input
- `image_url` and `reference_image_urls` are mutually exclusive — use one or the other
- Higher resolutions (`1080p`) and longer durations increase generation time
- Poll results via `POST /grok/tasks` using `{"id": "task-id"}` or `{"ids": ["id1", "id2"]}` for batch retrieval

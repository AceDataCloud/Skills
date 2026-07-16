---
name: grok-video
description: Generate AI videos with Grok Imagine (xAI) via AceDataCloud API. Use when creating videos from text prompts, animating a single image into video, or using reference images to guide generation. Supports text-to-video and image-guided generation with configurable aspect ratio, resolution, and duration.
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
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | Text-to-video and image-guided generation (default) |
| `grok-imagine-video-1.5-preview` | Enhanced quality preview model |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a majestic eagle soaring over snow-capped mountains at dawn",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a single input image into a video.

```json
POST /grok/videos
{
  "prompt": "the scene comes alive with gentle wind and subtle motion",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/landscape.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Reference-Guided Generation

Use one or more reference images to guide style or content.

```json
POST /grok/videos
{
  "prompt": "a short film inspired by these reference images",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": [
    "https://example.com/ref1.jpg",
    "https://example.com/ref2.jpg"
  ],
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | No | string | Text description of the video |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model to use (default: `grok-imagine-video`) |
| `image_url` | No | string | Input image URL for image-to-video generation |
| `reference_image_urls` | No | array of strings | Reference image URLs to guide the generation |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"` | Output resolution (default: `480p`) |
| `duration` | No | integer (1–15) | Duration in seconds (default: `8`) |
| `callback_url` | No | string | Async callback URL |
| `async` | No | boolean | Return task ID immediately for async polling |

## Gotchas

- `prompt` and/or `image_url` should be provided — a completely empty request may produce unexpected results
- `reference_image_urls` accepts an array of image URLs to guide style or subject content
- Default resolution is `480p`; use `720p` for higher quality output
- Duration range is 1–15 seconds; default is 8 seconds
- Task polling uses `id` in the `/grok/tasks` request body
- Task states use `"succeeded"` — check for this value when polling

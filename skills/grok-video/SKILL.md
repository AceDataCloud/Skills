---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or images using Grok's video generation models. Supports text-to-video and image-to-video with aspect ratio, resolution, and duration control.
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

| Model | Speed | Best For |
|-------|-------|----------|
| `grok-imagine-video-1.5-fast` | Fast | Quick generation, good quality (default) |
| `grok-imagine-video-1.5` | Standard | Higher quality output |

## Workflows

### 1. Text-to-Video

Generate video from a text description.

```json
POST /grok/videos
{
  "prompt": "a time-lapse of a thunderstorm rolling over a mountain range at dusk",
  "model": "grok-imagine-video-1.5-fast",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 6
}
```

### 2. Image-to-Video

Animate a still image into video.

```json
POST /grok/videos
{
  "prompt": "the scene slowly comes alive with gentle movement",
  "image_url": "https://example.com/scene.jpg",
  "model": "grok-imagine-video-1.5",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 3. Image-to-Video with References

Use multiple reference images for style or subject consistency.

```json
POST /grok/videos
{
  "prompt": "the character walks through a neon-lit street at night",
  "reference_image_urls": [
    "https://example.com/character.jpg",
    "https://example.com/style.jpg"
  ],
  "model": "grok-imagine-video-1.5",
  "aspect_ratio": "9:16"
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | — | Text description of the video to generate |
| `model` | string | `"grok-imagine-video-1.5-fast"` | Model to use (see Models table) |
| `image_url` | string | — | Source image URL for image-to-video |
| `reference_image_urls` | array | — | Additional reference image URLs for style/subject consistency |
| `aspect_ratio` | string | — | Video aspect ratio: `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` |
| `resolution` | string | `"480p"` | Output resolution: `"480p"`, `"720p"`, `"1080p"` |
| `duration` | integer | `6` | Duration in seconds (1–30) |
| `callback_url` | string | — | Webhook URL for async notifications |
| `async` | boolean | — | Return task ID immediately without waiting for result |

## Gotchas

- Both `prompt` and `image_url` can be combined for image-to-video with a guiding prompt
- `reference_image_urls` provides additional style or subject references beyond the main `image_url`
- The default resolution is `"480p"` — specify `"720p"` or `"1080p"` for higher quality
- Duration range is 1–30 seconds with a default of 6 seconds
- Task state is `"succeeded"` (not "completed") when polling via `POST /grok/tasks`
- Poll using `{"id": "<task_id>"}` or retrieve multiple with `{"ids": [...], "action": "retrieve_batch"}`

---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images into video. Supports text-to-video and image-to-video with configurable aspect ratios and resolutions.
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
  -d '{"prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video-1.5", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Speed | Best For |
|-------|-------|----------|
| `grok-imagine-video-1.5` | Standard | High-quality video generation (default) |
| `grok-imagine-video-1.5-fast` | Fast | Quick generation at lower cost |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a time-lapse of a city skyline transitioning from day to night",
  "model": "grok-imagine-video-1.5",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image into a video.

```json
POST /grok/videos
{
  "prompt": "gentle waves lapping on the shore",
  "model": "grok-imagine-video-1.5",
  "image_url": "https://example.com/beach.jpg",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 3. Image-to-Video with Reference Images

Use reference images to guide the visual style or subject.

```json
POST /grok/videos
{
  "prompt": "the character walks through a neon-lit city at night",
  "model": "grok-imagine-video-1.5",
  "reference_image_urls": [
    "https://example.com/character.jpg",
    "https://example.com/style.jpg"
  ],
  "aspect_ratio": "9:16",
  "resolution": "720p"
}
```

### 4. Async Generation with Task Polling

```json
POST /grok/videos
{
  "prompt": "a rocket launching into a starry sky",
  "model": "grok-imagine-video-1.5",
  "callback_url": "https://api.acedata.cloud/health"
}
```

Poll the returned `task_id`:

```json
POST /grok/tasks
{"id": "<task_id>"}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | No | string | Text description of the video |
| `model` | No | `"grok-imagine-video-1.5"`, `"grok-imagine-video-1.5-fast"` | Model to use (default: `grok-imagine-video-1.5`) |
| `image_url` | No | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Reference image URLs for visual guidance |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `"480p"`) |
| `duration` | No | integer 1–15 | Duration in seconds (default: 6) |
| `callback_url` | No | string | Webhook URL for async delivery |
| `async` | No | boolean | Force async mode |

## Gotchas

- Generation is async by default — provide a `callback_url` or poll `/grok/tasks` for results
- `image_url` and `reference_image_urls` are both optional — omit both for pure text-to-video
- `reference_image_urls` can be used alongside `image_url` for combined style and subject guidance
- `1080p` produces higher-quality output than `480p`/`720p` but takes longer and costs more — use `480p` for quick drafts and `1080p` for final renders
- Use `grok-imagine-video-1.5-fast` when speed matters more than peak quality

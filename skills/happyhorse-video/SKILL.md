---
name: happyhorse-video
description: Generate AI videos with HappyHorse via AceDataCloud API. Use when creating videos from text prompts, animating images into video, using reference images for video generation, or editing existing videos. Supports text-to-video, image-to-video, reference-to-video, and video-edit modes.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# HappyHorse Video Generation

Generate AI videos through AceDataCloud's HappyHorse API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/happyhorse/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate", "prompt": "A cinematic white horse lifts its head, the mane moves gently in the sunrise wind", "model": "happyhorse-1.1-t2v"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /happyhorse/tasks` with `{"id": "..."}`.

## Models

| Model | Action | Best For |
|-------|--------|----------|
| `happyhorse-1.1-t2v` | `generate` | Text-to-video (latest) |
| `happyhorse-1.0-t2v` | `generate` | Text-to-video (v1.0) |
| `happyhorse-1.1-i2v` | `image_to_video` | Image-to-video (latest) |
| `happyhorse-1.0-i2v` | `image_to_video` | Image-to-video (v1.0) |
| `happyhorse-1.1-r2v` | `reference_to_video` | Reference-image-to-video (latest) |
| `happyhorse-1.0-r2v` | `reference_to_video` | Reference-image-to-video (v1.0) |
| `happyhorse-1.0-video-edit` | `video_edit` | Video editing |

## Workflows

### 1. Text-to-Video

```json
POST /happyhorse/videos
{
  "action": "generate",
  "prompt": "A cinematic white horse lifts its head, the mane moves gently in the sunrise wind, slow camera push in, warm film lighting",
  "model": "happyhorse-1.1-t2v",
  "resolution": "720P",
  "ratio": "16:9",
  "duration": 5
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /happyhorse/videos
{
  "action": "image_to_video",
  "prompt": "the horse begins to gallop across the meadow",
  "model": "happyhorse-1.1-i2v",
  "image_url": "https://example.com/horse.jpg"
}
```

### 3. Reference-to-Video

Generate a video using multiple reference images for style or character consistency.

```json
POST /happyhorse/videos
{
  "action": "reference_to_video",
  "prompt": "a majestic horse running on the beach at sunset",
  "model": "happyhorse-1.1-r2v",
  "image_urls": [
    "https://example.com/ref1.jpg",
    "https://example.com/ref2.jpg"
  ]
}
```

### 4. Video Editing

Edit an existing video using a text prompt.

```json
POST /happyhorse/videos
{
  "action": "video_edit",
  "prompt": "change the background to a snowy mountain landscape",
  "model": "happyhorse-1.0-video-edit",
  "video_url": "https://example.com/input.mp4"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"generate"`, `"image_to_video"`, `"reference_to_video"`, `"video_edit"` | Operation mode |
| `model` | see Models table | Model to use |
| `prompt` | string | Video description or editing instruction |
| `image_url` | string | Source image URL (for `image_to_video`) |
| `image_urls` | array of strings | Reference image URLs (for `reference_to_video`) |
| `video_url` | string | Source video URL (for `video_edit`) |
| `resolution` | `"720P"`, `"1080P"` | Output resolution (default: 720P) |
| `ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio (default: 16:9) |
| `duration` | integer | Duration in seconds |
| `audio_setting` | `"auto"`, `"origin"` | Audio generation mode (`auto` = AI-generated, `origin` = keep original) |
| `watermark` | boolean | Add watermark to video |
| `seed` | integer | Seed for reproducibility |
| `callback_url` | string | Async callback URL; returns a `task_id` immediately |
| `async` | boolean | Force async mode |

## Gotchas

- `image_url` is required for `image_to_video`; `image_urls` for `reference_to_video`; `video_url` for `video_edit`
- t2v/i2v/r2v use separate model series — choose the model that matches the `action`
- `audio_setting: "origin"` preserves the original audio from a source video (relevant for `video_edit`)
- Task polling accepts `id` (single task) or `ids` (batch) in the `/happyhorse/tasks` request body

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

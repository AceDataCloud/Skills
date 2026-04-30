---
name: hailuo-video
description: Generate AI videos with Hailuo (MiniMax) via AceDataCloud API. Use when creating videos from text descriptions or animating images into video. Supports text-to-video and image-to-video with director mode for precise control.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Hailuo Video Generation

Generate AI videos through AceDataCloud's Hailuo (MiniMax) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/hailuo/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate", "prompt": "a dolphin jumping through ocean waves at golden hour", "model": "minimax-t2v"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /hailuo/tasks` with `{"action": "retrieve", "id": "<task_id>"}`.

## Models

| Model | Type | Best For |
|-------|------|----------|
| `minimax-t2v` | Text-to-Video | Creating video from text description |
| `minimax-i2v` | Image-to-Video | Animating a still image |
| `minimax-i2v-director` | Image-to-Video (Director) | Precise control over animation from image |

## Workflows

### 1. Text-to-Video

```json
POST /hailuo/videos
{
  "action": "generate",
  "prompt": "a time-lapse of flowers blooming in a meadow",
  "model": "minimax-t2v"
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /hailuo/videos
{
  "action": "generate",
  "prompt": "gentle wind blows through the scene",
  "model": "minimax-i2v",
  "first_image_url": "https://example.com/landscape.jpg"
}
```

### 3. Image-to-Video (Director Mode)

More precise control over the animation.

```json
POST /hailuo/videos
{
  "action": "generate",
  "prompt": "camera slowly zooms in while leaves fall gently",
  "model": "minimax-i2v-director",
  "first_image_url": "https://example.com/scene.jpg"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `action` | Yes | `"generate"` | Action type |
| `prompt` | No | string | Video description |
| `model` | No | `"minimax-t2v"`, `"minimax-i2v"`, `"minimax-i2v-director"` | Model (default: `minimax-t2v`) |
| `first_image_url` | For i2v | string | Source image URL (required for image-to-video) |
| `callback_url` | No | string | Async callback URL |

## Response Structure

```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "model": "minimax-t2v",
      "prompt": "a dolphin jumping through ocean waves",
      "first_image_url": null,
      "video_url": "https://cdn.example.com/videos/a1b2c3d4.mp4",
      "status": "Success"
    }
  ],
  "success": true,
  "task_id": "a1b2c3d4-..."
}
```

## Task Retrieval

Poll task status via `POST /hailuo/tasks`:

| Parameter | Description |
|-----------|-------------|
| `action` | `"retrieve"` for a single task, `"retrieve_batch"` for multiple |
| `id` | Task ID for single retrieval |
| `ids` | Array of task IDs for batch retrieval |

## Gotchas

- `first_image_url` is **required** for `minimax-i2v` and `minimax-i2v-director` models
- Director mode (`minimax-i2v-director`) provides finer camera/motion control than standard i2v
- The `action` field currently only supports `"generate"` — no extend or edit
- Flat pricing per generation regardless of model

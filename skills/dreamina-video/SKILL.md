---
name: dreamina-video
description: Generate AI talking-photo videos with Dreamina (ByteDance OmniHuman) via AceDataCloud API. Use when animating a portrait image with a reference audio track to produce a lip-synced video. Supports the omnihuman-1.5 model with optional prompt and mask.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Animate a portrait image with a reference audio track using AceDataCloud's Dreamina (ByteDance OmniHuman) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "omnihuman-1.5",
    "image_url": "https://cdn.acedata.cloud/4hfydw.jpg",
    "audio_url": "https://cdn1.suno.ai/1b694cae-8b5f-424f-a5bf-2f27b7697843.mp3",
    "callback_url": "https://api.acedata.cloud/health"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `omnihuman-1.5` | Talking-photo: animate a portrait with a voice track |

## Generate a Talking-Photo Video

Provide a portrait image and a reference audio. The model lip-syncs and animates the subject to match the audio.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural head movement, bright studio lighting"
}
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `model` | No | string | Model to use (default: `omnihuman-1.5`) |
| `image_url` | **Yes** | string (URI) | Public URL of a portrait/face image |
| `audio_url` | **Yes** | string (URI) | Public URL of the driving audio |
| `prompt` | No | string | Optional text to guide generation style |
| `mask_url` | No | array of strings | Optional mask image URLs to define the animated region |
| `callback_url` | No | string (URI) | Webhook to receive the result when done |
| `async` | No | boolean | Run asynchronously (recommended) |

## Poll for Results

```bash
curl -X POST https://api.acedata.cloud/dreamina/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id>"}'
```

Response when done:

```json
{
  "id": "362b4fed-67bd-11f1-ad11-00163e57d510",
  "response": {
    "success": true,
    "data": {
      "status": "done",
      "video_url": "https://cdn.acedata.cloud/634d760216.mp4",
      "image_url": "https://cdn.acedata.cloud/4hfydw.jpg",
      "audio_url": "https://cdn.acedata.cloud/6f7d62b18b.wav"
    }
  }
}
```

## Gotchas

- Both `image_url` and `audio_url` are **required** — the API will return a 400 error if either is missing
- `image_url` must be a public URL of a portrait/face image — non-face images will fail with a 403 error
- Generation is async — always supply `callback_url` to receive the task ID immediately, then poll `/dreamina/tasks`
- `mask_url` accepts an array of public image URLs that define which region of the image should be animated

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

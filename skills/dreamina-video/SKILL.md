---
name: dreamina-video
description: Generate AI avatar videos with ByteDance Dreamina via AceDataCloud API. Use when animating a portrait photo with audio to create a talking avatar video. Supports the omnihuman-1.5 model with optional masking and prompt guidance.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-dreamina for tool-use.
---

# Dreamina Video Generation

Generate AI avatar videos through AceDataCloud's ByteDance Dreamina API. Animate a portrait image with an audio track to create a realistic talking-head video.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/portrait.jpg",
    "audio_url": "https://example.com/speech.mp3",
    "model": "omnihuman-1.5",
    "callback_url": "https://api.acedata.cloud/health"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `omnihuman-1.5` | Portrait animation — drive a face/body with audio |

## Workflows

### 1. Basic Talking Avatar

Animate a portrait photo using an audio track.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "model": "omnihuman-1.5"
}
```

### 2. Avatar with Prompt Guidance

Add a text prompt to further guide the animation style.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural head movements, warm lighting",
  "model": "omnihuman-1.5"
}
```

### 3. Masked Animation

Use a mask to restrict the animation to a specific region (e.g., face only).

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "mask_url": ["https://example.com/face_mask.jpg"],
  "model": "omnihuman-1.5"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | **Yes** | string | Portrait image URL to animate |
| `audio_url` | **Yes** | string | Audio track URL to drive the animation |
| `model` | No | `"omnihuman-1.5"` | Model to use (default: `omnihuman-1.5`) |
| `prompt` | No | string | Text guidance for animation style |
| `mask_url` | No | array of strings | Mask image URLs to restrict the animation region |
| `callback_url` | No | string | Async webhook notification URL |
| `async` | No | boolean | Return immediately with a task ID |

## Task Polling

```json
POST /dreamina/tasks
{
  "id": "<task_id>"
}
```

Batch polling:

```json
POST /dreamina/tasks
{
  "ids": ["<task_id_1>", "<task_id_2>"],
  "action": "retrieve_batch"
}
```

You can also poll by `trace_id` if provided:

```json
POST /dreamina/tasks
{
  "trace_id": "<trace_id>"
}
```

## Gotchas

- Both `image_url` and `audio_url` are **required** — the model drives a portrait with audio
- `mask_url` is an **array** — pass one or more mask image URLs
- The `omnihuman-1.5` model is specifically designed for portrait/avatar animation; it is not a general text-to-video model
- Task polling uses `id` (not `task_id`) in the `/dreamina/tasks` request body
- `trace_id` is an alternative identifier returned in some responses

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

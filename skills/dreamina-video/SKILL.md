---
name: dreamina-video
description: Generate AI talking-head and human video animations with Dreamina (OmniHuman) via AceDataCloud API. Use when animating a portrait photo with an audio track to produce a realistic talking-head video. Requires both an image and an audio URL; supports optional prompt and mask inputs.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate talking-head and human animation videos through AceDataCloud's Dreamina (OmniHuman) API.

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

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | Realistic talking-head and body animation from image + audio (only model available) |

## Workflows

### 1. Talking-Head Animation

Animate a portrait photo to speak with a given audio track.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3"
}
```

### 2. With Prompt and Mask

Provide a prompt to guide the animation style and an optional mask to constrain the region that animates.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural talking head with subtle gestures",
  "mask_url": [
    "https://example.com/face-mask.png",
    "https://example.com/shoulder-mask.png"
  ]
}
```

### 3. Async Generation with Task Polling

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "callback_url": "https://api.acedata.cloud/health"
}
```

Poll the returned `task_id`:

```json
POST /dreamina/tasks
{"id": "<task_id>"}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `model` | No | `"omnihuman-1.5"` | Model to use (default: `omnihuman-1.5`) |
| `image_url` | **Yes** | string (URI) | Portrait or full-body image URL to animate |
| `audio_url` | **Yes** | string (URI) | Audio track URL for driving the animation |
| `prompt` | No | string | Text description to guide the animation style |
| `mask_url` | No | array of strings (URI) | Mask image URLs to constrain the animated region |
| `callback_url` | No | string (URI) | Webhook URL for async delivery |
| `async` | No | boolean | Force async mode |

## Task Polling

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"retrieve"`, `"retrieve_batch"` | Retrieval mode |
| `id` | string | Single task ID |
| `ids` | array | Multiple task IDs (retrieve_batch) |
| `trace_id` | string | Trace ID returned with the original request |

Check `data.status == "done"` to confirm completion.

## Gotchas

- Both `image_url` and `audio_url` are **required** — the model always needs both a visual subject and a driving audio
- `omnihuman-1.5` is currently the only available model
- `mask_url` is an array — pass a single-element array for one mask
- Generation is typically async; poll `/dreamina/tasks` with the returned `task_id`
- Check `data.status` field for `"done"` to confirm the video is ready

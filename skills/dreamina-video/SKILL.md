---
name: dreamina-video
description: Generate AI portrait animation videos with Dreamina (ByteDance) via AceDataCloud API. Use when animating a portrait photo with an audio track to produce a lip-synced or expression-driven video. Requires both an image and audio input.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI portrait animation videos through AceDataCloud's Dreamina (ByteDance) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/portrait.jpg",
    "audio_url": "https://example.com/speech.mp3",
    "callback_url": "https://api.acedata.cloud/health"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Model

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | Portrait animation with lip-sync from audio (only model, default) |

## Workflow

### Portrait Animation with Audio

Animate a portrait photo by driving it with an audio clip.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/voiceover.mp3",
  "model": "omnihuman-1.5",
  "prompt": "natural head movement, warm expression"
}
```

### With Mask (Focus Area)

Optionally supply mask URLs to restrict animation to specific regions.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/voiceover.mp3",
  "mask_url": [
    "https://example.com/face-mask.png"
  ]
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | Yes | string (URI) | Portrait photo to animate |
| `audio_url` | Yes | string (URI) | Audio track to drive animation |
| `model` | No | `"omnihuman-1.5"` | Model (default: `omnihuman-1.5`) |
| `prompt` | No | string | Text hint for expression or motion style |
| `mask_url` | No | array of strings (URI) | Mask images to limit animated region |
| `callback_url` | No | string (URI) | Webhook URL for async completion |
| `async` | No | boolean | Force async mode |

## Polling

```json
POST /dreamina/tasks
{
  "id": "<task_id>"
}
```

Response includes `data.status`. Terminal state: `"done"`.

For batch polling:

```json
POST /dreamina/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

You can also poll by `trace_id`:

```json
POST /dreamina/tasks
{
  "trace_id": "<trace_id>"
}
```

## Gotchas

- Both `image_url` and `audio_url` are **required**
- Only one model is available: `omnihuman-1.5`
- Use `callback_url` to avoid HTTP timeout on long video generations
- Poll `/dreamina/tasks` until `data.status` equals `"done"` (not `"succeeded"`)
- Best results come from a front-facing portrait photo and a clean audio clip

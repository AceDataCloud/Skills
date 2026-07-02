---
name: dreamina-video
description: Generate AI talking-head videos with Dreamina (ByteDance) via AceDataCloud API. Use when animating a portrait image with an audio track to produce a lip-synced talking-head video. Requires an image URL and an audio URL; model omnihuman-1.5.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI talking-head videos through AceDataCloud's Dreamina API. Provide a portrait image and a driving audio file; Dreamina synchronises the face to the speech/audio.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "omnihuman-1.5",
    "image_url": "https://cdn.acedata.cloud/4hfydw.jpg",
    "audio_url": "https://cdn1.suno.ai/1b694cae-8b5f-424f-a5bf-2f27b7697843.mp3"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}` or `{"trace_id": "..."}`.

## Models

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | Default and only currently supported model — full-body / portrait talking-head |

## Workflow

### Generate a Talking-Head Video

Provide a portrait image and an audio clip. The model generates a video where the subject's face and mouth move in sync with the audio.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/narration.mp3",
  "prompt": "natural expressive movement"
}
```

### With Mask (Region Control)

Use `mask_url` to provide one or more mask images that constrain where animation is applied.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/narration.mp3",
  "mask_url": [
    "https://example.com/face-mask.png"
  ]
}
```

## Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `image_url` | Yes | string (URL) | Source portrait or full-body image |
| `audio_url` | Yes | string (URL) | Driving audio track (speech or music) |
| `model` | No | string | Model to use (default: `omnihuman-1.5`) |
| `prompt` | No | string | Optional text hint to guide animation style |
| `mask_url` | No | array of URLs | Mask images to restrict the animation region |
| `callback_url` | No | string (URL) | Webhook URL called when the task completes |
| `async` | No | boolean | Return a task ID immediately (default: true) |

## Polling Tasks

```json
POST /dreamina/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
}
```

Or poll by `trace_id`:

```json
POST /dreamina/tasks
{
  "action": "retrieve",
  "trace_id": "<trace_id>"
}
```

Batch polling:

```json
POST /dreamina/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

## Gotchas

- Both `image_url` and `audio_url` are **required** — the request will be rejected without them
- The only currently supported model is `omnihuman-1.5`
- Generation is async — always poll `/dreamina/tasks` with the returned `task_id` or `trace_id`
- `mask_url` is an **array** even if you only provide a single mask
- The response includes `video_url`, `image_url`, and `audio_url` in the `data` object once complete

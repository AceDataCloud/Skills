---
name: dreamina-video
description: Generate AI portrait videos with Dreamina (ByteDance) via AceDataCloud API. Use when animating a portrait image with an audio track to produce a talking/singing avatar video. Requires both an image URL and an audio URL.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI portrait videos through AceDataCloud's Dreamina (ByteDance) API. Dreamina animates a portrait image driven by an audio track, producing a talking or singing avatar video.

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

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | Portrait animation model — the only available model (default) |

## Workflow

### Animate a Portrait with Audio

Provide a portrait image and an audio file. Dreamina will animate the face to sync with the audio.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural head movements",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### With Mask

Apply a mask to restrict animation to specific regions of the image.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "mask_url": ["https://example.com/face-mask.png"]
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | Yes | string (URI) | Public URL of the portrait image |
| `audio_url` | Yes | string (URI) | Public URL of the audio file (speech/song) |
| `model` | No | `"omnihuman-1.5"` | Animation model (default: `omnihuman-1.5`) |
| `prompt` | No | string | Optional guidance for animation style |
| `mask_url` | No | array of strings | URLs of mask images to control animated region |
| `callback_url` | No | string | Webhook URL for async result delivery |
| `async` | No | boolean | Force async mode |

## Task Polling

The response includes a `task_id`. Poll using `trace_id` or `id`:

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

For batch polling:

```json
POST /dreamina/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

The result is in `data.video_url` when `data.status` is `"done"`.

## Response Example

```json
{
  "success": true,
  "task_id": "0c0b4d3a-2f1e-4a6b-9c2d-2b3c4d5e6f70",
  "trace_id": "a9063166-26ed-4451-85b5-54e896817c69",
  "data": {
    "task_id": "362b4fed67bd11f1ad1100163e57d510",
    "status": "done",
    "video_url": "https://cdn.acedata.cloud/634d760216.mp4",
    "image_url": "https://cdn.acedata.cloud/4hfydw.jpg",
    "audio_url": "https://cdn.acedata.cloud/6f7d62b18b.wav"
  }
}
```

## Gotchas

- Both `image_url` and `audio_url` are **required** — the API will return an error if either is missing
- Use a public URL for `image_url`; a clear, well-lit portrait photo yields the best results
- Poll `data.status` for `"done"` — the terminal success state
- `mask_url` is an array — pass one or more mask image URLs to control which parts of the image are animated
- Use `callback_url` to avoid HTTP timeout on longer generations

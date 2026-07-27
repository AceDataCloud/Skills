---
name: dreamina-video
description: Generate AI human-animation videos with Dreamina (OmniHuman) via AceDataCloud API. Use when animating a portrait or character image with audio — lip-sync, body movement, and expression driven by an audio clip. Requires both an image and an audio source.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI-driven human animation videos through AceDataCloud's Dreamina (OmniHuman) API. Animate a portrait or character image synchronized to an audio clip.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/portrait.jpg", "audio_url": "https://example.com/speech.mp3", "model": "omnihuman-1.5", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Model

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | OmniHuman v1.5 — drives full body and face animation from audio |

## Workflow

### Animate a Portrait with Audio

Provide a character image and an audio file. Dreamina generates a video with the character's lips, face, and body animated to match the audio.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/speaker-portrait.jpg",
  "audio_url": "https://example.com/narration.mp3",
  "prompt": "professional presenter speaking on stage"
}
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image_url` | **Yes** | URL of the character/portrait image to animate |
| `audio_url` | **Yes** | URL of the audio clip driving the animation |
| `model` | No | Model (only `"omnihuman-1.5"` currently) |
| `prompt` | No | Additional description for motion style or context |
| `mask_url` | No | Array of mask image URLs for controlling the animation region |
| `callback_url` | No | Async callback URL |
| `async` | No | Return task ID immediately |

## Task Polling

```json
POST /dreamina/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
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

Check `data.status`; terminal state is `"done"`.

## Gotchas

- Both `image_url` and `audio_url` are **required**
- Currently only one model is available: `omnihuman-1.5`
- All generation is **async** — use `callback_url` or `async: true` and poll `/dreamina/tasks`
- `mask_url` is an array of image URLs that define which regions of the image to animate

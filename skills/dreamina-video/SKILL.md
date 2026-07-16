---
name: dreamina-video
description: Generate AI talking-head videos with Dreamina (OmniHuman) via AceDataCloud API. Use when animating a portrait image to speak or sing along to an audio track. Provide a face image and an audio file to produce a synchronized talking-head video. Supports optional mask and prompt for fine-grained control.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI talking-head videos through AceDataCloud's Dreamina (OmniHuman) API. Animate a portrait image to speak or sing in sync with a provided audio track.

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

## Model

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | OmniHuman 1.5 — talking-head generation from image + audio (default and only model) |

## Workflows

### 1. Basic Talking-Head

Animate a portrait photo with an audio track.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3"
}
```

### 2. Guided Generation with Prompt

Add a text prompt to provide stylistic guidance.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural lighting, realistic facial expressions"
}
```

### 3. Masked Generation

Use mask images to restrict the animation region.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "mask_url": [
    "https://example.com/face-mask.jpg"
  ]
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | Yes | string (URI) | Public URL of a portrait/face image |
| `audio_url` | Yes | string (URI) | Public URL of the audio to animate to (speech, song, etc.) |
| `model` | No | `"omnihuman-1.5"` | Model to use (default and only option: `omnihuman-1.5`) |
| `prompt` | No | string | Optional text guidance for the generation |
| `mask_url` | No | array of strings | Optional mask image URLs to restrict the animation area |
| `callback_url` | No | string (URI) | Async callback URL |
| `async` | No | boolean | Return task ID immediately for async polling |

## Task Polling

Poll `/dreamina/tasks` with the task ID to retrieve results:

```json
POST /dreamina/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
}
```

Response includes `data.video_url` when the task status is `"done"`.

## Gotchas

- Both `image_url` and `audio_url` are **required** — the request will fail if either is missing
- `image_url` should be a clear portrait/face image for best results
- `mask_url` is an array; provide one or more mask image URLs to define the animated region
- Task status field is `data.status` (not `data.state`); check for `"done"` when polling
- Task polling accepts `id` or `trace_id` in the `/dreamina/tasks` request body

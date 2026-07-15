---
name: dreamina-video
description: Generate AI talking-photo and digital-human videos with Dreamina (OmniHuman) via AceDataCloud API. Use when animating a portrait photo with a driving audio clip to create a lip-synced video where the person speaks. Requires a portrait image URL and an audio URL.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI talking-photo and digital-human videos through AceDataCloud's Dreamina (OmniHuman 1.5) API. Provide a portrait image and driving audio to produce a video with synchronized lip movement.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model": "omnihuman-1.5", "image_url": "https://example.com/portrait.jpg", "audio_url": "https://example.com/speech.mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Models

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | Audio-driven digital-human video generation (default) |

## Workflows

### 1. Basic Talking-Photo

Animate a portrait image with a driving audio clip.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.wav"
}
```

### 2. With Expression Prompt

Steer the expression, emotion, and style of the generated video.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural smile, calm expression, professional tone"
}
```

### 3. Multi-Person with Mask

Target a specific person in a group image using mask URLs.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/group-photo.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "mask_url": [
    "https://example.com/person-mask.png"
  ]
}
```

### 4. Async Generation

For long-running jobs, use async mode and poll for the result.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "async": true
}
```

Then poll:

```json
POST /dreamina/tasks
{
  "action": "retrieve",
  "id": "<task_id_from_response>"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `model` | No | `"omnihuman-1.5"` (default) | Model to use |
| `image_url` | **Yes** | string | Public URL of the portrait image; clear, well-lit, front-facing face works best |
| `audio_url` | **Yes** | string | Public URL of the driving audio (mp3/wav); keep under 60s |
| `prompt` | No | string | Steers expression, emotion, stability, and style |
| `mask_url` | No | string[] | Subject mask URLs to target a specific person in a multi-person image |
| `callback_url` | No | string | Async callback URL; returns `task_id` immediately when set |
| `async` | No | boolean | When `true`, returns `task_id` immediately; poll via `/dreamina/tasks` |

## Response

```json
{
  "success": true,
  "task_id": "0c0b4d3a-2f1e-4a6b-9c2d-2b3c4d5e6f70",
  "trace_id": "a9063166-26ed-4451-85b5-54e896817c69",
  "data": {
    "task_id": "362b4fed67bd11f1ad1100163e57d510",
    "status": "done",
    "video_url": "https://cdn.acedata.cloud/output.mp4",
    "image_url": "https://cdn.acedata.cloud/portrait.jpg",
    "audio_url": "https://cdn.acedata.cloud/speech.wav"
  }
}
```

## Gotchas

- Both `image_url` and `audio_url` are **required** — the API will return `400 bad_request` without them
- Use a clear, well-lit, front-facing portrait for best results; the face should be unobstructed
- Audio should be mp3 or wav, publicly reachable; keep it under 60s (≤30s recommended for 1080p quality)
- Billed by generated video duration (approximately per second)

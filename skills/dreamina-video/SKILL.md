---
name: dreamina-video
description: Generate AI talking-photo and digital human videos with Dreamina (OmniHuman 1.5) via AceDataCloud API. Use when animating a portrait image to speak in sync with an audio clip, creating digital human presentations, or producing audio-driven lip-sync videos.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate AI talking-photo digital human videos through AceDataCloud's Dreamina (OmniHuman 1.5) API. Provide a portrait image and a driving audio clip; the person in the image speaks in sync with the audio.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/portrait.jpg", "audio_url": "https://example.com/speech.mp3", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

Poll the returned `task_id`:

```bash
curl -X POST https://api.acedata.cloud/dreamina/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Models

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | OmniHuman 1.5 — audio-driven talking-photo digital human (default) |

## Workflows

### 1. Talking-Photo Video (Portrait + Audio)

Animate a portrait image to lip-sync with a speech audio clip:

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/person.jpg",
  "audio_url": "https://example.com/narration.mp3",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 2. Guided Generation with Prompt

Add an optional prompt to influence expression, emotion, or style:

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/presenter.jpg",
  "audio_url": "https://example.com/announcement.wav",
  "prompt": "confident and professional expression, subtle head movement",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 3. Multi-Person Image (with Mask)

For images with multiple people, supply `mask_url` to specify which person to drive:

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/group-photo.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "mask_url": ["https://example.com/person-mask.jpg"],
  "callback_url": "https://api.acedata.cloud/health"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | Yes | string (URL) | Public URL of the portrait image. A clear frontal face works best. |
| `audio_url` | Yes | string (URL) | Public URL of the driving audio (mp3/wav). The character lip-syncs to it. Keep it under 60 s. |
| `model` | No | `"omnihuman-1.5"` | Model to use (default: `omnihuman-1.5`) |
| `prompt` | No | string | Optional text to guide expression, emotion, stability, and style |
| `mask_url` | No | array of URLs | Subject mask URLs (from object detection) to drive a specific person in a multi-person image |
| `callback_url` | No | string | Webhook URL; the request returns `task_id` immediately and the result is delivered here when ready |

## Response Structure

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

- Both `image_url` and `audio_url` are required — neither can be omitted
- Use a clear, frontal portrait for best lip-sync results; group photos require `mask_url` to specify the target person
- Audio should be under 60 seconds; longer clips may fail or be truncated
- `mask_url` is an array — wrap the single mask URL in `[...]`
- Video generation is asynchronous — always use `callback_url` or poll `/dreamina/tasks` for the result

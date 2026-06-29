---
name: dreamina-video
description: Generate AI human videos with Dreamina (OmniHuman) via AceDataCloud API. Use when animating a real person's image with driving audio to produce a talking/singing portrait video. Requires both a character image and an audio clip. Supports optional mask and prompt for fine-grained control.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Dreamina Video Generation

Generate human portrait videos through AceDataCloud's Dreamina (OmniHuman) API. Given a person's photo and a driving audio clip, the model animates the face and body to match the audio.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "omnihuman-1.5", "image_url": "https://example.com/person.jpg", "audio_url": "https://example.com/speech.mp3", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Models

| Model | Description |
|-------|-------------|
| `omnihuman-1.5` | Latest OmniHuman model — full-body portrait animation from a single image and audio |

## Workflow

### 1. Generate a Talking Portrait

Animate a person's photo with an audio clip (speech or singing).

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "prompt": "natural head movement, expressive face"
}
```

### 2. With a Mask

Use a mask to control which region of the image is animated. Provide mask as an array of URLs.

```json
POST /dreamina/videos
{
  "model": "omnihuman-1.5",
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/song.mp3",
  "mask_url": ["https://example.com/face-mask.png"]
}
```

### 3. Poll for Results

```json
POST /dreamina/tasks
{
  "id": "<task_id>"
}
```

Or batch poll:

```json
POST /dreamina/tasks
{
  "ids": ["<task_id_1>", "<task_id_2>"],
  "action": "retrieve_batch"
}
```

## Parameters

### POST /dreamina/videos

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `model` | Yes | `"omnihuman-1.5"` | Model to use |
| `image_url` | Yes | string | URL of the character/person image to animate |
| `audio_url` | Yes | string | URL of the driving audio clip (speech or singing) |
| `prompt` | No | string | Additional description for generation style |
| `mask_url` | No | array of strings | URLs of mask images to constrain the animation area |
| `callback_url` | No | string | Async callback URL |

### POST /dreamina/tasks

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `id` | For single | string | Task ID from `/dreamina/videos` |
| `ids` | For batch | array | Multiple task IDs for batch polling |
| `action` | For batch | `"retrieve_batch"` | Required when using `ids` |
| `trace_id` | No | string | Alternative trace ID for polling |

## Gotchas

- Both `image_url` and `audio_url` are **required** — the model needs a person photo and driving audio
- All generation is async — always set `"callback_url"` to get a task id immediately, then poll `/dreamina/tasks` using `{"id":"<task_id>"}`
- Use high-quality portrait images with a clear face for best results
- `mask_url` is an array — pass a list of mask image URLs
- The model animates the full body if visible; use `mask_url` to restrict to just the face

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

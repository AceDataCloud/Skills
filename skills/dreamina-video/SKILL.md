---
name: dreamina-video
description: Generate AI portrait videos with Dreamina via AceDataCloud API. Use when animating a portrait image with audio to create a talking/singing character video. Requires both an image and audio input. Supports optional prompt and mask for fine-grained control.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-dreamina for tool-use.
---

# Dreamina Video Generation

Generate AI portrait videos through AceDataCloud's Dreamina API. Animate a portrait image with audio to produce a talking or singing character video.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/dreamina/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/portrait.jpg", "audio_url": "https://example.com/speech.mp3", "model": "omnihuman-1.5"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /dreamina/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `omnihuman-1.5` | Portrait animation with audio (default and only model) |

## Workflows

### 1. Animate Portrait with Audio

Provide a portrait image and an audio file to generate a talking or singing video.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "model": "omnihuman-1.5"
}
```

### 2. Guided Animation with Prompt

Add a text prompt to guide the character's expression and motion.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/song.mp3",
  "prompt": "the character smiles warmly and nods while speaking",
  "model": "omnihuman-1.5"
}
```

### 3. Masked Animation

Use a mask to restrict animation to a specific region of the image.

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "mask_url": ["https://example.com/mask.jpg"],
  "model": "omnihuman-1.5"
}
```

### 4. Async Generation with Task Polling

Pass `async: true` to get a task ID immediately and poll for the result:

```json
POST /dreamina/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "callback_url": "https://api.acedata.cloud/health",
  "async": true
}
```

Poll the returned `task_id`:

```json
POST /dreamina/tasks
{"id": "<task_id>"}
```

## Parameters

### `POST /dreamina/videos`

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | Yes | string | URL of the portrait image to animate |
| `audio_url` | Yes | string | URL of the audio file to drive the animation |
| `model` | No | `"omnihuman-1.5"` | Model to use (default: `omnihuman-1.5`) |
| `prompt` | No | string | Text description to guide expression and motion |
| `mask_url` | No | array of strings | Mask image URLs to restrict animated region |
| `callback_url` | No | string | Webhook URL for async delivery |
| `async` | No | boolean | Return a `task_id` immediately and process asynchronously |

### `POST /dreamina/tasks`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `id` | string | Task ID to retrieve |
| `ids` | array | Multiple task IDs to retrieve in batch |
| `trace_id` | string | Trace ID for retrieval |
| `action` | `"retrieve"`, `"retrieve_batch"` | Action type (default: `retrieve`) |

## Gotchas

- Both `image_url` and `audio_url` are **required** — the API cannot generate without both
- `mask_url` accepts an array of image URLs; white pixels in the mask indicate the animated region
- Task `data.status` is `"done"` when generation is complete
- Poll using `id` (the task ID from the response)

> **MCP:** `pip install mcp-dreamina` | Hosted: `https://dreamina.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

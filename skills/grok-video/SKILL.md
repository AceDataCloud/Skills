---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text descriptions or animating images into video with Grok Imagine models. Supports text-to-video and image-to-video with multiple quality tiers and pricing options.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok (xAI) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video-1.5-fast:reverse"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

The model name suffix selects the upstream endpoint: `:reverse` routes to the fast/standard endpoint (cheaper); `:official` routes to the official endpoint (higher quality, billed per output second).

| Model | Modes | Duration | Notes |
|-------|-------|----------|-------|
| `grok-imagine-video-1.5-fast:reverse` | Text-to-Video, Image-to-Video | 6–30 s | Default. Tiered billing, cheapest. |
| `grok-imagine-video:reverse` | Text-to-Video, Image-to-Video | 1–15 s | Per-output-second billing. |
| `grok-imagine-video:official` | Text-to-Video, Image-to-Video | 1–15 s | Official endpoint, higher quality. |
| `grok-imagine-video-1.5:official` | Image-to-Video only | 1–15 s | **Requires** `image_url`; `prompt` is optional. Supports up to 1080p. |
| `grok-imagine-video` | Text-to-Video, Image-to-Video | 1–30 s | Legacy model. |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a whale breaching in slow motion at golden hour",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 6
}
```

### 2. Image-to-Video

Animate a still image with an optional guiding prompt.

```json
POST /grok/videos
{
  "prompt": "the scene gently comes to life",
  "model": "grok-imagine-video:reverse",
  "image_url": "https://example.com/scene.jpg",
  "aspect_ratio": "16:9",
  "duration": 6
}
```

### 3. Image-to-Video (High Quality, Official)

Use `grok-imagine-video-1.5:official` for highest quality — `image_url` is required.

```json
POST /grok/videos
{
  "model": "grok-imagine-video-1.5:official",
  "image_url": "https://example.com/portrait.jpg",
  "resolution": "1080p",
  "duration": 6
}
```

### 4. Async (Poll for Result)

Set `async: true` to receive a task ID immediately, then poll for the result.

```json
POST /grok/videos
{
  "prompt": "time-lapse of a city at night",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "async": true
}
```

Poll via:

```json
POST /grok/tasks
{
  "id": "<task_id>",
  "action": "retrieve"
}
```

## Parameters

### POST /grok/videos

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | For text-to-video | string | Text description of the video. Required when no `image_url`; optional with `image_url`. |
| `model` | No | see Models table | Model to use (default: `grok-imagine-video-1.5-fast:reverse`) |
| `image_url` | For `grok-imagine-video-1.5:official` | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Optional reference images to guide style/content |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `480p`) |
| `duration` | No | integer 1–30 | Video length in seconds (default: 6). `grok-imagine-video-1.5-fast:reverse`: 6–30 s; other `:reverse` models: 1–15 s; `grok-imagine-video`: 1–30 s. |
| `callback_url` | No | string | Webhook URL to receive result when complete |
| `async` | No | boolean | Return `task_id` immediately and poll for result |

### POST /grok/tasks

| Parameter | Values | Description |
|-----------|--------|-------------|
| `id` | string | Task ID from `/grok/videos` response |
| `ids` | array of strings | Batch retrieve multiple task IDs |
| `action` | `"retrieve"`, `"retrieve_batch"` | Operation type (default: `retrieve`) |

## Gotchas

- `grok-imagine-video-1.5:official` **requires** `image_url` — it does not support text-only generation
- `prompt` is required when not providing `image_url`; optional when `image_url` is set
- `duration` range varies by model: `grok-imagine-video-1.5-fast:reverse` supports 6–30 s; other models support 1–15 s
- Recommended durations are **6 s or 10 s** — these standard lengths are most reliable
- `:reverse` suffix = standard endpoint (cheaper); `:official` = official xAI endpoint (higher quality, per-second billing)
- Task polling uses `id` (not `task_id`) in the `/grok/tasks` request body
- Check `data[].state` for `"succeeded"` to confirm completion when polling

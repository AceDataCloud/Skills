---
name: grok-video
description: Generate AI videos with Grok via AceDataCloud API. Use when creating videos from text prompts or animating an input image. Supports multiple Grok video model routes (`:reverse` and `:official`), optional reference images, and async task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A cinematic shot of a kitten chasing a butterfly in a sunlit garden","model":"grok-imagine-video-1.5-fast:reverse","resolution":"480p","duration":6}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id":"..."}`.

## Models

| Model | Route | Notes |
|-------|-------|-------|
| `grok-imagine-video-1.5-fast:reverse` | Reverse | Default model; supports text-to-video and image-to-video |
| `grok-imagine-video:reverse` | Reverse | Supports text-to-video and image-to-video |
| `grok-imagine-video:official` | Official | Supports text-to-video and image-to-video |
| `grok-imagine-video-1.5:official` | Official | Image-to-video only; requires `image_url` |
| `grok-imagine-video` | Standard | Supports text-to-video and image-to-video |

## Workflows

### 1) Text-to-Video

```json
POST /grok/videos
{
  "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "resolution": "480p",
  "duration": 6
}
```

### 2) Image-to-Video

```json
POST /grok/videos
{
  "prompt": "The character slowly turns around and smiles at the camera",
  "model": "grok-imagine-video-1.5:official",
  "image_url": "https://example.com/input.jpg",
  "resolution": "720p",
  "duration": 6
}
```

### 3) Poll Task Result

```json
POST /grok/tasks
{
  "id": "your-task-id"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | For generation | string | Video prompt text |
| `model` | No | `grok-imagine-video-1.5-fast:reverse`, `grok-imagine-video:reverse`, `grok-imagine-video:official`, `grok-imagine-video-1.5:official`, `grok-imagine-video` | Video model (default: `grok-imagine-video-1.5-fast:reverse`) |
| `image_url` | Conditional | string | Input image URL for image-to-video; required for `grok-imagine-video-1.5:official` |
| `reference_image_urls` | No | array of strings | Style/content reference images |
| `aspect_ratio` | No | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3` | Output aspect ratio |
| `resolution` | No | `480p`, `720p`, `1080p` | Output resolution (default: `480p`) |
| `duration` | No | integer `1-30` | Video duration in seconds (default: `6`) |
| `callback_url` | No | string | Async callback URL |
| `async` | No | boolean | Return immediately with task id |
| `id` / `ids` (`/grok/tasks`) | No | string / array | Retrieve one or multiple tasks |
| `action` (`/grok/tasks`) | No | `retrieve`, `retrieve_batch` | Task retrieval action |

## Gotchas

- For pure text-to-video, provide `prompt`; for image-to-video, pass `image_url`.
- `grok-imagine-video-1.5:official` requires `image_url`.
- `duration` is schema-bounded to `1-30`; in practice, common stable choices are 6s or 10s.
- Use `POST /grok/tasks` to poll until `state` is terminal (for example `succeeded`).

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text prompts, guiding generation with reference images, or editing an existing video through the current Gemini video API. Supports 720p/1080p output, aspect-ratio control, async callbacks, and task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-veo for tool-use.
---

# Veo Video Generation

Generate AI videos through AceDataCloud's current Gemini video API (`/gemini/videos`).

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/gemini/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a whale breaching in slow motion at golden hour", "model": "omni-flash", "aspect_ratio": "16:9", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /gemini/tasks` with `{"id": "..."}`.
This returns a task ID immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/gemini/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Model

| Model | Best For |
|-------|----------|
| `omni-flash` | Text-to-video, image-guided video, and video editing/reference |

## Workflows

### 1. Text-to-Video

```json
POST /gemini/videos
{
  "prompt": "cinematic aerial shot of the Northern Lights over Iceland",
  "model": "omni-flash",
  "resolution": "1080p"
}
```

### 2. Image-Guided Video

Guide generation with one or more reference images.

```json
POST /gemini/videos
{
  "prompt": "the scene gently comes to life with wind and subtle motion",
  "image_urls": ["https://example.com/landscape.jpg"],
  "model": "omni-flash",
  "aspect_ratio": "16:9"
}
```

### 3. Video Editing / Reference Video

Edit or restyle an existing video by providing one source video plus at least one reference image. The API requires the image input as an additional guidance reference whenever `video_urls` is used.

```json
POST /gemini/videos
{
  "prompt": "restyle the video into cinematic anime while keeping the motion",
  "image_urls": [
    "https://example.com/reference.png"
  ],
  "video_urls": [
    "https://example.com/source.mp4"
  ],
  "model": "omni-flash",
  "resolution": "720p"
}
```

### 4. Async Without Callback

Set `async: true` to get a `task_id` immediately without configuring a callback URL.

```json
POST /gemini/videos
{
  "prompt": "a dramatic timelapse of clouds over a mountain range",
  "model": "omni-flash",
  "async": true
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Required text prompt describing the desired video |
| `model` | `"omni-flash"` | Model to use (default: `omni-flash`) |
| `aspect_ratio` | `"16:9"`, `"9:16"` | Output aspect ratio (default: `16:9`) |
| `resolution` | `"720p"`, `"1080p"` | Output resolution (default: `720p`) |
| `image_urls` | array of strings | Optional reference image URLs; required when using `video_urls` |
| `video_urls` | array of strings | Optional reference video URLs (max 1) for video editing/reference |
| `callback_url` | string | Optional webhook URL for async completion |
| `async` | `true` / `false` | Optional async mode; when `true`, the API returns a `task_id` immediately |

## Task Polling

Poll generation status and retrieve results with `POST /gemini/tasks`.

### Single Task

```json
POST /gemini/tasks
{
  "id": "b8976e18-32dc-4718-9ed8-1ea090fcb6ea"
}
```

### Batch Task Lookup

```json
POST /gemini/tasks
{
  "ids": ["task_1", "task_2"],
  "action": "retrieve_batch"
}
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | array of strings | Multiple task IDs for batch retrieval |
| `action` | `"retrieve"`, `"retrieve_batch"` | Polling mode (`retrieve` is the default) |

## Gotchas

- `prompt` is required for every generation request
- The only documented model is `omni-flash`
- `video_urls` accepts at most **one** video URL
- If you provide `video_urls`, you must also provide at least one `image_urls` entry because the API requires an image guidance reference for video-editing requests
- Use `callback_url` or `async: true` to avoid holding open a long-running request
- Task polling uses `id` or `ids` in the `/gemini/tasks` request body
- Task states use values like `"pending"`, `"succeeded"`, and `"failed"`

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

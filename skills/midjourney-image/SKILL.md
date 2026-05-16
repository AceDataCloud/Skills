---
name: midjourney-image
description: Generate, edit, blend, upscale, and describe images with Midjourney via AceDataCloud API. Use when creating AI images from text prompts, editing existing images, generating 2x2 grids, upscaling, creating variations, blending multiple images, reverse-prompting from images, or generating video from images. Supports versions 5.2 through 8.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-midjourney for tool-use.
---

# Midjourney Image Generation

Generate and manipulate AI images through AceDataCloud's Midjourney API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start — Generate an Image

```bash
curl -X POST https://api.acedata.cloud/midjourney/imagine \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a futuristic city at sunset, cyberpunk style --ar 16:9", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /midjourney/tasks` with `{"action": "retrieve", "id": "<task_id>"}`. You can also retrieve by `trace_id`, or batch-retrieve with `ids` / `trace_ids`.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/midjourney/imagine` | POST | Generate images, blend inputs, or run follow-up transform actions |
| `/midjourney/seed` | POST | Get the seed for a generated image |
| `/midjourney/edits` | POST | Edit an existing image with a prompt and optional mask |
| `/midjourney/videos` | POST | Generate or extend a video from an image/video |
| `/midjourney/describe` | POST | Reverse-prompt an image |
| `/midjourney/shorten` | POST | Analyze and shorten a prompt |
| `/midjourney/translate` | POST | Translate a prompt into English |
| `/midjourney/tasks` | POST | Retrieve one or more tasks |

## Generation Modes

| Mode | Speed | Cost | Best For |
|------|-------|------|----------|
| `fast` | Fast | Standard | Most tasks (default) |
| `relax` | Slow | Cheaper | Batch generation |
| `turbo` | Fastest | Premium | Time-sensitive work |

## Midjourney Versions

| Version | Notes |
|---------|-------|
| `8.1` | Latest, recommended |
| `8` | V8 billing/version controls |
| `7` | Great quality, fast |
| `6.1` | Stable, well-tested |
| `6` | Previous generation |
| `5.2` | Legacy |

## Core Workflows

### 1. Generate Images (Imagine)

```json
POST /midjourney/imagine
{
  "prompt": "a serene mountain lake at dawn, photorealistic --ar 16:9 --v 7",
  "mode": "fast",
  "translation": true,
  "split_images": true
}
```

Set `translation: true` to auto-translate non-English prompts. Set `split_images: true` to return individual crops alongside the 2x2 grid.

### 2. Upscale / vary / pan / zoom

```json
POST /midjourney/imagine
{
  "action": "upscale1",
  "image_id": "grid-image-id"
}
```

Common action values include:

- `upscale1`–`upscale4`
- `variation1`–`variation4`
- `variation_subtle`, `variation_strong`
- `reroll`
- `zoom_out_2x`, `zoom_out_1_5x`
- `pan_left`, `pan_right`, `pan_up`, `pan_down`
- `blend`

### 3. Edit an image

```json
POST /midjourney/edits
{
  "image_url": "https://example.com/photo.jpg",
  "prompt": "add a rainbow in the sky",
  "mode": "fast",
  "split_images": true
}
```

### 4. Describe, shorten, and translate prompts

```json
POST /midjourney/describe
{"image_url": "https://example.com/photo.jpg"}
```

```json
POST /midjourney/shorten
{"prompt": "very long prompt text here"}
```

```json
POST /midjourney/translate
{"content": "将这个提示词翻译成英文"}
```

### 5. Generate or extend video

```json
POST /midjourney/videos
{
  "action": "generate",
  "image_url": "https://example.com/photo.jpg",
  "prompt": "the city comes alive with moving traffic",
  "resolution": "720p"
}
```

```json
POST /midjourney/videos
{
  "action": "extend",
  "video_id": "existing-video-id",
  "video_index": 0,
  "prompt": "continue the motion for a few more seconds"
}
```

### 6. Poll tasks

```json
POST /midjourney/tasks
{
  "action": "retrieve",
  "id": "task-id"
}
```

Batch retrieval:

```json
POST /midjourney/tasks
{
  "action": "retrieve_batch",
  "ids": ["task-1", "task-2"]
}
```

You can also substitute `trace_id` / `trace_ids`.

## Prompt Parameters

Append these to the prompt string:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `--ar` | `--ar 16:9` | Aspect ratio |
| `--v` | `--v 7` | Midjourney version |
| `--q` | `--q 2` | Quality (`0.25`, `0.5`, `1`, `2`) |
| `--s` | `--s 750` | Stylization (`0–1000`) |
| `--c` | `--c 50` | Chaos (`0–100`) |
| `--no` | `--no text, watermark` | Negative prompt |
| `--seed` | `--seed 12345` | Reproducible generation |

## API-Level Parameters (Billing Impact)

These top-level `POST /midjourney/imagine` fields affect billing and are separate from inline prompt parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `version` | string | Version used for billing calculation (`8.1`, `8`, `7`, `6.1`, etc.) |
| `hd` | boolean | Enable HD image generation (V8/V8.1 only) |
| `quality` | string | Quality level: `.25`, `.5`, `1`, `2`, `4` |
| `style_reference` | boolean | Whether the prompt uses `--sref` |
| `moodboard` | boolean | Whether the prompt uses moodboard references |

## Other Request Parameters

### `POST /midjourney/imagine`

`mask`, `mode`, `action`, `prompt`, `timeout`, `image_id`, `translation`, `callback_url`, `split_images`, `version`, `hd`, `quality`, `style_reference`, `moodboard`

### `POST /midjourney/edits`

`mask`, `mode`, `action`, `prompt`, `image_url`, `callback_url`, `split_images`

### `POST /midjourney/videos`

`action`, `mode`, `resolution`, `prompt`, `video_id`, `video_index`, `loop`, `image_url`, `end_image_url`, `callback_url`

### `POST /midjourney/tasks`

`action`, `id`, `trace_id`, `ids`, `trace_ids`, `offset`, `limit`

## Gotchas

- Imagine returns a **2x2 grid** by default — use follow-up actions to work on individual results
- Prompt parameters (`--ar`, `--v`, etc.) go **inside the prompt string**, not as separate JSON fields
- `translation: true` auto-translates non-English prompts before sending them to Midjourney
- Prompt utility endpoints are separate: use `/midjourney/shorten` to compress prompts and `/midjourney/translate` to translate them
- Video generation requires `image_url` for `action: "generate"`; video extension requires `video_id` and `video_index`
- `/midjourney/tasks` polling uses `id` / `ids` (or `trace_id` / `trace_ids`), not `task_id`
- Use `POST /midjourney/seed` with an image ID when you need reproducible seed data

> **MCP:** `pip install mcp-midjourney` | Hosted: `https://midjourney.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

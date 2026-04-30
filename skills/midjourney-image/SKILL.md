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

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /midjourney/tasks` with `{"action": "retrieve", "id": "..."}` or `{"action": "retrieve", "trace_id": "..."}`. Use `retrieve_batch` with `ids`/`trace_ids` arrays plus optional `offset`/`limit` for pagination.

## Generation Modes

| Mode | Speed | Cost | Best For |
|------|-------|------|----------|
| `fast` | Fast | Standard | Most tasks (default) |
| `relax` | Slow | Cheaper | Batch generation |
| `turbo` | Fastest | Premium | Time-sensitive work |

## Midjourney Versions

| Version | Notes |
|---------|-------|
| `8` | Latest, best quality |
| `7` | Great quality, fast |
| `6.1` | Stable, well-tested |
| `6` | Previous generation |
| `5.2` | Legacy |

## Core Workflows

### 1. Generate Images (Imagine)

Creates a 2x2 grid of 4 image variations.

```json
POST /midjourney/imagine
{
  "prompt": "a serene mountain lake at dawn, photorealistic --ar 16:9 --v 7",
  "mode": "fast",
  "translation": true,
  "split_images": true
}
```

Set `translation: true` to auto-translate non-English prompts. Set `split_images: true` to get individual images besides the grid.

### 2. Upscale / Vary / Pan / Zoom

After generating a grid, use transform actions on individual images:

```json
POST /midjourney/imagine
{
  "action": "upscale1",
  "image_id": "grid-image-id"
}
```

**Available actions:**
- `upscale1`–`upscale4`: Upscale individual quadrant
- `variation1`–`variation4`: Create variation of a quadrant
- `variation_subtle` / `variation_strong`: Subtle/strong variation of full image
- `reroll`: Re-generate with same prompt
- `zoom_out_2x` / `zoom_out_1_5x`: Zoom out
- `pan_left` / `pan_right` / `pan_up` / `pan_down`: Extend canvas

### 3. Edit an Image

Modify an existing image using a text prompt, optionally with a mask.

```json
POST /midjourney/edits
{
  "image_url": "https://example.com/photo.jpg",
  "prompt": "add a rainbow in the sky",
  "mode": "fast"
}
```

### 4. Blend Images

Combine 2–5 images into a new composition.

```json
POST /midjourney/imagine
{
  "action": "blend",
  "image_urls": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ]
}
```

### 5. Describe an Image (Reverse Prompt)

Get AI-generated text descriptions of an image (returns 4 options).

```json
POST /midjourney/describe
{"image_url": "https://example.com/photo.jpg"}
```

### 6. Generate Video

Create a video from a text prompt (with an optional reference image), or extend an existing video.

```json
POST /midjourney/videos
{
  "image_url": "https://example.com/photo.jpg",
  "prompt": "the city comes alive with moving traffic",
  "resolution": "720p"
}
```

**Extend an existing video:**

```json
POST /midjourney/videos
{
  "action": "extend",
  "video_id": "existing-video-id",
  "video_index": 0,
  "mode": "fast"
}
```

## Prompt Parameters

Append these to your prompt text:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `--ar` | `--ar 16:9` | Aspect ratio |
| `--v` | `--v 7` | Midjourney version |
| `--q` | `--q 2` | Quality (0.25, 0.5, 1, 2) |
| `--s` | `--s 750` | Stylization (0–1000) |
| `--c` | `--c 50` | Chaos/variety (0–100) |
| `--no` | `--no text, watermark` | Negative prompt |
| `--seed` | `--seed 12345` | Reproducible generation |

## API-Level Parameters (Billing Impact)

These top-level fields on `POST /midjourney/imagine` affect billing and are separate from inline prompt parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `version` | string | Midjourney version (`"8"`, `"7"`, `"6.1"`, etc.) — used for billing calculation |
| `hd` | boolean | Enable HD 2K resolution (V8 only) — costs 4× GPU time |
| `quality` | string | Quality level: `".25"`, `".5"`, `"1"`, `"2"`, `"4"` — quality `"4"` is V8 only and costs 16× GPU time |
| `style_reference` | boolean | Whether prompt uses `--sref` style references (V8: costs 4× GPU time) |
| `moodboard` | boolean | Whether prompt uses moodboard image references (V8: costs 4× GPU time) |

## Video Parameters

`POST /midjourney/videos` fields:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"generate"`, `"extend"` | Operation type |
| `mode` | `"fast"`, `"turbo"` | Speed mode (default: fast) |
| `resolution` | `"480p"`, `"720p"` | Output resolution (default: 720p) |
| `prompt` | string | Text description for generation |
| `image_url` | string | First-frame reference image URL |
| `end_image_url` | string | Image to use as the last frame |
| `loop` | boolean | Generate a looping video (default: false) |
| `video_id` | string | Video ID to extend (required for `extend`) |
| `video_index` | number | Index (0-based) of video to extend |
| `callback_url` | string | Async callback URL |



- Imagine returns a **2x2 grid** — use upscale/variation actions to work with individual images
- Use `split_images: true` to also receive individual cropped images alongside the grid
- Prompt parameters (`--ar`, `--v`, etc.) go **inside the prompt string**, not as separate fields
- `translation: true` auto-translates Chinese/other languages to English before sending to Midjourney
- Video generation supports both text-only (`prompt`) and image-first (`image_url`) modes; `image_url` is optional
- Available transform actions depend on the image — check `available_actions` in the response
- Get the seed with `POST /midjourney/seed` using the image_id for reproducible results

> **MCP:** `pip install mcp-midjourney` | Hosted: `https://midjourney.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

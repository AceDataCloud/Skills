---
name: kickart-video
description: Generate e-commerce marketing videos with Kickart (ByteDance 即创) via AceDataCloud API. Use when creating product introduction videos, main-image videos from product links or user images, viral reference-driven videos, or template-based videos. Supports fast/pro modes, multiple languages, and async task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Kickart E-Commerce Video Generation

Generate AI-powered e-commerce marketing videos through AceDataCloud's Kickart (ByteDance 即创) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/kickart/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "fast",
    "type": "intro",
    "product_url": "https://www.tiktok.com/view/product/172839182",
    "duration": 15,
    "language": "en",
    "aspect_ratio": "9:16",
    "async": true
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /kickart/tasks` with `{"action": "retrieve", "id": "..."}`.

## Endpoints

### 1. Product Video (`POST /kickart/videos`)

Generate an intro or main-image marketing video from a product source.

```json
POST /kickart/videos
{
  "mode": "fast",
  "type": "intro",
  "product_url": "https://example.com/product/123",
  "duration": 30,
  "aspect_ratio": "9:16",
  "language": "en",
  "prompt": "Highlight the premium quality and minimal design",
  "nle_subtitle_enabled": true,
  "async": true
}
```

At least one product source is required: `product_url`, `product_id`, `user_images`, or `user_videos`.

### 2. Viral Video (`POST /kickart/viral-videos`)

Create a viral-style video by referencing an existing video. Useful for content repurposing.

```json
POST /kickart/viral-videos
{
  "mode": "pro",
  "ref_video": "https://example.com/reference-video.mp4",
  "language": "en",
  "product_url": "https://example.com/product/123",
  "similarity": "medium",
  "async": true
}
```

### 3. Template Video (`POST /kickart/template-videos`)

Generate a video using a specific Kickart template with a resource list.

```json
POST /kickart/template-videos
{
  "template_id": "your-template-id",
  "resource_list": [
    {"url": "https://example.com/image1.jpg", "type": "image"},
    {"url": "https://example.com/video1.mp4", "type": "video"}
  ],
  "async": true
}
```

## Parameters

### `/kickart/videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `duration` | `15`, `30`, `45`, `60` | Video duration in seconds (**required**). `type=main` only supports 15/30 |
| `mode` | `"fast"`, `"pro"` | Generation mode (default: `fast`). `pro` is slower but higher quality |
| `type` | `"intro"`, `"main"` | Video type: product intro or main-image video (default: `intro`) |
| `product_url` | URL | Product page link (TikTok Shop / Douyin Store) |
| `product_id` | string | Product ID from the platform |
| `user_images` | array of URLs | User-supplied product images |
| `user_videos` | array of URLs | User-supplied product video clips |
| `aspect_ratio` | `"9:16"`, `"16:9"`, `"3:4"`, `"4:3"`, `"1:1"` | Output aspect ratio (default: `9:16`) |
| `language` | `"zh"`, `"en"`, `"en-us"`, `"pt-br"`, `"ja"`, `"es-mx"`, `"id"`, `"ms"`, `"tl"` | Voiceover/subtitle language (default: `zh`) |
| `purpose` | string | Marketing sub-type (e.g. product recommendation, brand ad, review) |
| `prompt` | string | Creative instructions for the video content and style |
| `nle_subtitle_enabled` | boolean | Add hardcoded subtitles (default: `true`) |
| `use_subtitle_erasure` | boolean | Erase existing subtitles during rendering |
| `watermark` | boolean | Add "AI Generated" watermark (default: `false`) |
| `template_id` | string | Override mode/type with a specific template ID |
| `callback_url` | URL | Webhook for result delivery |
| `async` | boolean | Return task ID immediately for polling |

### `/kickart/viral-videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `ref_video` | URL | Reference video to derive style from (**required**) |
| `language` | string | Output language (**required**) |
| `mode` | `"pro"`, `"advanced"` | Generation mode (default: `pro`) |
| `product_url` | URL | Product source URL |
| `product_id` | string | Product source ID |
| `product_images` | array of URLs | Product image references |
| `model_images` | array of URLs | Model/person images |
| `location_images` | array of URLs | Scene/location image references |
| `similarity` | `"high"`, `"medium"` | Similarity to reference video (default: `medium`) |
| `ai_product_analysis` | boolean | Auto-analyse product from URL/images (default: `true`) |
| `nle_subtitle_enabled` | boolean | Add subtitles (default: `true`) |
| `prompt` | string | Additional creative instructions |
| `callback_url` | URL | Webhook for result delivery |
| `async` | boolean | Return task ID immediately for polling |

### `/kickart/template-videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `template_id` | string | Kickart template ID (**required**) |
| `resource_list` | array | Resource items for the template (**required**) |
| `resolution` | string | Output resolution |
| `watermark` | boolean | Add watermark |
| `callback_url` | URL | Webhook for result delivery |
| `async` | boolean | Return task ID immediately for polling |

## Task Queries

```json
POST /kickart/tasks
{"action": "retrieve", "id": "<task_id>"}
```

The completed response includes `data.video_url` with the generated video URL.

## Gotchas

- At least one product source is required for `/kickart/videos`: `product_url`, `product_id`, `user_images`, or `user_videos`
- `duration` is **required** for `/kickart/videos`; valid values are `15`, `30`, `45`, `60`. The `main` type only supports `15` or `30`
- Video generation (especially `pro` mode) can take minutes to tens of minutes — always use `async: true` or `callback_url`
- `language` affects voiceover and subtitle text, not the product description
- `/kickart/viral-videos` requires both `ref_video` and `language`
- `/kickart/template-videos` requires both `template_id` and `resource_list`

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

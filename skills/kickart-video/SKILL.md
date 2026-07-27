---
name: kickart-video
description: Generate AI e-commerce videos with Kickart via AceDataCloud API. Use when creating product showcase videos from duration and product source (URL, ID, or images/videos), viral-style marketing videos from a reference video, or template-based videos. Supports fast/pro quality modes, multiple aspect ratios, subtitle control, and asynchronous task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Kickart E-Commerce Video Generation

Generate AI-powered e-commerce product videos through AceDataCloud's Kickart API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/kickart/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"duration": 15, "product_url": "https://www.tiktok.com/view/product/172839182", "mode": "fast", "aspect_ratio": "9:16", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /kickart/tasks` with `{"id": "..."}`.

## Workflows

### 1. Product Video from URL

Generate a product showcase video using a product page URL.

```json
POST /kickart/videos
{
  "duration": 30,
  "product_url": "https://www.tiktok.com/view/product/172839182",
  "mode": "pro",
  "aspect_ratio": "9:16",
  "language": "en",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 2. Product Video from Images

Generate a video using your own product images and videos.

```json
POST /kickart/videos
{
  "duration": 15,
  "user_images": [
    "https://cdn.acedata.cloud/product-image-1.jpg",
    "https://cdn.acedata.cloud/product-image-2.jpg"
  ],
  "mode": "fast",
  "aspect_ratio": "16:9",
  "prompt": "Showcase the sleek design and key features of the product",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 3. Viral-Style Video from Reference

Clone the style of a reference video and apply it to your product.

```json
POST /kickart/viral-videos
{
  "ref_video": "https://static.bytednsdoc.com/obj/example/demo_video.mp4",
  "product_url": "https://www.tiktok.com/view/product/172839182",
  "language": "zh",
  "mode": "pro",
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 4. Template-Based Video

Generate a video using a pre-defined template with your product resources.

```json
POST /kickart/template-videos
{
  "template_id": "1690784258",
  "resource_list": [
    "https://cdn.acedata.cloud/kickart/input.jpg"
  ],
  "resolution": "1080p",
  "callback_url": "https://api.acedata.cloud/health"
}
```

## Parameters

### POST /kickart/videos

| Parameter | Type | Required | Values / Notes |
|-----------|------|----------|----------------|
| `duration` | integer | ✓ | `15`, `30`, `45`, `60` (seconds) |
| `mode` | string | | `fast` (default), `pro` — quality vs. speed |
| `type` | string | | `intro`, `main` — video section type |
| `product_url` | string (URI) | * | Product page URL |
| `product_id` | string | * | Product ID |
| `user_images` | array of URIs | * | User-supplied product images |
| `user_videos` | array of URIs | * | User-supplied product videos |
| `template_id` | string | | Pre-defined template to apply |
| `aspect_ratio` | string | | `9:16`, `16:9`, `3:4`, `4:3`, `1:1` |
| `language` | string | | Output language (e.g. `zh`, `en`, `ja`, `pt-br`) |
| `purpose` | string | | Use-case or purpose hint for the video |
| `prompt` | string | | Additional creative guidance |
| `nle_subtitle_enabled` | boolean | | Enable auto subtitles (default `true`) |
| `use_subtitle_erasure` | boolean | | Erase existing subtitles from source (default `false`) |
| `watermark` | boolean | | Add watermark (default `false`) |
| `callback_url` | string (URI) | | Webhook URL for async result delivery |
| `async` | boolean | | `true` to return task ID immediately |

\* At least one product source (`product_url`, `product_id`, `user_images`, or `user_videos`) is recommended to get meaningful output.

### POST /kickart/viral-videos

| Parameter | Type | Required | Values / Notes |
|-----------|------|----------|----------------|
| `ref_video` | string (URI) | ✓ | Reference video to clone style from |
| `language` | string | ✓ | `zh`, `en`, `en-us`, `pt-br`, `ja`, `es-mx`, `id`, `ms`, `tl` |
| `mode` | string | | `pro` (default), `advanced` |
| `template_id` | string | | Specific template to use |
| `product_url` | string (URI) | | Product page URL |
| `product_id` | string | | Product ID |
| `product_images` | array of URIs | | Product images |
| `model_images` | array of URIs | | Model/person images |
| `ai_product_analysis` | boolean | | AI-analyze product (default `true`) |
| `similarity` | string | | `medium` (default), `high` — style adherence to reference |
| `nle_subtitle_enabled` | boolean | | Enable auto subtitles (default `true`) |
| `use_subtitle_erasure` | boolean | | Erase source subtitles (default `false`) |
| `prompt` | string | | Creative guidance |
| `location_images` | array of URIs | | Scene/location images |
| `watermark` | boolean | | Add watermark (default `false`) |
| `callback_url` | string (URI) | | Webhook URL for async result delivery |
| `async` | boolean | | `true` to return task ID immediately |

### POST /kickart/template-videos

| Parameter | Type | Required | Values / Notes |
|-----------|------|----------|----------------|
| `template_id` | string | ✓ | Template identifier |
| `resource_list` | array of strings | ✓ | Resource URLs/IDs to fill template slots |
| `resolution` | string | | Output resolution (e.g. `1080p`) |
| `watermark` | boolean | | Add watermark |
| `callback_url` | string (URI) | | Webhook URL for async result delivery |
| `async` | boolean | | `true` to return task ID immediately |

## Task Polling

Retrieve one task:

```json
POST /kickart/tasks
{"id": "<task_id>"}
```

Retrieve several tasks:

```json
POST /kickart/tasks
{"action": "retrieve_batch", "ids": ["<task_id_1>", "<task_id_2>"]}
```

A completed response contains `data.video_url` with the generated video.

## Gotchas

- `duration` is required for `/kickart/videos`; allowed values are `15`, `30`, `45`, and `60` seconds
- `ref_video` and `language` are both required for `/kickart/viral-videos`
- `template_id` and `resource_list` are both required for `/kickart/template-videos`
- Language codes are locale strings (`zh`, `en`, `en-us`, `pt-br`, `ja`, `es-mx`, `id`, `ms`, `tl`); plain `en` and locale `en-us` are both valid
- Use `callback_url` to avoid long-running synchronous connections that time out during video rendering
- `similarity: "high"` makes the viral video closely match the reference style; `"medium"` (default) allows more creative freedom

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

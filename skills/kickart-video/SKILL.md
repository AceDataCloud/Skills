---
name: kickart-video
description: Generate AI product and viral marketing videos with Kickart via AceDataCloud API. Use when creating product showcase videos, viral social media videos from a reference clip, or template-based videos. Supports configurable duration, aspect ratio, language, and subtitle options.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Kickart Video Generation

Generate AI-powered product and marketing videos through AceDataCloud's Kickart API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/kickart/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"duration": 15, "product_url": "https://example.com/product", "aspect_ratio": "9:16", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /kickart/tasks` with `{"id": "..."}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /kickart/videos` | Product showcase video from images/videos |
| `POST /kickart/viral-videos` | Viral-style video from a reference clip |
| `POST /kickart/template-videos` | Video from a predefined template |
| `POST /kickart/tasks` | Poll async task status |

## Workflows

### 1. Product Video

Create a product showcase video. Provide at least one product source (`product_url`, `product_id`, `user_images`, or `user_videos`).

```json
POST /kickart/videos
{
  "duration": 30,
  "mode": "pro",
  "product_url": "https://example.com/product-page",
  "aspect_ratio": "9:16",
  "language": "en",
  "nle_subtitle_enabled": true
}
```

Parameters:

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `duration` | **Yes** | `15`, `30`, `45`, `60` | Video duration in seconds |
| `mode` | No | `"fast"`, `"pro"` | Generation speed/quality trade-off |
| `type` | No | `"intro"`, `"main"` | Video segment type |
| `template_id` | No | string | Use a specific template |
| `product_url` | No* | string | Product page URL (at least one product source required) |
| `product_id` | No* | string | Product ID |
| `user_images` | No* | array | Product image URLs |
| `user_videos` | No* | array | Product video URLs |
| `aspect_ratio` | No | `"9:16"`, `"16:9"`, `"3:4"`, `"4:3"`, `"1:1"` | Output aspect ratio |
| `language` | No | `"zh"`, `"en"`, `"en-us"`, `"pt-br"`, `"ja"`, `"es-mx"`, `"id"`, `"ms"`, `"tl"` | Subtitle/narration language |
| `prompt` | No | string | Additional description or instructions |
| `purpose` | No | string | Campaign purpose or context |
| `nle_subtitle_enabled` | No | boolean | Enable subtitles |
| `use_subtitle_erasure` | No | boolean | Remove existing subtitles from source |
| `watermark` | No | boolean | Add watermark |
| `callback_url` | No | string | Async callback URL |
| `async` | No | boolean | Return task ID immediately |

### 2. Viral Video

Create a viral-style video based on a reference clip. The reference video defines the format and style.

```json
POST /kickart/viral-videos
{
  "ref_video": "https://example.com/reference-clip.mp4",
  "language": "en",
  "mode": "pro",
  "product_url": "https://example.com/product",
  "similarity": "high"
}
```

Parameters:

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `ref_video` | **Yes** | string | Reference video URL |
| `language` | **Yes** | `"zh"`, `"en"`, `"en-us"`, `"pt-br"`, `"ja"`, `"es-mx"`, `"id"`, `"ms"`, `"tl"` | Output language |
| `mode` | No | `"pro"`, `"advanced"` | Generation mode |
| `template_id` | No | string | Specific template ID |
| `product_url` | No | string | Product page URL |
| `product_id` | No | string | Product ID |
| `product_images` | No | array | Product image URLs |
| `model_images` | No | array | Model/character image URLs |
| `location_images` | No | array | Background/location images |
| `ai_product_analysis` | No | boolean | AI-based product analysis |
| `similarity` | No | `"high"`, `"medium"` | Similarity to reference video |
| `nle_subtitle_enabled` | No | boolean | Enable subtitles |
| `use_subtitle_erasure` | No | boolean | Remove existing subtitles |
| `prompt` | No | string | Additional instructions |
| `watermark` | No | boolean | Add watermark |
| `callback_url` | No | string | Async callback URL |
| `async` | No | boolean | Return task ID immediately |

### 3. Template Video

Generate a video using a predefined template with a resource list.

```json
POST /kickart/template-videos
{
  "template_id": "tpl_12345",
  "resource_list": [
    {"type": "image", "url": "https://example.com/image.jpg"},
    {"type": "text", "content": "Our amazing product"}
  ]
}
```

Parameters:

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `template_id` | **Yes** | string | Template identifier |
| `resource_list` | **Yes** | array | Resources to populate the template |
| `resolution` | No | string | Output resolution |
| `watermark` | No | boolean | Add watermark |
| `callback_url` | No | string | Async callback URL |
| `async` | No | boolean | Return task ID immediately |

## Task Polling

```json
POST /kickart/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
}
```

## Gotchas

- `POST /kickart/videos` requires `duration` plus at least one product source (`product_url`, `product_id`, `user_images`, or `user_videos`)
- `POST /kickart/viral-videos` requires both `ref_video` and `language`
- `POST /kickart/template-videos` requires both `template_id` and `resource_list`
- All generation is **async** — always set `callback_url` or `async: true` and poll `/kickart/tasks`

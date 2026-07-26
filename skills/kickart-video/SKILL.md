---
name: kickart-video
description: Generate AI e-commerce marketing videos with Kickart (即创) via AceDataCloud API. Use when creating product intro/main videos from a product URL or media assets, producing viral-style videos from a reference clip, or rendering a video from a specific Kickart template. Supports multiple languages, aspect ratios, subtitle control, and asynchronous task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Kickart E-commerce Video Generation

Use Kickart (即创) through AceDataCloud to generate e-commerce marketing videos from product links,
user media, reference clips, or pre-built templates.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Choose an Endpoint

| Goal | Endpoint | Required inputs |
|---|---|---|
| Generate a product intro or main video | `POST /kickart/videos` | `duration`; at least one of `product_url`, `product_id`, `user_images`, or `user_videos` |
| Produce a viral-style video from a reference clip | `POST /kickart/viral-videos` | `ref_video`, `language` |
| Render a video using a specific template | `POST /kickart/template-videos` | `template_id`, `resource_list` |

## Quick Start

Submit a product intro video asynchronously:

```bash
curl -X POST https://api.acedata.cloud/kickart/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "fast",
    "type": "intro",
    "product_url": "https://www.tiktok.com/view/product/172839182",
    "duration": 15,
    "language": "zh",
    "aspect_ratio": "9:16",
    "async": true
  }'
```

The response contains a `task_id`. Poll after 15–60 seconds:

```bash
curl -X POST https://api.acedata.cloud/kickart/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve", "id": "<task_id>"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Pro-mode videos can take several
> minutes; always use `async: true` or `callback_url` to avoid HTTP timeouts.

## Workflows

### Product Videos (`POST /kickart/videos`)

Generate a product-intro or product-main video from a product link or your own images/videos.
`mode` + `type` selects the template tier; pass `template_id` to override.

```json
POST /kickart/videos
{
  "mode": "fast",
  "type": "intro",
  "product_url": "https://www.tiktok.com/view/product/172839182",
  "duration": 15,
  "language": "zh",
  "aspect_ratio": "9:16"
}
```

### Viral Videos (`POST /kickart/viral-videos`)

Replicate the style of a reference video and apply it to your product.

```json
POST /kickart/viral-videos
{
  "mode": "pro",
  "ref_video": "https://static.bytednsdoc.com/obj/example/demo_video.mp4",
  "product_url": "https://www.tiktok.com/view/product/172839182",
  "language": "zh"
}
```

### Template Videos (`POST /kickart/template-videos`)

Render a video using a specific Kickart template ID with your own resource images.

```json
POST /kickart/template-videos
{
  "template_id": "1690784258",
  "resource_list": [
    "https://cdn.acedata.cloud/kickart/input.jpg"
  ],
  "resolution": "1080p"
}
```

## Parameters

### `POST /kickart/videos`

| Parameter | Type | Required | Values / Notes |
|---|---|---|---|
| `duration` | integer | **Yes** | `15`, `30`, `45`, `60` (seconds) |
| `mode` | string | No | `fast` (default), `pro` |
| `type` | string | No | `intro` (default), `main` |
| `template_id` | string | No | Override `mode`/`type` with a specific template ID |
| `product_url` | string | No | TikTok/Douyin product URL |
| `product_id` | string | No | TikTok/Douyin product ID |
| `user_images` | string[] | No | User-supplied image URLs |
| `user_videos` | string[] | No | User-supplied video URLs |
| `aspect_ratio` | string | No | `9:16` (default), `16:9`, `3:4`, `4:3`, `1:1` |
| `language` | string | No | `zh` (default), `en`, `en-us`, `pt-br`, `ja`, `es-mx`, `id`, `ms`, `tl` |
| `purpose` | string | No | Fine-grained video purpose (e.g. product review, brand ad) |
| `prompt` | string | No | Creative instruction for style and key selling points |
| `nle_subtitle_enabled` | boolean | No | Add hard subtitles; default `true` |
| `use_subtitle_erasure` | boolean | No | Erase source subtitles during rendering; default `false` |
| `watermark` | boolean | No | Add AI-generated watermark; default `false` |
| `callback_url` | URL | No | Webhook; forces async and returns `task_id` immediately |
| `async` | boolean | No | Return `task_id` immediately and poll via `/kickart/tasks` |

### `POST /kickart/viral-videos`

| Parameter | Type | Required | Values / Notes |
|---|---|---|---|
| `ref_video` | string | **Yes** | URL of the reference video to replicate style from |
| `language` | string | **Yes** | `zh`, `en`, `en-us`, `pt-br`, `ja`, `es-mx`, `id`, `ms`, `tl` |
| `mode` | string | No | `pro` (default) — standard viral generation; `advanced` — higher quality with more AI analysis |
| `template_id` | string | No | Override mode with a specific template ID |
| `product_url` | string | No | TikTok/Douyin product URL |
| `product_id` | string | No | TikTok/Douyin product ID |
| `product_images` | string[] | No | Product image URLs |
| `model_images` | string[] | No | Model/person image URLs |
| `location_images` | string[] | No | Location/background image URLs |
| `ai_product_analysis` | boolean | No | Enable AI product analysis; default `true` |
| `similarity` | string | No | `medium` (default), `high` |
| `nle_subtitle_enabled` | boolean | No | Add hard subtitles; default `true` |
| `use_subtitle_erasure` | boolean | No | Erase source subtitles; default `false` |
| `prompt` | string | No | Additional creative instructions |
| `watermark` | boolean | No | Default `false` |
| `callback_url` | URL | No | Webhook for async delivery |
| `async` | boolean | No | Return `task_id` immediately |

### `POST /kickart/template-videos`

| Parameter | Type | Required | Values / Notes |
|---|---|---|---|
| `template_id` | string | **Yes** | Kickart template ID |
| `resource_list` | string[] | **Yes** | List of resource image URLs for the template |
| `resolution` | string | No | Output resolution (e.g. `1080p`) |
| `watermark` | boolean | No | Default `false` |
| `callback_url` | URL | No | Webhook for async delivery |
| `async` | boolean | No | Return `task_id` immediately |

## Response

All endpoints return:

```json
{
  "success": true,
  "task_id": "0c0b4d3a-2f1e-4a6b-9c2d-2b3c4d5e6f70",
  "trace_id": "a9063166-26ed-4451-85b5-54e896817c69",
  "data": {
    "task_id": "0c0b4d3a-2f1e-4a6b-9c2d-2b3c4d5e6f70",
    "video_url": "https://cdn.acedata.cloud/kickart/example.mp4",
    "usage": 0.21
  }
}
```

The finished video URL is at `data.video_url`.

## Task Queries

Retrieve one task:

```json
POST /kickart/tasks
{"action": "retrieve", "id": "<task_id>"}
```

Retrieve several tasks:

```json
POST /kickart/tasks
{"action": "retrieve_batch", "ids": ["<task_id_1>", "<task_id_2>"]}
```

## Gotchas

- At least one of `product_url`, `product_id`, `user_images`, or `user_videos` should be supplied for `/kickart/videos`; supplying none may result in a generic video
- `duration` for `/kickart/videos` must be one of `15`, `30`, `45`, `60`; not all durations are available for every `type`
- Pro-mode (`mode: "pro"`) generation can take several minutes; always use `async: true` or `callback_url`
- `ref_video` and `language` are both required for `/kickart/viral-videos`
- `template_id` and `resource_list` are both required for `/kickart/template-videos`
- Pricing is determined by `mode`+`type` (or `template_id`) and `duration`; failed generations are not billed
- By submitting content, you confirm you have rights to the materials and that any human likeness is an authorized virtual avatar

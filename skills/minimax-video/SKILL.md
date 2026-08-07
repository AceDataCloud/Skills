---
name: minimax-video
description: Generate MiniMax H3 videos from text, images, videos, or audio through AceDataCloud. Use for multimodal video generation and MiniMax H3 task management.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Generate 4–15 second videos with `POST https://api.acedata.cloud/minimax/videos`.

> **Setup:** See [authentication](../_shared/authentication.md).

## Generate a video

The request must include `model`, `content`, `resolution`, and `duration`.

| Parameter | Values |
| --- | --- |
| `model` | Required. `MiniMax-H3` |
| `content` | Required. One or more text or media content items |
| `resolution` | Required. `768P` or `2K` |
| `duration` | Required integer, 4–15 seconds |
| `ratio` | Optional: `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, or `9:16` |
| `callback_url` | Optional public URI for completion callbacks |
| `aigc_watermark` | Optional boolean; defaults to `false` |

Each `content` item has a required `type`: `text`, `image_url`, `video_url`, or `audio_url`. Media items use an object such as `"image_url": {"url": "https://example.com/image.png"}` and may set `role` to `first_frame`, `last_frame`, `reference_image`, `reference_video`, or `reference_audio`.

```bash
curl -X POST https://api.acedata.cloud/minimax/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-H3",
    "content": [
      {
        "type": "text",
        "text": "A red fox running through a snowy forest at dawn, cinematic tracking shot"
      },
      {
        "type": "image_url",
        "image_url": {"url": "https://example.com/fox.png"},
        "role": "first_frame"
      }
    ],
    "resolution": "2K",
    "duration": 5,
    "ratio": "adaptive"
  }'
```

Text items support up to 7,000 characters. The successful response contains a `task_id`.

## Manage tasks

Use `POST https://api.acedata.cloud/minimax/tasks` to retrieve, list, or delete generation tasks.

| Action | Parameters | Result |
| --- | --- | --- |
| `retrieve` (default) | `id` | A `task` object |
| `retrieve_batch` | optional `ids`, `limit`, `offset`, `created_at_min`, `created_at_max` | `items` and `total` |
| `delete` | `id` | `id` and `deleted` |

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

A task contains its `id`, `model`, `status`, `task_type`, and `modality`, and may include `error`, timestamps, output `content.url`, `resolution`, `duration`, `usage`, and `ratio`. Possible statuses are `queued`, `running`, `succeeded`, `failed`, and `cancelled`.

## Gotchas

- Use the exact model name `MiniMax-H3`.
- A media item must provide its URL in the matching object (`image_url`, `video_url`, or `audio_url`).
- Do not send legacy `prompt`, `image_urls`, `audio_urls`, or `async` fields; express all inputs in `content`.
- A `callback_url` receives the completion callback when supplied.

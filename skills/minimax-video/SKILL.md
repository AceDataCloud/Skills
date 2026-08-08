---
name: minimax-video
description: Generate MiniMax H3 videos from structured text, image, video, and audio content through AceDataCloud. Use for text-to-video, first/last-frame image video, reference media, and MiniMax H3 task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Generate 4–15 second videos through `POST https://api.acedata.cloud/minimax/videos`.

> **Setup:** See [authentication](../_shared/authentication.md). For long jobs, use [async task polling](../_shared/async-tasks.md) with `POST /minimax/tasks`.

## Contract

| Parameter | Values | Default |
| --- | --- | --- |
| `model` | `MiniMax-H3` | required |
| `content` | array of text/media items, min 1 item | required |
| `content[].type` | `text`, `image_url`, `video_url`, `audio_url` | required |
| `content[].text` | string, max 7000 chars | for text items |
| `content[].image_url.url` | public HTTP(S) image URL | for image items |
| `content[].video_url.url` | public HTTP(S) video URL | for video items |
| `content[].audio_url.url` | public HTTP(S) audio URL | for audio items |
| `content[].role` | `first_frame`, `last_frame`, `reference_image`, `reference_video`, `reference_audio` | optional |
| `resolution` | `768P`, `2K` | required |
| `duration` | integer 4–15 | required |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `aigc_watermark` | boolean | false |
| `callback_url` | public HTTP(S) webhook | omitted |

The endpoint always returns a `task_id`; poll `POST /minimax/tasks` for completion. Build `content` as an ordered list: include a `text` item for the prompt, then media items with roles such as `first_frame`, `last_frame`, or `reference_audio`.

Public pricing is **$0.057143/s for 768P** and **$0.091429/s for 2K** on the largest package. Failed tasks are not charged.

## Text to video

```bash
curl -X POST https://api.acedata.cloud/minimax/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-H3",
    "content": [
      {
        "type": "text",
        "text": "A red fox running through a snowy forest at dawn, low tracking shot"
      }
    ],
    "resolution": "768P",
    "duration": 4,
    "ratio": "16:9"
  }'
```

The response is a task handle:

```json
{"task_id": "c0f63a98-a7dc-4a09-a1fb-46d32b312a28"}
```

## First-frame image video

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "Preserve the character and clothing while the camera slowly pushes in"
    },
    {
      "type": "image_url",
      "image_url": {"url": "https://cdn.acedata.cloud/b1c82e4937.png"},
      "role": "first_frame"
    }
  ],
  "resolution": "768P",
  "duration": 8,
  "ratio": "adaptive"
}
```

## Reference media

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "A dancer moves naturally to the rhythm"
    },
    {
      "type": "image_url",
      "image_url": {"url": "https://cdn.acedata.cloud/b1c82e4937.png"},
      "role": "reference_image"
    },
    {
      "type": "audio_url",
      "audio_url": {"url": "https://cdn.acedata.cloud/6f7d62b18b.wav"},
      "role": "reference_audio"
    }
  ],
  "resolution": "768P",
  "duration": 8,
  "ratio": "9:16"
}
```

## Poll a task

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

Continue polling about every five seconds until `task.status` is `succeeded`, `failed`, or `cancelled`. Use `retrieve_batch` with `ids` to check several tasks in one request, or `delete` with `id` to delete a task record.

Successful retrieve responses return:

```json
{
  "task": {
    "id": "c0f63a98-a7dc-4a09-a1fb-46d32b312a28",
    "model": "MiniMax-H3",
    "status": "succeeded",
    "content": {"url": "https://cdn.acedata.cloud/minimax/c0f63a98-a7dc-4a09-a1fb-46d32b312a28.mp4"},
    "resolution": "2K",
    "duration": 5,
    "ratio": "adaptive",
    "usage": {"total_seconds": 5, "output_seconds": 5, "input_image_count": 1},
    "task_type": "generation",
    "modality": "video"
  }
}
```

## Gotchas

- Do not send `action` or `async` to `/minimax/videos`; the API creates a task and returns `task_id`.
- `model`, `content`, `resolution`, and `duration` are required.
- `duration` must be an integer from 4 to 15, not a decimal.
- Media URLs are nested objects such as `"image_url": {"url": "https://..."}`.
- Use `role` to distinguish first frame, last frame, reference image, reference video, and reference audio.
- Use public URLs that the generation service can download.
- Finished task video URLs are returned under `task.content.url` and served from AceDataCloud CDN.

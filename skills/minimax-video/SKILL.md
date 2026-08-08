---
name: minimax-video
description: Generate MiniMax H3 videos from text plus optional image/video/audio references through AceDataCloud. Use for text-to-video and multimodal-guided generation, then poll MiniMax tasks.
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
| `content` | array of typed items (see below), min 1 | required |
| `resolution` | `768P`, `2K` | required |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `aigc_watermark` | boolean | false |
| `duration` | integer 4–15 | required |
| `callback_url` | public HTTP(S) webhook | omitted |

`content` items:

- `{"type":"text","text":"..."}` (text max length 7000)
- `{"type":"image_url","image_url":{"url":"..."},"role":"first_frame|last_frame|reference_image"}`
- `{"type":"video_url","video_url":{"url":"..."},"role":"reference_video"}`
- `{"type":"audio_url","audio_url":{"url":"..."},"role":"reference_audio"}`

Public pricing is **$0.057143/s for 768P** and **$0.091429/s for 2K** on the largest package. Failed tasks are not charged.

## Text + first-frame image

```bash
curl -X POST https://api.acedata.cloud/minimax/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-H3",
    "content": [
      {
        "type": "text",
        "text": "Let the character move naturally while the camera slowly pushes in"
      },
      {
        "type": "image_url",
        "image_url": { "url": "https://cdn.acedata.cloud/b1c82e4937.png" },
        "role": "first_frame"
      }
    ],
    "resolution": "2K",
    "duration": 5,
    "ratio": "adaptive"
  }'
```

## Poll a task

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

Continue polling about every five seconds until `task.status` is one of `succeeded`, `failed`, or `cancelled`. Use `retrieve_batch` with `ids` to check several tasks in one request, or `delete` with `id` to remove a task.

## Gotchas

- `model` is case-sensitive (`MiniMax-H3`).
- `content` must include at least one item, and each media item requires `{"url":"..."}` nesting.
- For media content, set a valid `role` that matches the media type.
- Use public URLs that the generation service can download.
- Returned videos are served from AceDataCloud CDN.

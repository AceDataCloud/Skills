---
name: minimax-video
description: Generate MiniMax H3 videos with structured multimodal content through AceDataCloud. Use for text/image/video/audio-conditioned generation and MiniMax task polling.
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
| `content` | array (min 1) of typed blocks | required |
| `resolution` | `768P`, `2K` | `2K` |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `aigc_watermark` | boolean | false |
| `duration` | integer 4–15 | required |
| `callback_url` | public HTTP(S) webhook | omitted |

`content` items use one of:
- `{"type":"text","text":"..."}` (text max 7000 chars)
- `{"type":"image_url","image_url":{"url":"..."},"role":"first_frame|last_frame|reference_image"}`
- `{"type":"video_url","video_url":{"url":"..."},"role":"reference_video"}`
- `{"type":"audio_url","audio_url":{"url":"..."},"role":"reference_audio"}`

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
    "ratio": "16:9",
    "duration": 4
  }'
```

## Image-conditioned video

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
      "image_url": {
        "url": "https://cdn.acedata.cloud/b1c82e4937.png"
      },
      "role": "first_frame"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "https://cdn.acedata.cloud/eb75d88a3f.png"
      },
      "role": "reference_image"
    }
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8
}
```

## Audio-guided video

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
      "image_url": {
        "url": "https://cdn.acedata.cloud/b1c82e4937.png"
      },
      "role": "first_frame"
    },
    {
      "type": "audio_url",
      "audio_url": {
        "url": "https://cdn.acedata.cloud/6f7d62b18b.wav"
      },
      "role": "reference_audio"
    }
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8
}
```

## Poll a task

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

Continue polling about every five seconds until `task.status` reaches a terminal state (`succeeded`, `failed`, or `cancelled`). Use `retrieve_batch` with `ids` to check several tasks in one request.

## Gotchas

- `/minimax/videos` requires `model`, `content`, `resolution`, and `duration`.
- `duration` must be an integer, not a decimal.
- `content` media blocks use nested objects (`image_url.url`, `video_url.url`, `audio_url.url`), not plain URL strings.
- Use valid `role` values for media guidance (`first_frame`, `last_frame`, `reference_image`, `reference_video`, `reference_audio`).
- Use public URLs that the generation service can download.
- Returned videos are served from AceDataCloud CDN.

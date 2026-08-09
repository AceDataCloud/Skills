---
name: minimax-video
description: Generate MiniMax H3 videos from ordered text and media content through AceDataCloud. Use for text-to-video, image/video/audio-referenced video, and MiniMax H3 task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Generate 4–15 second videos through `POST https://api.acedata.cloud/minimax/videos`.
Requests always create a task and return its `task_id`.

> **Setup:** See [authentication](../_shared/authentication.md). Poll the returned task ID with `POST /minimax/tasks`.

## Contract

| Parameter | Values | Required |
| --- | --- | --- |
| `model` | `MiniMax-H3` | Yes |
| `content` | Non-empty ordered array of content items (below) | Yes |
| `resolution` | `768P`, `2K` | Yes |
| `duration` | Integer 4–15 | Yes |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | No |
| `aigc_watermark` | boolean (default `false`) | No |
| `callback_url` | Public webhook URI | No |

Each `content` item has a `type` of `text`, `image_url`, `video_url`, or
`audio_url`. Text items use `text` (maximum 7000 characters); media items use
the corresponding object with a public `url`. Media items may specify one of
`first_frame`, `last_frame`, `reference_image`, `reference_video`, or
`reference_audio` as `role`.

## Text to video

```bash
curl -X POST https://api.acedata.cloud/minimax/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-H3",
    "content": [{
      "type": "text",
      "text": "A red fox running through a snowy forest at dawn, low tracking shot"
    }],
    "resolution": "768P",
    "ratio": "16:9",
    "duration": 4
  }'
```

## Video with references

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
    },
    {
      "type": "audio_url",
      "audio_url": {"url": "https://cdn.acedata.cloud/6f7d62b18b.wav"},
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
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

Continue polling about every five seconds until `task.status` is `succeeded`,
`failed`, or `cancelled`. A succeeded task provides the video at
`task.content.url`. Use `retrieve_batch` with `ids` to check several tasks, or
use `delete` with `id` to remove a task. Batch retrieval also accepts `limit`,
`offset`, `created_at_min`, and `created_at_max`.

## Gotchas

- Do not send obsolete `prompt`, `image_urls`, `audio_urls`, or `async` fields;
  `/minimax/videos` accepts only the documented contract.
- `duration` must be an integer, not a decimal.
- Use public media URLs that the generation service can download.
- Returned videos are served from AceDataCloud CDN.

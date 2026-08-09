---
name: minimax-video
description: Generate MiniMax H3 videos through AceDataCloud with the unified `content` array contract (text/image/video/audio blocks) and poll MiniMax tasks.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Generate videos through `POST https://api.acedata.cloud/minimax/videos`.

> **Setup:** See [authentication](../_shared/authentication.md). For long jobs, use [async task polling](../_shared/async-tasks.md) with `POST /minimax/tasks`.

## Contract

| Parameter | Values | Default |
| --- | --- | --- |
| `model` | `MiniMax-H3` | required |
| `content` | array (min 1 item), each item requires `type` | required |
| `resolution` | `768P`, `2K` | required |
| `duration` | integer `4`–`15` | required |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `aigc_watermark` | boolean | `false` |
| `callback_url` | public HTTP(S) webhook | omitted |

### `content` item schema

Each array item is an object with required `type`:

- `type: "text"` + `text` (max 7000 chars)
- `type: "image_url"` + `image_url: { "url": "..." }`
- `type: "video_url"` + `video_url: { "url": "..." }`
- `type: "audio_url"` + `audio_url: { "url": "..." }`

Optional `role` values: `first_frame`, `last_frame`, `reference_image`, `reference_video`, `reference_audio`.

## Example request

```json
{
  "model": "MiniMax-H3",
  "content": [
    { "type": "text", "text": "A red fox running through a snowy forest at dawn, low tracking shot" },
    { "type": "image_url", "image_url": { "url": "https://cdn.example.com/reference-1.png" }, "role": "reference_image" }
  ],
  "resolution": "768P",
  "duration": 5,
  "ratio": "16:9",
  "aigc_watermark": false
}
```

## Poll a task

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

`/minimax/tasks` supports:

- `action: "retrieve"` with `id`
- `action: "retrieve_batch"` with `ids`
- `action: "delete"` with `id`

Optional list filters: `limit`, `offset`, `created_at_min`, `created_at_max`.

## Task statuses

Video tasks use: `queued`, `running`, `succeeded`, `failed`, `cancelled`.

## Gotchas

- Do not send old `prompt`, `image_urls`, or `audio_urls` top-level fields; use unified `content` items.
- `model` is `MiniMax-H3` (case-sensitive).
- Every media URL must be publicly reachable by the generation service.
- `duration` must be an integer from 4 to 15.

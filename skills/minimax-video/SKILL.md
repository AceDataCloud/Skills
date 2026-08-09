---
name: minimax-video
description: Generate MiniMax H3 videos from text and optional image, video, or audio references through AceDataCloud. Use for text-to-video, first/last-frame video, multimodal reference video, and MiniMax H3 task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Generate 4–15 second videos through `POST https://api.acedata.cloud/minimax/videos`. Use the V2 multimodal `content` array to supply the prompt and optional reference media.

> **Setup:** See [authentication](../_shared/authentication.md). By default `/minimax/videos` waits for completion and returns `task`; pass `async: true` or `callback_url` to get `task_id`/`trace_id` immediately and poll with `POST /minimax/tasks`.

## Contract

| Parameter | Values | Default |
| --- | --- | --- |
| `model` | `MiniMax-H3` | required |
| `content` | array of prompt and optional media items | required |
| `resolution` | `768P`, `2K` | required |
| `duration` | integer 4–15 | required |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `async` | boolean | `false` |
| `callback_url` | public HTTP(S) webhook; forces async mode | omitted |

Each `content` item is one of the documented typed objects: `text` items require non-empty `text`; `image_url` items require `image_url` and may set `role`; `video_url` and `audio_url` items require their URL field and a matching reference role. Media roles are:

| Role | Use |
| --- | --- |
| `first_frame` | Starting image |
| `last_frame` | Ending image |
| `reference_image` | Reference image (`image_url` only) |
| `reference_video` | Reference video (`video_url` only; required for `video_url`) |
| `reference_audio` | Reference audio (`audio_url` only; required for `audio_url`) |

Include a `text` item with the generation prompt in every request. Text items accept 1–7000 characters. Image roles are limited to `first_frame`, `last_frame`, and `reference_image`.

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

## First and last frame video

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "A camera slowly pushes in as the character walks into the sunrise."
    },
    {
      "type": "image_url",
      "image_url": "https://cdn.acedata.cloud/first-frame.png",
      "role": "first_frame"
    },
    {
      "type": "image_url",
      "image_url": "https://cdn.acedata.cloud/last-frame.png",
      "role": "last_frame"
    }
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8
}
```

## Reference-guided video

```json
{
  "model": "MiniMax-H3",
  "content": [
    {
      "type": "text",
      "text": "A dancer moves naturally to the rhythm."
    },
    {
      "type": "image_url",
      "image_url": "https://cdn.acedata.cloud/reference.png",
      "role": "reference_image"
    },
    {
      "type": "audio_url",
      "audio_url": "https://cdn.acedata.cloud/reference.wav",
      "role": "reference_audio"
    }
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8
}
```


## Synchronous vs asynchronous responses

Without `async` or `callback_url`, `/minimax/videos` returns a completed response shaped as `{ "task": { ... } }`; read the video from `task.content.url` when `task.status` is `succeeded`. With `"async": true` or `callback_url`, it returns `{ "task_id": "...", "trace_id": "..." }`; save `task_id` for polling.

## Poll a task

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

Continue polling about every ten seconds until the task reaches a terminal state. `retrieve` returns `{ "task": ... }`; `retrieve_batch` with `ids` returns `{ "items": [...], "total": n }`; `delete` with `id` returns `{ "id": "...", "deleted": true }`. Batch listing also accepts `limit`, `offset`, `created_at_min`, and `created_at_max`.

## Gotchas

- Do not send `action` to `/minimax/videos`; the API infers the mode from media inputs.
- `duration` must be an integer, not a decimal.
- Put the prompt in a `content` item with `type: "text"`; do not send a top-level `prompt`.
- Use `first_frame`, `last_frame`, and reference roles explicitly; do not rely on item order to determine an image's role.
- Use public URLs that the generation service can download for every media item.
- Do not send legacy fields such as top-level `prompt`, `image_urls`, `audio_urls`, `messages`, or `first_frame_image`; migrate everything into `content`.
- Returned videos are served from AceDataCloud CDN.

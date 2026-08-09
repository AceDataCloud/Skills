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

Generate 4–15 second videos through `POST https://api.acedata.cloud/minimax/videos`. Use the V2 multimodal `content` array to supply the prompt and optional reference media. By default the request waits for completion and returns a `task`; set `async: true` or provide `callback_url` to return `task_id` and `trace_id` immediately.

> **Setup:** See [authentication](../_shared/authentication.md). For long jobs, use [async task polling](../_shared/async-tasks.md) with `POST /minimax/tasks`.

## Contract

| Parameter | Values | Default |
| --- | --- | --- |
| `model` | `MiniMax-H3` | required |
| `content` | array of prompt and optional media items | required |
| `resolution` | `768P`, `2K` | required |
| `duration` | integer 4–15 | required |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `async` | boolean | `false` |
| `callback_url` | public HTTP(S) webhook | omitted |

Each `content` item has a `type` of `text`, `image_url`, `video_url`, or `audio_url`; set the matching field to the text or a media object such as `{"url": "https://..."}`. Text items require non-empty `text` (max 7000 characters). Video and audio items require their matching reference role; image roles are optional but should be explicit for frame/reference use:

| Role | Use |
| --- | --- |
| `first_frame` | Starting image |
| `last_frame` | Ending image |
| `reference_image` | Reference image |
| `reference_video` | Reference video |
| `reference_audio` | Reference audio |

Include a `text` item with the generation prompt in every request.

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
    "duration": 4,
    "async": true
  }'
```

With async mode enabled, the creation response is:

```json
{
  "task_id": "c0f63a98-a7dc-4a09-a1fb-46d32b312a28",
  "trace_id": "trace_7f8c2b1a"
}
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
      "image_url": {
        "url": "https://cdn.acedata.cloud/first-frame.png"
      },
      "role": "first_frame"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "https://cdn.acedata.cloud/last-frame.png"
      },
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
      "image_url": {
        "url": "https://cdn.acedata.cloud/reference.png"
      },
      "role": "reference_image"
    },
    {
      "type": "audio_url",
      "audio_url": {
        "url": "https://cdn.acedata.cloud/reference.wav"
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

Continue polling about every five seconds until the task reaches a terminal state. Use `retrieve_batch` with `ids` to check several tasks, or `delete` with `id` to remove a task. Batch listing also accepts `limit`, `offset`, `created_at_min`, and `created_at_max`.

## Gotchas

- Do not send `action` to `/minimax/videos`; the API infers the mode from media inputs.
- `duration` must be an integer, not a decimal.
- Omit `async` for a synchronous completed `task` response; set `async: true` or `callback_url` for `task_id`/`trace_id` polling.
- Put the prompt in a `content` item with `type: "text"`; do not send a top-level `prompt`.
- Use `first_frame`, `last_frame`, and reference roles explicitly; do not rely on item order to determine an image's role. `video_url` only accepts `reference_video`; `audio_url` only accepts `reference_audio`.
- Use public URLs that the generation service can download for every media item.
- Returned videos are served from AceDataCloud CDN.

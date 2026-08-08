---
name: minimax-video
description: Generate MiniMax H3 videos from text, image frames, and image, video, or audio references through AceDataCloud. Use for MiniMax H3 video generation and task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Create an asynchronous MiniMax H3 video task with `POST https://api.acedata.cloud/minimax/videos`.
The request uses the V2 multimodal `content` format and returns a `task_id`
immediately. Poll it with `POST /minimax/tasks`.

> **Setup:** See [authentication](../_shared/authentication.md).

## Contract

| Parameter | Values | Required |
| --- | --- | --- |
| `model` | `MiniMax-H3` | yes |
| `content` | multimodal content array containing a non-empty text item | yes |
| `resolution` | `768P`, `2K` | yes |
| `duration` | integer 4–15 seconds | yes |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | conditional |
| `callback_url` | public callback URL | no |
| `aigc_watermark` | boolean (default `false`) | no |

For text-only video, `ratio` is required and cannot be `adaptive`. For
first-/last-frame video, omit `ratio` or use `adaptive`; the frame determines
the ratio. Reference-media video defaults to `adaptive`.

The endpoint is always asynchronous. It does not accept the legacy
`prompt`, `image_urls`, `audio_urls`, `messages`, `first_frame_image`, or
`async` fields.

## Content items

Every item has a `type`. Include one non-empty `text` item (at most 7,000
characters) in every request.

| `type` | Value field | `role` |
| --- | --- | --- |
| `text` | `text` | none |
| `image_url` | `image_url.url` | `first_frame`, `last_frame`, or `reference_image` |
| `video_url` | `video_url.url` | `reference_video` |
| `audio_url` | `audio_url.url` | `reference_audio` |

Media URLs may be public HTTPS URLs, `mm_file://{file_id}`, or media-specific
Base64 data URIs. First-/last-frame inputs cannot be combined with any
reference-media input. Use at most one first frame, one last frame, nine
reference images, three reference videos, and three reference audios; reference
media totals at most 12 files.

## Text to video

```bash
curl -X POST https://api.acedata.cloud/minimax/videos \
  -H "Authorization: ******ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-H3",
    "content": [{
      "type": "text",
      "text": "A red fox runs through a snowy forest at dawn, cinematic tracking shot"
    }],
    "resolution": "768P",
    "duration": 4,
    "ratio": "16:9"
  }'
```

The successful response is:

```json
{"task_id":"TASK_ID"}
```

## First and last frame video

```json
{
  "model": "MiniMax-H3",
  "content": [
    {"type": "text", "text": "The character naturally walks toward the camera"},
    {
      "type": "image_url",
      "image_url": {"url": "https://example.com/first.png"},
      "role": "first_frame"
    },
    {
      "type": "image_url",
      "image_url": {"url": "https://example.com/last.png"},
      "role": "last_frame"
    }
  ],
  "resolution": "2K",
  "duration": 5,
  "ratio": "adaptive"
}
```

## Reference-media video

```json
{
  "model": "MiniMax-H3",
  "content": [
    {"type": "text", "text": "Keep the character consistent and follow the reference movement"},
    {
      "type": "image_url",
      "image_url": {"url": "https://example.com/character.png"},
      "role": "reference_image"
    },
    {
      "type": "video_url",
      "video_url": {"url": "https://example.com/movement.mp4"},
      "role": "reference_video"
    },
    {
      "type": "audio_url",
      "audio_url": {"url": "https://example.com/audio.wav"},
      "role": "reference_audio"
    }
  ],
  "resolution": "2K",
  "duration": 5
}
```

## Poll and manage tasks

Poll approximately every 10 seconds. `queued` and `running` are non-terminal;
stop when the status is `succeeded`, `failed`, or `cancelled`. On success, use
`task.content.url`; a failed task includes `task.error.code` and
`task.error.message`.

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: ******ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

`action` defaults to `retrieve`. Use `retrieve_batch` with optional `ids`,
`created_at_min`, `created_at_max`, `offset`, and `limit`; it returns
`{"items":[...],"total":number}`. Use `delete` with `id` to cancel a queued
task or remove a completed task record. Tasks can be queried for the most
recent seven days.

Task records include the model, status, timestamps, output `content.url`,
resolution, duration, actual ratio, and `usage` (`total_seconds`,
`input_seconds`, `output_seconds`, and `input_image_count`).

## Callback

When using `callback_url`, first respond to the platform's POST verification
request by echoing its `challenge` within three seconds. Later status
notifications use the task response structure. Save the `task_id` and poll as
a fallback for missed notifications.

## Gotchas

- The model name is case-sensitive: `MiniMax-H3`, not `minimax-h3`.
- A successful creation response only means the task was queued; use task
  status before treating a video as available.
- Do not mix first-/last-frame inputs with reference images, video, or audio.
- Use public URLs that the generation service can download when not using
  `mm_file://` or a Base64 data URI.

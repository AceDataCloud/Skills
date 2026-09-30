---
name: minimax-video
description: Generate MiniMax H3 and H3 Max videos, enhance prompts, or regenerate owned source videos through AceDataCloud. Use for text/image/video/audio references, model-specific output settings, structured prompt guidance and asynchronous task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env (see _shared/authentication.md).
---

# MiniMax H3 Video Generation

Generate 4–15 second videos through `POST https://api.acedata.cloud/minimax/videos`. Use the V2 multimodal `content` array to supply the prompt and optional reference media.

> **Setup:** See [authentication](../_shared/authentication.md). The HTTP API waits for the final result by default. Agents and MCP clients should send `"async": true`, save the returned `task_id`, then use [async task polling](../_shared/async-tasks.md) with `POST /minimax/tasks`. MiniMax MCP generation tools expose `async` and default it to `true`.

## Contract

| Parameter | Values | Default |
| --- | --- | --- |
| `model` | `MiniMax-H3` | required |
| `content` | array of prompt and optional media items | required |
| `resolution` | `768P`, `2K` | required |
| `duration` | integer 4–15 | required |
| `ratio` | `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16` | omitted |
| `async` | `true`, `false` | `false` at the HTTP API; `true` in MiniMax MCP tools |
| `callback_url` | public HTTP(S) webhook; also enables async mode | omitted |

Each `content` item has a `type` of `text`, `image_url`, `video_url`, or `audio_url`; set the matching field to the text or public URL. Media items use a `role`:

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
      "image_url": {"url": "https://cdn.acedata.cloud/first-frame.png"},
      "role": "first_frame"
    },
    {
      "type": "image_url",
      "image_url": {"url": "https://cdn.acedata.cloud/last-frame.png"},
      "role": "last_frame"
    }
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8,
  "async": true
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
      "image_url": {"url": "https://cdn.acedata.cloud/reference.png"},
      "role": "reference_image"
    },
    {
      "type": "audio_url",
      "audio_url": {"url": "https://cdn.acedata.cloud/reference.wav"},
      "role": "reference_audio"
    }
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8,
  "async": true
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
- Put the prompt in a `content` item with `type: "text"`; do not send a top-level `prompt`.
- Use `first_frame`, `last_frame`, and reference roles explicitly; do not rely on item order to determine an image's role.
- Use public URLs that the generation service can download for every media item.
- Returned videos are served from AceDataCloud CDN.

## H3 Max, prompt enhancement and regeneration

H3 Max uses public model `MiniMax-H3-Max` through `/minimax/videos`. Select 480P or 768P and an integer duration 5–15 seconds. H3 retains 768P/2K and 4–15 seconds. Keep model-specific resolution and duration settings.

`POST /minimax/prompt-enhancement` accepts H3 content, duration and ratio and returns structured prompt guidance. `POST /minimax/regenerate` outputs 2K from an owned completed H3 768P source_task_id, or exact original content plus exactly one base_video. Missing/truncated original inputs are rejected. Use platform task IDs.

Companion MCP tools: minimax_generate_max_video, minimax_enhance_prompt, minimax_regenerate_video. CLI commands: max-video, enhance-prompt, regenerate with --request-file. Poll through /minimax/tasks. Generation/regeneration billing includes output duration, input video duration and extra reference images according to the selected operation.

---
name: minimax-video
description: Generate MiniMax H3 videos from text, up to nine reference images, or up to three audio references through AceDataCloud. Use for text-to-video, multi-image video, audio-guided video, and MiniMax H3 task polling.
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
| `model` | `minimax-h3` | `minimax-h3` |
| `prompt` | non-empty string, max 7000 chars | required |
| `image_urls` | 1–9 public HTTP(S) URLs | omitted |
| `audio_urls` | 1–3 public HTTP(S) URLs | omitted |
| `resolution` | `768P`, `2K` | `2K` |
| `ratio` | `16:9`, `9:16` | `16:9` |
| `aigc_watermark` | boolean | false |
| `duration` | integer 4–15 | 4 |
| `async` | boolean | false |
| `callback_url` | public HTTP(S) webhook | omitted |

`prompt` is required in every mode. Audio also requires at least one image. Mode inference is deterministic:

1. `audio_urls` present → audio-guided video
2. otherwise `image_urls` present → image-to-video
3. otherwise → text-to-video

Public pricing is **$0.057143/s for 768P** and **$0.091429/s for 2K** on the largest package. Failed tasks are not charged.

## Text to video

```bash
curl -X POST https://api.acedata.cloud/minimax/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimax-h3",
    "prompt": "A red fox running through a snowy forest at dawn, low tracking shot",
    "resolution": "768P",
    "ratio": "16:9",
    "duration": 4,
    "async": true
  }'
```

## Multi-image video

```json
{
  "model": "minimax-h3",
  "prompt": "Preserve the character and clothing while the camera slowly pushes in",
  "image_urls": [
    "https://cdn.acedata.cloud/b1c82e4937.png",
    "https://cdn.acedata.cloud/eb75d88a3f.png"
  ],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8,
  "async": true
}
```

## Audio-guided video

```json
{
  "model": "minimax-h3",
  "prompt": "A dancer moves naturally to the rhythm",
  "image_urls": ["https://cdn.acedata.cloud/b1c82e4937.png"],
  "audio_urls": ["https://cdn.acedata.cloud/6f7d62b18b.wav"],
  "resolution": "768P",
  "ratio": "9:16",
  "duration": 8,
  "async": true
}
```

## Poll a task

```bash
curl -X POST https://api.acedata.cloud/minimax/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID"}'
```

Continue polling about every five seconds until `response.success` is true or an error appears. Use `retrieve_batch` with `ids` to check several tasks in one request.

## Gotchas

- Do not send `action` to `/minimax/videos`; the API infers the mode from media inputs.
- `duration` must be an integer, not a decimal.
- Audio mode requires both `prompt` and at least one `image_urls` entry.
- Single-image mode uses the image as the first frame; multiple images are references.
- Use public URLs that the generation service can download.
- Returned videos are served from AceDataCloud CDN.

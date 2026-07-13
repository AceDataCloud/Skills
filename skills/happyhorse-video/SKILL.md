---
name: happyhorse-video
description: Generate and edit AI videos with Happy Horse via AceDataCloud API. Use when creating videos from text prompts, animating a first-frame image, generating scenes from up to 9 subject or style reference images, or editing an existing video with optional references. Supports 720P/1080P output, 3-15 second generation, aspect-ratio control, audio preservation, seeds, callbacks, and asynchronous task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-happyhorse for tool-use.
---

# Happy Horse Video Generation and Editing

Use Happy Horse through AceDataCloud for text-to-video, first-frame animation, reference-guided
generation, and video editing.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Choose an Action

| Goal | `action` | Valid models | Required input |
|---|---|---|---|
| Generate from text | `generate` | `happyhorse-1.0-t2v`, `happyhorse-1.1-t2v` | `prompt` |
| Animate one image | `image_to_video` | `happyhorse-1.0-i2v`, `happyhorse-1.1-i2v` | `image_url` |
| Generate from references | `reference_to_video` | `happyhorse-1.0-r2v`, `happyhorse-1.1-r2v` | `prompt`, 1-9 `image_urls` |
| Edit a video | `video_edit` | `happyhorse-1.0-video-edit` | `prompt`, `video_url` |

The 1.1 model is the default where available. Video editing currently has only a 1.0 model.

## Quick Start

Submit text-to-video asynchronously:

```bash
curl -X POST https://api.acedata.cloud/happyhorse/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate",
    "model": "happyhorse-1.1-t2v",
    "prompt": "A cinematic white horse crossing a snowy ridge at sunrise, wind moving its mane, slow camera push",
    "resolution": "720P",
    "ratio": "16:9",
    "duration": 5,
    "async": true
  }'
```

The response contains a `task_id`. Poll it after about 15 seconds:

```bash
curl -X POST https://api.acedata.cloud/happyhorse/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id>", "action": "retrieve"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Continue until
> `response.data[].video_url` appears or a terminal error is returned.

## Workflows

### Text-to-Video

Use `generate` when no visual input exists. Describe the subject, action, environment, camera,
lighting, and style.

```json
POST /happyhorse/videos
{
  "action": "generate",
  "model": "happyhorse-1.1-t2v",
  "prompt": "A white horse gallops across a moonlit beach, side tracking shot, silver reflections, cinematic realism",
  "resolution": "1080P",
  "ratio": "16:9",
  "duration": 8,
  "seed": 42
}
```

### First-Frame Image-to-Video

Use `image_to_video` to animate one image. `prompt` is optional but useful for motion and camera
direction. The output ratio follows the first-frame image, so omit `ratio`.

```json
POST /happyhorse/videos
{
  "action": "image_to_video",
  "model": "happyhorse-1.1-i2v",
  "image_url": "https://example.com/horse.jpg",
  "prompt": "The horse slowly lifts its head as the mane moves in the breeze, gentle camera push",
  "resolution": "1080P",
  "duration": 5
}
```

### Reference-to-Video

Use `reference_to_video` with 1-9 reference images. Mention images as `character1`, `character2`,
and so on in list order when the prompt needs to distinguish them.

```json
POST /happyhorse/videos
{
  "action": "reference_to_video",
  "model": "happyhorse-1.1-r2v",
  "prompt": "character1 walks through a sunrise meadow wearing the leather and gold style from character2",
  "image_urls": [
    "https://example.com/subject.jpg",
    "https://example.com/style.jpg"
  ],
  "resolution": "720P",
  "ratio": "16:9",
  "duration": 5
}
```

### Video Editing

Use `video_edit` with an existing video and editing instructions. Add at most 5 reference images
for wardrobe, subject, style, or local replacement guidance. Use `audio_setting: "origin"` to
preserve the source audio.

```json
POST /happyhorse/videos
{
  "action": "video_edit",
  "model": "happyhorse-1.0-video-edit",
  "prompt": "Apply the warm leather and gold style from the reference while preserving camera motion",
  "video_url": "https://example.com/source.mp4",
  "image_urls": ["https://example.com/style.jpg"],
  "resolution": "720P",
  "audio_setting": "origin"
}
```

Do not send `duration` or `ratio` for video editing. Output duration follows the source video.

## Parameters

| Parameter | Values | Notes |
|---|---|---|
| `action` | `generate`, `image_to_video`, `reference_to_video`, `video_edit` | Defaults to `generate` |
| `model` | See action table | The model family must match the action |
| `prompt` | string | Required except for `image_to_video` |
| `image_url` | URL | First frame for `image_to_video` |
| `image_urls` | URL array | 1-9 for reference generation; 0-5 for editing |
| `video_url` | URL | Required only for editing |
| `resolution` | `720P`, `1080P` | Uppercase `P` is required; default `1080P` |
| `ratio` | `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | Text/reference generation only |
| `duration` | integer 3-15 | Generation only; default 5 seconds |
| `watermark` | boolean | Default `false` |
| `audio_setting` | `auto`, `origin` | Video editing only; `origin` preserves source audio |
| `seed` | integer 0-2147483647 | Optional reproducibility seed |
| `callback_url` | URL | Webhook for final result; returns immediately |
| `async` | boolean | Set `true` to return a task ID for polling |

## Task Queries

Retrieve one task:

```json
POST /happyhorse/tasks
{"id": "<task_id>", "action": "retrieve"}
```

Retrieve several tasks:

```json
POST /happyhorse/tasks
{"ids": ["<task_id_1>", "<task_id_2>"], "action": "retrieve_batch"}
```

A completed single-task response stores the original request in `request` and the final API result
in `response`. Read the media URL from `response.data[].video_url`.

## Gotchas

- Match the model family to `action`; for example, an `*-i2v` model is invalid for `generate`
- Resolution values are `720P` and `1080P`, not lowercase `720p` / `1080p`
- Generated duration must be an integer from 3 through 15 seconds
- `image_to_video` requires `image_url`; its prompt is optional and its ratio follows the image
- `reference_to_video` requires a prompt and 1-9 images
- `video_edit` requires both prompt and video URL, accepts at most 5 references, and ignores duration/ratio
- `audio_setting` applies to video editing; use `origin` to preserve source audio
- A `task_id` is not a completed result; poll until a final video URL or terminal error appears
- Failed tasks are not billed; video edits use the upstream-reported input plus output duration for billing

> **MCP:** `pip install mcp-happyhorse` | Hosted:
> `https://happyhorse.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
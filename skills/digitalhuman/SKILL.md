---
name: digitalhuman
description: Generate talking-head digital human videos and cloned voices via AceDataCloud API. Use when animating a source face video or portrait image with audio, or when generating speech from text with a cloned voice. Supports async task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Digital Human — Talking-Head Video + Voice Cloning

Generate lip-synced digital human videos through AceDataCloud's Digital Human API. You can drive the output from either a source face **video** or **image**, then animate it with a supplied audio track or with text spoken by a cloned voice.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

Create a talking-head video asynchronously:

```bash
curl -X POST https://api.acedata.cloud/digital-human/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/portrait.jpg",
    "audio_url": "https://example.com/voiceover.mp3",
    "async": true
  }'
```

The response contains a `task_id`. Poll for the detailed result:

```bash
curl -X POST https://api.acedata.cloud/digital-human/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id>", "action": "retrieve"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). This service uses `task_id` (not `id`) when polling a single task.

## Endpoints

| Endpoint | Use For |
|----------|---------|
| `POST /digital-human/videos` | Create a talking-head video from a source face video or portrait image |
| `POST /digital-human/voices` | Clone a voice from a short sample clip |
| `POST /digital-human/tasks` | Poll async tasks and use documented task actions such as `retrieve_batch` or `delete` |

## 1. Create Video

Use either a source face **video** or **image**:

```json
POST /digital-human/videos
{
  "video_url": "https://example.com/source-face.mp4",
  "audio_url": "https://example.com/speech.wav",
  "guidance": 2,
  "steps": 40,
  "seam_fix": true,
  "speed": 1,
  "async": true
}
```

You can also drive speech from text by pairing `text` with a previously cloned `voice_id`:

```json
POST /digital-human/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "text": "Welcome to our product launch.",
  "voice_id": "f754a190e26c",
  "async": true
}
```

### Video Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `video_url` | conditional | URL | Source face video URL; provide this **or** `image_url` |
| `image_url` | conditional | URL | Source portrait image URL; provide this **or** `video_url` |
| `audio_url` | conditional | URL | Driving audio URL (`.wav`, `.mp3`, `.m4a`); provide this, or pair `text` with `voice_id` |
| `text` | conditional | string | Spoken text for TTS-driven generation; requires `voice_id` |
| `voice_id` | conditional | string | Cloned voice ID returned by `POST /digital-human/voices` |
| `guidance` | | number | Lip-sync strength (default `2.0`) |
| `steps` | | integer | Diffusion steps (default `40`) |
| `seam_fix` | | boolean | Enable mouth seam reduction blend (default `true`) |
| `speed` | | number | Audio tempo multiplier (default `1.0`) |
| `engine` | | `latentsync`, `heygem` | Deprecated compatibility field; no longer changes output or price |
| `resolution` | | `720p`, `540p` | Deprecated compatibility field; output is always `720p` |
| `callback_url` | | URL | Webhook for async completion |
| `async` | | boolean | Return a task immediately instead of waiting |

## 2. Clone Voice

```json
POST /digital-human/voices
{
  "audio_url": "https://example.com/voice-sample.wav",
  "lang": "en",
  "name": "Product narrator",
  "async": true
}
```

### Voice Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `audio_url` | ✓ | URL | Public URL of a clean 10–20 second voice sample |
| `lang` | | `zh`, `en` | Voice sample language (default `zh`) |
| `name` | | string | Optional label for the cloned voice |
| `async` | | boolean | Return a task immediately instead of waiting |

## 3. Poll Tasks

Retrieve one task:

```json
POST /digital-human/tasks
{"task_id": "<task_id>", "action": "retrieve"}
```

The spec also documents `retrieve_batch` and `delete` task actions on this endpoint.

When available, the detailed retrieve response can include lifecycle metadata such as `created_at`, `started_at`, `finished_at`, and `elapsed`, alongside fields like `video_url`, `duration`, `width`, `height`, `engine`, and `progress`.

## Gotchas

- Supply **either** `video_url` **or** `image_url`; the API rejects requests missing both.
- Supply either `audio_url`, or `text` together with `voice_id`, for speech input.
- `engine` is deprecated and kept only for backward compatibility — it no longer changes output quality, speed tier, or pricing.
- `resolution` is deprecated — output is always rendered at `720p`.
- `POST /digital-human/tasks` uses `task_id` for single lookups, not the more common `id`.
- A 400 error example now reads `video_url or image_url is required`, matching the current spec.

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

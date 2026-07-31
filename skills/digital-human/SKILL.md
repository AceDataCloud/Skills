---
name: digital-human
description: Generate AI digital human lip-sync videos and clone voices via AceDataCloud API. Use when animating a face video or portrait photo to speak given audio or TTS text, cloning voices for TTS-driven animation, or creating lip-synced talking-head videos with LatentSync or HeyGem engines.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Digital Human Video Generation

Generate AI lip-sync digital human videos through AceDataCloud's Digital Human API. Animate a face video or portrait photo to speak given audio or synthesised speech.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/digital-human/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://cdn.acedata.cloud/634d760216.mp4",
    "audio_url": "https://example.com/speech.mp3",
    "async": true
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll `POST /digital-human/tasks` with `{"task_id": "<task_id>"}` until `state` is `"succeed"`.

```bash
curl -X POST https://api.acedata.cloud/digital-human/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id from above>"}'
```

## Engines

| Engine | Speed | Best For |
|--------|-------|---------|
| `latentsync` | Slower | Highest quality lip-sync (default) |
| `heygem` | Faster | Fast tier, good for drafts |

## Workflows

### 1. Video-Driven (Lip-Sync from Audio)

Animate an existing face video to speak your audio track.

```json
POST /digital-human/videos
{
  "video_url": "https://cdn.acedata.cloud/634d760216.mp4",
  "audio_url": "https://example.com/voiceover.wav",
  "engine": "latentsync",
  "resolution": "720p",
  "async": true
}
```

### 2. Photo-Driven (Portrait + Audio)

Animate a still portrait photo to speak your audio track.

```json
POST /digital-human/videos
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/speech.mp3",
  "engine": "latentsync",
  "async": true
}
```

### 3. TTS-Driven (Text + Cloned Voice)

First clone a voice, then use it to synthesize speech for the animation.

**Step 1 — Clone a voice:**

```json
POST /digital-human/voices
{
  "audio_url": "https://example.com/voice-sample.wav",
  "lang": "zh",
  "name": "my-voice"
}
```

Returns `voice_id` in the response.

**Step 2 — Generate the video with TTS:**

```json
POST /digital-human/videos
{
  "video_url": "https://cdn.acedata.cloud/634d760216.mp4",
  "text": "大家好，这是离线生成的数字人。",
  "voice_id": "<voice_id from Step 1>",
  "async": true
}
```

## Parameters — `/digital-human/videos`

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `video_url` | ✓¹ | URL | Source face video (public, preferred input) |
| `image_url` | ✓¹ | URL | Source face photo (portrait-driven path) |
| `audio_url` | | URL | Driving audio — `.wav`, `.mp3`, or `.m4a`. Required unless using TTS (`text` + `voice_id`) |
| `text` | | string | Spoken text for TTS (requires `voice_id`) |
| `voice_id` | | string | Voice cloned via `POST /digital-human/voices` |
| `engine` | | `"latentsync"`, `"heygem"` | Processing engine (default: `"latentsync"`) |
| `guidance` | | number | Lip-sync strength for LatentSync — lower = looser sync (default: `2.0`) |
| `steps` | | integer | Diffusion steps for LatentSync (default: `40`) |
| `seam_fix` | | boolean | Apply mouth-seam reduction blend (default: `true`) |
| `speed` | | number | Audio tempo multiplier (default: `1.0`) |
| `resolution` | | `"720p"`, `"540p"` | Output resolution (default: `"720p"`) |
| `callback_url` | | URL | Webhook URL for async result delivery |
| `async` | | boolean | Return task ID immediately instead of blocking (default: `false`) |

¹ One of `video_url` or `image_url` is required.

## Parameters — `/digital-human/voices`

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `audio_url` | ✓ | URL | Clean 10–20s voice sample (public URL) |
| `lang` | | `"zh"`, `"en"` | Language of the voice sample (default: `"zh"`) |
| `name` | | string | Optional label for the voice |
| `async` | | boolean | Return task ID immediately (default: `false`) |

## Task Polling

```json
POST /digital-human/tasks
{"task_id": "<task_id>"}
```

The response contains `state` (`"succeed"` when done), `video_url`, `duration`, `width`, `height`, and `engine`.

Use `action: "retrieve"` for the detailed shape including `created_at`, `started_at`, `finished_at`, and `elapsed` (all Unix timestamps in seconds):

```json
POST /digital-human/tasks
{"task_id": "<task_id>", "action": "retrieve"}
```

## Gotchas

- Supply either `video_url` **or** `image_url` — not both
- The audio source is either `audio_url` **or** `text` + `voice_id` — not mixed
- `guidance`, `steps`, and `seam_fix` only apply to the `latentsync` engine
- Use `async: true` or `callback_url` for long jobs — synchronous mode may time out
- Task terminal state is `state: "succeed"`
- `voice_id` must be obtained from a prior `POST /digital-human/voices` call

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

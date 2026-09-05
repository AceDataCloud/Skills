---
name: fish-audio
description: Generate AI text-to-speech audio with Fish Audio, including saved voices or one-shot reference-audio cloning via AceDataCloud API. Use when creating voiceover/narration audio (TTS), synthesizing multilingual speech, selecting a Fish reference voice from the model catalog, or temporarily cloning a voice from an audio sample plus transcript.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Fish Audio — Text-to-Speech

Generate narration / voiceover through AceDataCloud's Fish Audio API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: ******ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{"text":"你好，欢迎使用 AceData Cloud。","reference_id":"d7900c21663f485ab63ebdb7e5905036","format":"mp3"}'
```

Synchronous responses return a direct audio URL:

```json
{"audio_url":"https://platform.r2.fish.audio/task/8a72ff9840234006a9f74cb2fa04f978.mp3"}
```

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Text-to-speech generation |
| `GET /fish/model` | Browse/search public Fish reference voices |
| `GET /fish/model/{id}` | Fetch one reference voice by ID |
| `POST /fish/tasks` | Poll async TTS jobs when `async: true` |

## Workflows

### 1. Find a reference voice

```bash
curl "https://api.acedata.cloud/fish/model?page_size=10&page_number=1&title=Marcus" \
  -H "Authorization: ******ACEDATACLOUD_API_TOKEN"
```

The response includes `items[]` with public voice metadata such as `_id`, `title`,
`languages`, `tags`, `visibility`, and `state`. Use an item `_id` as
`reference_id` in TTS requests.

### 2. Text-to-Speech

```json
POST /fish/tts
Headers:
  model: s2-pro

{
  "text": "Your narration text.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3"
}
```

### 3. One-shot voice cloning

Use `references` when you have a publicly reachable HTTPS MP3/WAV sample and an
accurate transcript, but do not want to create a reusable model. Only one
reference sample is accepted per request.

```json
POST /fish/tts
Headers:
  model: s2-pro

{
  "text": "A new journey begins now.",
  "format": "mp3",
  "references": [{
    "audio": "https://cdn.acedata.cloud/reference-voice.mp3",
    "text": "Spring morning sunlight filtered through the trees."
  }]
}
```

Do not send `reference_id` and `references` together.

### 4. Async TTS

```json
POST /fish/tts
Headers:
  model: s1

{
  "text": "Longer narration for background processing.",
  "async": true,
  "callback_url": "https://api.acedata.cloud/health"
}
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id":"..."}`.

## Parameters — `/fish/tts`

### Header

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `"s1"`, `"s2-pro"`, `"s2.1-pro"` | Fish TTS engine selection |

### JSON body

| Parameter | Type / Values | Description |
|-----------|---------------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string \| string[] | Saved/public voice model ID(s) from `GET /fish/model`; mutually exclusive with `references` |
| `format` | `"mp3"`, `"wav"`, `"pcm"` | Output format |
| `sample_rate` | integer | Optional output sample rate |
| `mp3_bitrate` | `64`, `128`, `192` | MP3 bitrate |
| `latency` | `"normal"`, `"balanced"` | TTS latency mode |
| `chunk_length` / `min_chunk_length` | integer | Chunking controls |
| `temperature`, `top_p`, `repetition_penalty` | number | Sampling controls |
| `max_new_tokens` | integer | Maximum generated tokens |
| `normalize` | boolean | Normalize generated audio |
| `prosody` | object | Prosody tuning |
| `references` | array | One-shot voice clone sample; exactly one object with `audio` (public HTTPS MP3/WAV URL) and `text` (accurate transcript); mutually exclusive with `reference_id` |
| `callback_url` | string | Async callback URL |
| `async` | boolean | Run asynchronously and poll `/fish/tasks` |

## Gotchas

- The documented TTS endpoint is `POST /fish/tts` — not `/fish/audios`.
- Choose the Fish engine with the **`model` request header**, not a JSON `model` field.
- Use `reference_id` from `GET /fish/model` — not `voice_id`; pass `references` only for one-shot cloning from a temporary reference audio sample.
- `references` accepts HTTPS audio URLs only, not Base64, data URIs, MessagePack, local files, or credentialed URLs.
- Synchronous requests return `audio_url` directly; async jobs should be polled via `/fish/tasks`.

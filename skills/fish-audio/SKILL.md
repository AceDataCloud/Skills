---
name: fish-audio
description: Generate AI text-to-speech audio, use saved voices, or create a one-shot voice clone from an HTTPS reference audio URL and exact transcript via AceDataCloud API.
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

Use a temporary reference voice without creating a persistent model:

```json
POST /fish/tts
Headers:
  model: s2-pro

{
  "text": "New speech in the referenced voice.",
  "format": "mp3",
  "references": [{
    "audio": "https://cdn.acedata.cloud/reference.mp3",
    "text": "The exact words spoken in the reference audio."
  }]
}
```

`audio` must be a public HTTPS MP3/WAV URL and `text` must be the exact transcript. Use one reference lasting 10–270 seconds. Do not combine `references` with `reference_id`; use `reference_id` when the same saved/public voice will be reused. Raw bytes, Base64, data URIs, and MessagePack are not accepted by the AceDataCloud endpoint.

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
| `reference_id` | string | Public/reference voice ID from `GET /fish/model` |
| `format` | `"mp3"`, `"wav"`, `"pcm"` | Output format |
| `sample_rate` | integer | Optional output sample rate |
| `mp3_bitrate` | `64`, `128`, `192` | MP3 bitrate |
| `latency` | `"normal"`, `"balanced"` | TTS latency mode |
| `chunk_length` / `min_chunk_length` | integer | Chunking controls |
| `temperature`, `top_p`, `repetition_penalty` | number | Sampling controls |
| `max_new_tokens` | integer | Maximum generated tokens |
| `normalize` | boolean | Normalize generated audio |
| `prosody` | object | Prosody tuning |
| `references` | array | One `{audio, text}` object for a one-shot voice clone; mutually exclusive with `reference_id` |
| `callback_url` | string | Async callback URL |
| `async` | boolean | Run asynchronously and poll `/fish/tasks` |

## Gotchas

- The documented TTS endpoint is `POST /fish/tts` — not `/fish/audios`.
- Choose the Fish engine with the **`model` request header**, not a JSON `model` field.
- Use `reference_id` from `GET /fish/model` — not `voice_id`.
- Use `references` for a one-shot clone that is not saved as a model.
- Billing is based on the target text UTF-8 byte count; the reference audio does not add a separate clone fee.
- Synchronous requests return `audio_url` directly; async jobs should be polled via `/fish/tasks`.

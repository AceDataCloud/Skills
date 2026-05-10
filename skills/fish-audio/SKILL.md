---
name: fish-audio
description: Generate AI audio and synthesize voices with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, synthesizing voices, or generating audio content. Supports multiple voice models and TTS capabilities.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Fish Audio — Voice & Audio Synthesis

Generate AI audio and synthesize voices through AceDataCloud's Fish Audio API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** `POST /fish/tts` supports `callback_url` and returns `{task_id, started_at}` immediately; then your webhook receives the final result with `audio_url`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Fish Audio-compatible TTS (primary endpoint) |
| `POST /fish/model` | Create a cloned voice model from sample URLs |
| `GET /fish/model` | List voice models with pagination/filtering |
| `POST /fish/audios` | Legacy text-to-speech endpoint |
| `POST /fish/voices` | Legacy voice cloning endpoint |
| `POST /fish/tasks` | Poll legacy async tasks |

## Workflows

### 1. Text-to-Speech (`/fish/tts`)

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3",
  "sample_rate": 44100
}
```

Select TTS model with HTTP header `model: s1` or `model: s2-pro` (default `s2-pro`).

### 2. Voice Cloning — Create Model (`/fish/model`)

Upload a reference audio to create a cloneable voice.

```json
POST /fish/model
{
  "title": "My Custom Voice",
  "description": "Clear, neutral-toned speaker for TTS",
  "voices": ["https://example.com/reference-voice.mp3"],
  "cover_image": "https://example.com/avatar.jpg",
  "visibility": "private"
}
```

### 3. List Voice Models (`GET /fish/model`)

```json
GET /fish/model?page_size=10&page_number=1&self=true
```

## Parameters

### `/fish/tts` (primary)

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize |
| `reference_id` | string | Cloned voice ID from `POST /fish/model` |
| `references` | array | Multi-reference voice inputs (Fish-compatible) |
| `prosody` | object | Prosody controls (Fish-compatible) |
| `format` | string | Output format such as `mp3` |
| `sample_rate` | integer | Output sample rate |
| `mp3_bitrate` | integer | MP3 bitrate |
| `chunk_length` | integer | Chunk length for synthesis |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Nucleus sampling |
| `callback_url` | string | Async callback URL (platform extension) |

### `/fish/tts` Headers

| Header | Values | Description |
|--------|--------|-------------|
| `model` | `s1`, `s2-pro` | TTS model for `/fish/tts` (default `s2-pro`) |

### `/fish/model` (voice clone models)

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Display title for cloned model |
| `voices` | array of strings | Sample audio URLs (required for create) |
| `description` | string | Description of the voice model |
| `cover_image` | string | Cover image URL |
| `visibility` | string | Visibility such as `private` |

`GET /fish/model` query params include `page_size`, `page_number`, `title`, `tag`, `self`, `author_id`, `language`, `title_language`.

### Legacy `/fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID |
| `ids` | array | Batch task IDs |
| `action` | string | `retrieve` or `retrieve_batch` |

## Gotchas

- Pricing is based on **byte count** of the generated audio
- `POST /fish/tts` is Fish Audio-compatible and uses `Authorization: Bearer ...` instead of Fish official keys
- `POST /fish/tts` model is selected via HTTP header `model`, not request body
- `callback_url` on `/fish/tts` is a platform extension for async webhook delivery
- Create/list clone models via `/fish/model`; use returned `_id` as `reference_id` in `/fish/tts`
- Legacy `/fish/audios` and `/fish/voices` still exist for backward compatibility

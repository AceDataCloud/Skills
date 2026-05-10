---
name: fish-audio
description: Generate AI audio and synthesize voices with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, synthesizing voices, managing voice models, or generating audio content. Supports multiple voice models, TTS capabilities, Fish Audio-compatible TTS, and voice model management.
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

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"task_id": "..."}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Fish Audio-compatible TTS (returns `audio_url` directly) |
| `POST /fish/audios` | Generate audio from text or parameters |
| `POST /fish/voices` | Voice synthesis and cloning |
| `POST /fish/model` | Create a cloned voice model from reference audio URLs |
| `GET /fish/model` | List available voice models |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech (Fish Audio-compatible)

The `/fish/tts` endpoint is fully compatible with the Fish Audio official API. Migrate existing Fish Audio code by swapping the URL and token.

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog.",
    "format": "mp3",
    "sample_rate": 44100
  }'
```

Response:

```json
{
  "audio_url": "https://platform.r2.fish.audio/task/8a72ff9840234006a9f74cb2fa04f978.mp3"
}
```

### 2. TTS with Cloned Voice

Use a cloned voice model by passing its `_id` as `reference_id`:

```json
POST /fish/tts
{
  "text": "Welcome to our platform.",
  "reference_id": "<model _id from POST /fish/model>",
  "format": "mp3"
}
```

Header: `model: s2-pro`

### 3. Text-to-Speech (Legacy)

```json
POST /fish/audios
{
  "prompt": "The quick brown fox jumps over the lazy dog.",
  "voice_id": "default"
}
```

### 4. Voice Cloning — Register a Voice

Upload a reference audio to create a cloneable voice (legacy endpoint).

```json
POST /fish/voices
{
  "voice_url": "https://example.com/reference-voice.mp3",
  "title": "My Custom Voice",
  "description": "Clear, neutral-toned speaker for TTS",
  "image_url": "https://example.com/avatar.jpg"
}
```

### 5. Create a Voice Model (Fish Model API)

Create a cloned voice model from reference audio sample URLs. The returned `_id` can be used as `reference_id` in `/fish/tts`.

```bash
curl -X POST https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Cloned Voice",
    "description": "Cloned from a podcast recording",
    "voices": ["https://example.com/sample-voice.mp3"],
    "visibility": "private"
  }'
```

Response:

```json
{
  "_id": "d7900c21663f485ab63ebdb7e5905036",
  "type": "tts",
  "title": "My Cloned Voice",
  "state": "trained",
  "languages": ["zh", "en"],
  "visibility": "private"
}
```

### 6. List Voice Models

```bash
curl -G https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --data-urlencode 'page_size=10' \
  --data-urlencode 'self=true'
```

## Parameters

### `/fish/tts`

Model is specified via an HTTP header, not the request body.

| Header/Parameter | Type | Description |
|-----------------|------|-------------|
| `model` (header) | string | TTS model: `s1` or `s2-pro` (default: `s2-pro`) |
| `text` | string | Text to synthesize |
| `reference_id` | string | Cloned voice model `_id` to use |
| `references` | array | Reference audio objects for voice cloning |
| `format` | string | Output format: `mp3`, `wav`, `opus`, etc. |
| `sample_rate` | integer | Audio sample rate in Hz |
| `mp3_bitrate` | integer | MP3 bitrate |
| `latency` | string | Latency mode (default: `normal`) |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Nucleus sampling |
| `chunk_length` | integer | Chunk length for streaming |
| `callback_url` | string | Webhook for async delivery; returns `{task_id, started_at}` immediately |

### `/fish/model` (POST — create)

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Display name for the voice model (required) |
| `voices` | array | List of audio sample URLs (required; 30s+ per file recommended) |
| `description` | string | Description of the voice |
| `cover_image` | string | Cover image URL |
| `visibility` | string | `private` or `public` |

### `/fish/model` (GET — list)

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Items per page (default: 10) |
| `page_number` | integer | Page number starting from 1 |
| `title` | string | Fuzzy search by title |
| `tag` | string | Filter by tag |
| `self` | boolean | `true` to return only your own models |
| `author_id` | string | Filter by creator |
| `language` | string | Filter by voice language |
| `title_language` | string | Filter by title language |

### `/fish/audios`

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Text to synthesize into speech |
| `voice_id` | string | Voice model or cloned voice ID to use |
| `model` | string | TTS model (e.g., `"speech-1.5"`, `"speech-1.5-hd"`) |
| `action` | string | Operation type (e.g., `"generate"`) |
| `callback_url` | string | Webhook URL for async delivery |

### `/fish/voices`

| Parameter | Type | Description |
|-----------|------|-------------|
| `voice_url` | string | Reference audio URL for voice cloning |
| `title` | string | Display title for the cloned voice |
| `description` | string | Description of the voice |
| `image_url` | string | Cover image URL for the voice |
| `callback_url` | string | Webhook URL for async delivery |

## Gotchas

- **`/fish/tts`** is the Fish Audio-compatible endpoint — migrate existing Fish Audio projects by changing the URL and token only
- **`/fish/tts` model** is specified in the HTTP header (`model: s2-pro`), not the request body
- **`/fish/tts` latency**: defaults to `normal` automatically if omitted (Fish official requires it; this platform fills it in)
- **`/fish/tts` async**: provide `callback_url` to get `{task_id, started_at}` immediately; the full result is POSTed to the callback URL on completion
- **`/fish/model` billing**: only `POST /fish/model` with `voices` field is billed; `GET /fish/model` is free
- **`/fish/model` voices**: submit audio sample URLs (JSON only); files of 30s+ and 16kHz+ sample rate recommended
- Pricing for `/fish/audios` is based on **byte count** of the generated audio
- Voice cloning requires a clear reference audio sample
- Text-to-speech supports multiple languages automatically

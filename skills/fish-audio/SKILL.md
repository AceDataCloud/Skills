---
name: fish-audio
description: Generate AI audio and synthesize voices with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, synthesizing voices, cloning voices, or managing voice models. Supports multiple voice models and TTS capabilities.
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
| `POST /fish/tts` | Text-to-speech (Fish Audio official API compatible) |
| `POST /fish/model` | Create a cloned voice model |
| `GET /fish/model` | List available voice models |
| `POST /fish/audios` | Generate audio from text or parameters |
| `POST /fish/voices` | Voice synthesis and cloning |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
Headers: { "model": "s2-pro" }
{
  "text": "The quick brown fox jumps over the lazy dog."
}
```

Response:
```json
{
  "audio_url": "https://platform.r2.fish.audio/task/8a72ff9840234006a9f74cb2fa04f978.mp3"
}
```

### 2. Text-to-Speech with Cloned Voice

Use a `reference_id` obtained from `POST /fish/model` to apply a cloned voice:

```json
POST /fish/tts
Headers: { "model": "s2-pro" }
{
  "text": "Welcome to our platform.",
  "reference_id": "<_id from POST /fish/model>",
  "format": "mp3",
  "sample_rate": 44100
}
```

### 3. Async TTS with Callback

For long texts, use `callback_url` to receive the result asynchronously:

```json
POST /fish/tts
{
  "text": "A long passage...",
  "callback_url": "https://your-server.example.com/webhook"
}
```

Returns immediately:
```json
{ "task_id": "2725a2d3-...", "started_at": "2025-05-09T12:34:56.789Z" }
```

The callback URL receives the completed audio once ready:
```json
{ "task_id": "2725a2d3-...", "audio_url": "https://..." }
```

### 4. Create a Cloned Voice Model

Upload reference audio URLs to train a custom voice:

```json
POST /fish/model
{
  "title": "My Custom Voice",
  "description": "Podcast recording clone",
  "voices": ["https://example.com/sample-voice.mp3"],
  "cover_image": "https://example.com/cover.png",
  "visibility": "private"
}
```

Response includes `_id`, which can be used as `reference_id` in `POST /fish/tts`.

### 5. List Voice Models

```bash
GET /fish/model?page_size=10&page_number=1&self=true
```

### 6. Legacy Audio Generation

```json
POST /fish/audios
{
  "prompt": "Hello world.",
  "voice_id": "default"
}
```

### 7. Legacy Voice Cloning — Register a Voice

```json
POST /fish/voices
{
  "voice_url": "https://example.com/reference-voice.mp3",
  "title": "My Custom Voice",
  "description": "Clear, neutral-toned speaker for TTS",
  "image_url": "https://example.com/avatar.jpg"
}
```

## Parameters

### `/fish/tts` (POST)

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string | Cloned voice model `_id` from `POST /fish/model` |
| `references` | array | Reference audio list for few-shot voice cloning |
| `format` | string | Output format (`mp3`, `wav`, etc.) |
| `sample_rate` | integer | Audio sample rate (e.g., `44100`) |
| `mp3_bitrate` | integer | MP3 bitrate |
| `prosody` | object | Prosody control settings |
| `callback_url` | string | Async callback URL; returns `task_id` immediately |

> **Header:** Pass `model: s1` or `model: s2-pro` (default `s2-pro`) to select the TTS model.

### `/fish/model` (POST)

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Voice model title (required) |
| `voices` | array | Audio sample URLs for training (required, ≥30 s each recommended) |
| `description` | string | Description of the voice |
| `cover_image` | string | Cover image URL |
| `visibility` | string | `"private"` or `"public"` |

### `/fish/model` (GET)

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Results per page (default 10) |
| `page_number` | integer | Page number (1-based) |
| `title` | string | Fuzzy search by title |
| `tag` | string | Filter by tag |
| `self` | boolean | `true` to return only your own models |
| `author_id` | string | Filter by creator |
| `language` | string | Filter by voice language |

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

- `POST /fish/tts` is fully compatible with the Fish Audio official API; only the auth and base URL differ
- `POST /fish/model` is billed only when `voices` is provided; `GET /fish/model` is free
- The `_id` returned from `POST /fish/model` can be used directly as `reference_id` in `POST /fish/tts`
- `POST /fish/model` accepts audio via URLs only (not binary upload); recommended sample length ≥ 30 s, sample rate ≥ 16 kHz
- `/fish/tts` automatically sets `latency=normal` when not specified, matching Fish Audio default behavior
- For long texts, use `callback_url` to avoid holding an open connection
- Pricing is based on **byte count** of the generated audio
- Text-to-speech supports multiple languages automatically

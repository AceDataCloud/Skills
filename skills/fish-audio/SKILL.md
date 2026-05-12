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
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "..."}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Text-to-speech synthesis |
| `GET /fish/model` | List available voice models |
| `GET /fish/model/{id}` | Get a single voice model |
| `POST /fish/model` | Create a voice clone |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
Headers: model: s2-pro
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "format": "mp3"
}
```

### 2. Text-to-Speech with a Specific Voice

Use a `reference_id` to speak in a cloned or community voice.

```json
POST /fish/tts
Headers: model: s2-pro
{
  "text": "Welcome to our platform.",
  "reference_id": "<voice_model_id>",
  "format": "mp3"
}
```

### 3. List Available Voice Models

```bash
GET /fish/model?page_size=10&page_number=1
```

### 4. Create a Voice Clone

```json
POST /fish/model
{
  "title": "My Custom Voice",
  "voices": "https://example.com/reference-voice.mp3"
}
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `format` | string | Output audio format: `"mp3"` or `"pcm"` (default: `mp3`) |
| `reference_id` | string | Voice model ID for single-speaker synthesis |
| `sample_rate` | integer | Output audio sampling rate (e.g. 16000, 44100) |
| `mp3_bitrate` | integer | MP3 bit rate when `format=mp3` |
| `latency` | string | Latency mode (default: `normal`) |
| `temperature` | number | Sampling temperature (0.0–1.0) |
| `top_p` | number | Top-p nucleus sampling parameter |
| `normalize` | boolean | Whether to apply text normalization |
| `callback_url` | string | Webhook URL for async delivery |

**Request headers:**
| Header | Values | Description |
|--------|--------|-------------|
| `model` | `s1`, `s2-pro` | TTS model to use (default: `s2-pro`) |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Number of items per page (default: 10) |
| `page_number` | integer | 1-based page number (default: 1) |
| `title` | string | Filter by partial title match |
| `tag` | string | Filter by a single tag |
| `self` | boolean | Only return models owned by the calling account |
| `language` | string | Filter by language code (e.g. `en`, `zh`) |
| `sort_by` | string | Sort by field (e.g. `created_at`, `task_count`) |

### `POST /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Display title for the cloned voice |
| `voices` | string | Single reference audio URL for voice cloning |

## Gotchas

- The TTS endpoint is `POST /fish/tts` with `text` (not `prompt`) as the input field
- The TTS model is passed via the **`model` request header** (`s1` or `s2-pro`), not in the request body
- Valid `format` values are `mp3` and `pcm` only — other formats are not accepted
- To use a cloned voice, pass the voice model ID as `reference_id` in the TTS request
- Task polling uses `id` (not `task_id`) in the `/fish/tasks` request body
- Voice model URLs returned by `GET /fish/model/{id}` are signed R2 URLs valid for ~1 hour

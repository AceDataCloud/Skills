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
curl -X POST https://api.acedata.cloud/fish/audios \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"task_id": "..."}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/audios` | Generate audio from text or parameters |
| `POST /fish/voices` | Voice synthesis and cloning |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/audios
{
  "prompt": "The quick brown fox jumps over the lazy dog.",
  "voice_id": "d7900c21663f485ab63ebdb7e5905036"
}
```

### 2. Voice Cloning — Register a Voice

Upload a reference audio to create a cloneable voice.

```json
POST /fish/voices
{
  "voice_url": "https://example.com/reference-voice.mp3",
  "title": "My Custom Voice",
  "description": "Clear, neutral-toned speaker for TTS",
  "image_url": "https://example.com/avatar.jpg"
}
```

### 3. Text-to-Speech with Cloned Voice

```json
POST /fish/audios
{
  "prompt": "Welcome to our platform.",
  "voice_id": "<voice_id from POST /fish/voices>"
}
```

## Parameters

### `/fish/audios`

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Text to synthesize into speech |
| `voice_id` | string | Voice model or cloned voice ID to use (default: `"d7900c21663f485ab63ebdb7e5905036"`) |
| `model` | string | TTS model: `"fish-tts"` |
| `action` | string | Operation type: `"speech"` |
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

- Pricing is based on **byte count** of the generated audio
- Voice cloning requires a clear reference audio sample
- Text-to-speech supports multiple languages automatically
- Use the `/fish/voices` endpoint to register a reference audio and receive a `voice_id` for TTS

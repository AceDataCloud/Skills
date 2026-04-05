---
name: fish-audio
description: Generate AI audio and synthesize voices with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, synthesizing voices, or generating audio content. Supports multiple voice models and TTS capabilities.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable.
---

# Fish Audio — Voice & Audio Synthesis

Generate AI audio and synthesize voices through AceDataCloud's Fish Audio API.

## Authentication

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/audios \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, this is a demonstration of AI voice synthesis."}'
```

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
  "voice_id": "default"
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
| `voice_id` | string | Voice model to use |
| `model` | string | Model for voice cloning |
| `action` | string | Operation type |
| `callback_url` | string | Webhook URL for async delivery |

### `/fish/voices`

| Parameter | Type | Description |
|-----------|------|-------------|
| `voice_url` | string | Reference audio URL for voice cloning |
| `title` | string | Display title for the cloned voice |
| `description` | string | Description of the voice |
| `image_url` | string | Cover image URL for the voice |
| `callback_url` | string | Webhook URL for async delivery |

## Task Polling

```json
POST /fish/tasks
{"task_id": "your-task-id"}
```

## Response

```json
{
  "task_id": "abc123",
  "audio_url": "https://cdn.example.com/output.mp3",
  "success": true
}
```

## Gotchas

- Pricing is based on **byte count** of the generated audio
- Voice cloning requires a clear reference audio sample
- Text-to-speech supports multiple languages automatically
- Use the `/fish/voices` endpoint to register a reference audio and receive a `voice_id` for TTS

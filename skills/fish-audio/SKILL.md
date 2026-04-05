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
  -d '{"action": "speech", "model": "fish-tts", "prompt": "Hello, this is a demonstration of AI voice synthesis."}'
```

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/audios` | Generate audio from text |
| `POST /fish/voices` | Register a custom voice profile |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/audios
{
  "action": "speech",
  "model": "fish-tts",
  "prompt": "The quick brown fox jumps over the lazy dog.",
  "voice_id": "d7900c21663f485ab63ebdb7e5905036"
}
```

### 2. Register a Custom Voice

Upload a reference audio to create a custom voice profile.

```json
POST /fish/voices
{
  "voice_url": "https://example.com/reference-voice.mp3",
  "title": "My Custom Voice",
  "description": "A custom voice profile",
  "image_url": "https://example.com/cover.jpg"
}
```

## Parameters

### `/fish/audios`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Must be `"speech"` |
| `model` | string | Yes | Must be `"fish-tts"` |
| `prompt` | string | Yes | Text to synthesize into speech |
| `voice_id` | string | No | Voice model ID to use |
| `callback_url` | string | No | Async callback URL |

### `/fish/voices`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `voice_url` | string | No | Reference audio URL for voice cloning |
| `title` | string | No | Title of the voice profile |
| `description` | string | No | Description of the voice profile |
| `image_url` | string | No | Cover image URL for the voice profile |
| `callback_url` | string | No | Async callback URL |

## Task Polling

```json
POST /fish/tasks
{"id": "your-task-id", "action": "retrieve"}
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
- Use the `/fish/voices` endpoint to register a voice profile before using a custom `voice_id`

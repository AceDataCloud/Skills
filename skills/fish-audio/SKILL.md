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
  -H "model: s2-pro" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id":"...", "action":"retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Fish-compatible text-to-speech |
| `GET /fish/model` | Paginated voice model query |
| `GET /fish/model/{id}` | Get one voice model by ID |
| `POST /fish/tasks` | Poll async task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3",
  "sample_rate": 44100
}
```

### 2. List Voice Models

```json
GET /fish/model?page_size=10&page_number=1&self=true
```

### 3. Get Voice Model Detail

```json
GET /fish/model/{id}
```

### 4. Poll Async Result

```json
POST /fish/tasks
{
  "id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
  "action": "retrieve"
}
```

## Parameters

### `/fish/tts` body

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (**required**) |
| `reference_id` | string | Voice model ID for cloned voice synthesis |
| `format` | string | Audio format: `mp3`, `wav`, `pcm`, `opus` |
| `sample_rate` | integer | Output sample rate (e.g. 16000, 22050, 44100) |
| `latency` | string | `normal` or `balanced` |
| `references` | array | Inline reference samples passed to Fish upstream |
| `prosody` | object | Prosody controls passed to Fish upstream |
| `callback_url` | string | Optional webhook URL for async callback (`task_id`) |

### `/fish/tts` headers

| Parameter | Type | Description |
|-----------|------|-------------|
| `Authorization` | string | `Bearer <ACEDATACLOUD_API_TOKEN>` |
| `model` | string | Fish TTS model: `s1` or `s2-pro` (default `s2-pro`) |

### `/fish/model` query

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Items per page |
| `page_number` | integer | Page number (starts at 1) |
| `title` | string | Fuzzy title filter |
| `tag` | string | Tag filter |
| `self` | boolean | Return only current account's voices |
| `author_id` | string | Filter by creator |
| `language` | string | Filter by language |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sort rule |

### `/fish/tasks` body

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | `retrieve` (single) or `retrieve_batch` (batch) |
| `id` | string | One task ID (for `retrieve`) |
| `ids` | array | Task IDs (for `retrieve_batch`) |

## Gotchas

- Fish-compatible TTS uses `POST /fish/tts` (not `/fish/audios`)
- Voice model discovery/detail uses `GET /fish/model` and `GET /fish/model/{id}`
- For async callback mode, `POST /fish/tts` returns `task_id` immediately; then poll via `POST /fish/tasks`
- Task polling payload uses `id`/`ids` with `action`, not `task_id`

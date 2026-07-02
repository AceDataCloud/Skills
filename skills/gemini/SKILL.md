---
name: gemini
description: Access Google Gemini models via AceDataCloud API. Use when making OpenAI-compatible chat completions with Gemini models, calling the native Gemini generateContent API, or generating short videos with the omni-flash model. Supports streaming, tool calling, and multimodal input.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Gemini — Google AI via AceDataCloud

Access Google Gemini models through AceDataCloud. Supports the OpenAI-compatible `/gemini/chat/completions` endpoint, the native `/v1beta/models/{model}:generateContent` endpoint, and video generation via `/gemini/videos`.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/gemini/chat/completions \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.1-pro",
    "messages": [{"role": "user", "content": "Explain quantum entanglement in simple terms."}]
  }'
```

> **Async (video only):** See [async task polling](../_shared/async-tasks.md). Poll via `POST /gemini/tasks` with `{"id": "..."}`.

## Models

### Chat / Text

| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` | Latest flagship, highest quality |
| `gemini-3.1-flash-lite-preview` | Fast lightweight preview |
| `gemini-3.1-flash-image` | Multimodal with image understanding |
| `gemini-3.0-pro` | Stable high-quality |
| `gemini-3.5-flash` | Fast general-purpose |
| `gemini-3-flash-preview` | Flash preview |
| `gemini-3-pro-image` | Pro with image capabilities |
| `gemini-2.5-pro` | Proven pro model |
| `gemini-2.5-flash` | Fast 2.5 model |
| `gemini-2.5-flash-lite` | Lightweight 2.5 |
| `gemini-2.5-flash-image` | 2.5 with image capabilities |
| `gemini-2.0-flash` | Stable 2.0 model |

### Video

| Model | Best For |
|-------|----------|
| `omni-flash` | Short video generation from text or image |

## Workflows

### 1. OpenAI-Compatible Chat

Standard OpenAI-style request via the `/gemini/chat/completions` endpoint.

```json
POST /gemini/chat/completions
{
  "model": "gemini-3.1-pro",
  "messages": [
    {"role": "user", "content": "Write a haiku about machine learning."}
  ],
  "stream": false,
  "temperature": 0.7
}
```

With streaming:

```json
POST /gemini/chat/completions
{
  "model": "gemini-3.5-flash",
  "messages": [{"role": "user", "content": "Tell me a story."}],
  "stream": true
}
```

### 2. Native Gemini API

Call the native Gemini `generateContent` endpoint directly.

```json
POST /v1beta/models/gemini-3.1-pro:generateContent
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "Describe this scene."}]
    }
  ],
  "generationConfig": {
    "temperature": 0.9,
    "maxOutputTokens": 1024
  }
}
```

Multimodal with inline image data:

```json
POST /v1beta/models/gemini-3.1-flash-image:generateContent
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "What is in this image?"},
        {
          "inlineData": {
            "mimeType": "image/jpeg",
            "data": "<base64-encoded-image>"
          }
        }
      ]
    }
  ]
}
```

Streaming version:

```bash
POST /v1beta/models/gemini-3.5-flash:streamGenerateContent
```
(same body as `generateContent`)

### 3. Video Generation

Generate short videos from text or images using the `omni-flash` model.

```json
POST /gemini/videos
{
  "prompt": "a hummingbird hovering near a red flower in slow motion",
  "model": "omni-flash",
  "aspect_ratio": "16:9"
}
```

Image-to-video:

```json
POST /gemini/videos
{
  "prompt": "the scene gently comes alive",
  "model": "omni-flash",
  "image_urls": ["https://example.com/scene.jpg"],
  "aspect_ratio": "9:16"
}
```

## Parameters

### `/gemini/chat/completions`

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Gemini model name (see Models table) |
| `messages` | array | Standard OpenAI chat messages |
| `stream` | boolean | Enable SSE streaming |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Nucleus sampling |
| `max_tokens` | number | Maximum output tokens |
| `reasoning_effort` | string | `minimal`, `low`, `medium`, `high` |
| `service_tier` | string | `auto`, `default`, `flex`, `scale`, `priority` |
| `tools` / `tool_choice` | array / string | Function-calling |

### `/gemini/videos`

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `prompt` | Yes | string | Video description |
| `model` | No | string | `omni-flash` (default) |
| `aspect_ratio` | No | string | `16:9` (default) or `9:16` |
| `image_urls` | No | array of URLs | Reference images for image-to-video |
| `callback_url` | No | string (URL) | Webhook called when task completes |
| `async` | No | boolean | Return task ID immediately (default: true) |

## Polling Tasks (Video)

```json
POST /gemini/tasks
{
  "action": "retrieve",
  "id": "<task_id>"
}
```

Batch:

```json
POST /gemini/tasks
{
  "action": "retrieve_batch",
  "ids": ["<task_id_1>", "<task_id_2>"]
}
```

## Gotchas

- The `/gemini/chat/completions` endpoint is OpenAI-compatible — you can use the OpenAI SDK with `base_url="https://api.acedata.cloud/gemini"`.
- Native endpoint path format: `/v1beta/models/{model_name}:generateContent` — put the model name in the URL path.
- Video generation via `/gemini/videos` is async — poll `/gemini/tasks` for results.
- Only `omni-flash` is available for video generation.
- Gemini models are also accessible via the unified `/aichat/conversations` endpoint (see [ai-chat](../ai-chat/SKILL.md)).

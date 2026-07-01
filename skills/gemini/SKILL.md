---
name: gemini
description: Use Google Gemini through AceDataCloud's native Gemini APIs for chat completions, Gemini generateContent calls, streaming responses, and Omni video generation. Supports Gemini 2.0, 2.5, 3.0, 3.1, and 3.5 model variants plus `omni-flash` for video.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Gemini Native APIs

Use AceDataCloud's Gemini-native endpoints when you need the **Gemini API surface**
rather than the unified `ai-chat` gateway.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

### OpenAI-compatible Gemini chat

```bash
curl -X POST https://api.acedata.cloud/gemini/chat/completions \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-3.1-pro","messages":[{"role":"user","content":"Summarize the latest Gemini features."}]}'
```

### Native Gemini `generateContent`

```bash
curl -X POST 'https://api.acedata.cloud/v1beta/models/gemini-2.5-flash:generateContent' \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Explain function calling in Gemini."}]}]}'
```

### Gemini video generation

```bash
curl -X POST https://api.acedata.cloud/gemini/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"cinematic drone shot above a waterfall at sunrise","model":"omni-flash","aspect_ratio":"16:9","async":true}'
```

> **Async:** Poll Gemini video tasks via `POST /gemini/tasks` with `{"id":"..."}` or batch-retrieve with `{"ids":["..."],"action":"retrieve_batch"}`.

## Endpoints

| Endpoint | Use For |
|----------|---------|
| `POST /gemini/chat/completions` | OpenAI-style Gemini chat completions |
| `POST /v1beta/models/{model}:generateContent` | Native Gemini content generation |
| `POST /v1beta/models/{model}:streamGenerateContent?alt=sse` | Native streaming Gemini responses |
| `POST /gemini/videos` | Gemini Omni text/image-to-video generation |
| `POST /gemini/tasks` | Poll Gemini video task results |

## Current Documented Models

### Chat / Generate Content

`gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`,
`gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3.5-flash`,
`gemini-3.0-pro`, `gemini-3.1-pro`, `gemini-3.1-flash-lite-preview`,
`gemini-3.1-flash-image-preview`, `gemini-2.5-flash-image`,
`gemini-3-pro-image-preview`

### Video

`omni-flash`

## Workflows

### 1. Chat completions

```json
POST /gemini/chat/completions
{
  "model": "gemini-3.5-flash",
  "messages": [
    {"role": "system", "content": "Be concise."},
    {"role": "user", "content": "Draft a launch announcement."}
  ],
  "temperature": 0.7,
  "stream": true,
  "tools": []
}
```

Useful parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | One of the documented Gemini chat models |
| `messages` | array | OpenAI-format chat messages |
| `stream` | boolean | Enable streaming output |
| `temperature`, `top_p` | number | Sampling controls |
| `max_tokens`, `max_completion_tokens` | integer | Output cap |
| `tools`, `tool_choice`, `parallel_tool_calls` | array / object / boolean | Tool-calling controls |
| `reasoning_effort` | string | `minimal`, `low`, `medium`, or `high` |
| `service_tier` | string | `auto`, `default`, `flex`, `scale`, or `priority` |
| `modalities`, `audio` | array / object | Multimodal output controls |

### 2. Native `generateContent`

```json
POST /v1beta/models/gemini-2.5-pro:generateContent
{
  "contents": [
    {
      "parts": [
        {"text": "Describe the tradeoffs between RAG and fine-tuning."}
      ]
    }
  ],
  "systemInstruction": {
    "parts": [
      {"text": "Answer in bullet points."}
    ]
  }
}
```

Useful parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` (path) | string | Required Gemini model name in the URL path |
| `contents` | array | Required Gemini-native message/content structure |
| `systemInstruction` | object | Optional system prompt |
| `generationConfig` | object | Generation tuning |
| `tools`, `toolConfig` | array / object | Native tool-calling configuration |
| `safetySettings` | array | Safety overrides |
| `cachedContent` | string | Reuse cached content handle |

### 3. Streaming `streamGenerateContent`

Use the same request body as `generateContent`, but call:

```text
POST /v1beta/models/{model}:streamGenerateContent?alt=sse
```

The documented `alt` value is `sse`.

### 4. Gemini Omni video generation

```json
POST /gemini/videos
{
  "prompt": "a futuristic train gliding through a neon city at night",
  "model": "omni-flash",
  "aspect_ratio": "9:16",
  "image_urls": ["https://example.com/reference.jpg"],
  "callback_url": "https://example.com/webhook",
  "async": true
}
```

Useful parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Required video prompt |
| `model` | string | Video model (`omni-flash`) |
| `aspect_ratio` | string | `16:9` or `9:16` |
| `image_urls` | array | Optional reference images |
| `callback_url` | string | Optional webhook for async completion |
| `async` | boolean | Return immediately with a task ID |

### 5. Poll Gemini video tasks

```json
POST /gemini/tasks
{
  "id": "task_id_from_videos"
}
```

```json
POST /gemini/tasks
{
  "ids": ["task_a", "task_b"],
  "action": "retrieve_batch"
}
```

## Gotchas

- Use the `gemini` skill for Gemini-native APIs; use `ai-chat` for the cross-provider unified gateway.
- `generateContent` and `streamGenerateContent` put the model in the **URL path**, not the JSON body.
- Native Gemini requests require `contents`; OpenAI-style chat requests require `messages`.
- `streamGenerateContent` uses `alt=sse` for documented streaming output.
- `/gemini/videos` requires `prompt`; the only documented video model is `omni-flash`.
- Gemini video task polling uses `id` / `ids` on `POST /gemini/tasks`, with `action` values `retrieve` and `retrieve_batch`.

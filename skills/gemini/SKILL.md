---
name: gemini
description: Access Google Gemini models via AceDataCloud API. Use when you need OpenAI-compatible Gemini chat completions, native Gemini generateContent (with imageConfig/speechConfig), or AI video generation with omni-flash. Supports streaming, multimodal input, tool calling, and thinking budgets.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Gemini — Google AI via AceDataCloud

AceDataCloud exposes Google Gemini through three surfaces:

| Endpoint | Use For |
|----------|---------|
| `POST /gemini/chat/completions` | OpenAI-compatible chat completions |
| `POST /v1beta/models/{model}:generateContent` | Native Gemini generate-content API |
| `POST /v1beta/models/{model}:streamGenerateContent` | Native Gemini streaming generate-content |
| `POST /gemini/videos` | Video generation (omni-flash) |
| `POST /gemini/tasks` | Poll async video tasks |

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/gemini/chat/completions \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-3.1-pro","messages":[{"role":"user","content":"Explain transformers in one paragraph."}]}'
```

> **Async (video):** See [async task polling](../_shared/async-tasks.md). Poll via `POST /gemini/tasks` with `{"id": "..."}`.

## Models

### Chat Completions (`/gemini/chat/completions`)

| Model | Notes |
|-------|-------|
| `gemini-3.1-pro` | Latest flagship |
| `gemini-3.0-pro` | Previous flagship |
| `gemini-3.5-flash` | Fast, capable |
| `gemini-3-flash-preview` | Flash preview |
| `gemini-2.5-pro` | Stable pro |
| `gemini-2.5-flash` | Stable flash |
| `gemini-2.5-flash-lite` | Lightweight |
| `gemini-2.0-flash` | Legacy flash |
| `gemini-3.1-flash-lite-preview` | Lightest 3.1 |
| `gemini-3.1-flash-image` | Image-focused |
| `gemini-2.5-flash-image` | Image-focused |
| `gemini-3-pro-image` | Image-focused |

### Native API (`/v1beta/models/{model}:generateContent`)

Supports the same model list as chat completions above.

## OpenAI-Compatible Chat

```json
POST /gemini/chat/completions
{
  "model": "gemini-3.1-pro",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Summarize this image.", "image_url": "https://example.com/img.jpg"}
  ],
  "stream": false,
  "max_tokens": 1024
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (required) |
| `messages` | array | Standard OpenAI message list with multimodal support |
| `stream` | boolean | SSE streaming |
| `max_tokens` / `max_completion_tokens` | integer | Output cap |
| `temperature` / `top_p` | number | Sampling controls |
| `tools` / `tool_choice` | array / string | Function calling |
| `reasoning_effort` | string | Thinking depth |
| `service_tier` | string | Processing tier |
| `response_format` | object | JSON mode or structured output |

## Native Gemini API

Use the native `/v1beta` endpoints for Gemini-specific capabilities like `imageConfig`, `speechConfig`, and thinking budgets.

```json
POST /v1beta/models/gemini-3.1-flash-image:generateContent
{
  "contents": [
    {"role": "user", "parts": [{"text": "Generate an image of a sunset over mountains"}]}
  ],
  "generationConfig": {
    "imageConfig": {
      "aspectRatio": "16:9",
      "imageSize": "1K"
    }
  }
}
```

### `generationConfig` Options

| Field | Type | Description |
|-------|------|-------------|
| `temperature` / `topP` / `topK` | number | Sampling controls |
| `maxOutputTokens` | integer | Output cap |
| `responseMimeType` | string | e.g. `"application/json"` for structured output |
| `responseSchema` | object | JSON schema for structured output |
| `thinkingConfig.thinkingBudget` | integer | Token budget for reasoning |
| `imageConfig.aspectRatio` | string | Image aspect ratio |
| `imageConfig.imageSize` | string | `"512"`, `"1K"`, `"2K"`, or `"4K"` |
| `speechConfig` | object | Speech synthesis config |
| `responseModalities` | array | e.g. `["TEXT"]`, `["IMAGE"]` |

### Tool Use

```json
POST /v1beta/models/gemini-3.1-pro:generateContent
{
  "contents": [{"role": "user", "parts": [{"text": "What is the weather in London?"}]}],
  "tools": [{"functionDeclarations": [{"name": "get_weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}}]}],
  "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}}
}
```

## Video Generation

```json
POST /gemini/videos
{
  "prompt": "A time-lapse of a blooming flower",
  "model": "omni-flash",
  "aspect_ratio": "16:9",
  "image_urls": ["https://example.com/seed.jpg"],
  "async": true,
  "callback_url": "https://your-server.example.com/webhook"
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | ✓ | Video description |
| `model` | string | — | `omni-flash` (default) |
| `aspect_ratio` | string | — | e.g. `"16:9"`, `"9:16"` |
| `image_urls` | array | — | Seed images for image-to-video |
| `async` | boolean | — | Return task ID immediately |
| `callback_url` | string | — | Webhook for completion |

Poll results with:

```json
POST /gemini/tasks
{"id": "<task_id>"}
```

## Gotchas

- `/gemini/chat/completions` is OpenAI-compatible — you can use the OpenAI Python SDK pointing at `https://api.acedata.cloud/gemini`.
- Use image-focused models (`gemini-3.1-flash-image`, `gemini-2.5-flash-image`, `gemini-3-pro-image`) with `imageConfig` in `generationConfig` for image generation via the native API.
- `imageConfig.imageSize` values are `"512"`, `"1K"`, `"2K"`, `"4K"` — not pixel counts.
- `speechConfig` enables audio output on supported models.
- Video generation is always async — set `async: true` and poll `/gemini/tasks`.
- The `/v1beta/models/{model}:streamGenerateContent` endpoint mirrors `generateContent` but streams chunks via SSE.

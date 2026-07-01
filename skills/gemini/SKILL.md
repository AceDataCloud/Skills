---
name: gemini
description: Access Google Gemini models directly via AceDataCloud API. Use when you need OpenAI-compatible chat completions, native multimodal generateContent (text, images, thinking, grounding), streaming, or Gemini video generation. Supports Gemini 2.0–3.x model families including image-generation and flash-lite variants.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Gemini — Google AI via AceDataCloud

AceDataCloud exposes Google Gemini through three surfaces:

| Surface | Endpoint | Use For |
|---------|----------|---------|
| OpenAI-compatible | `POST /gemini/chat/completions` | Drop-in replacement for OpenAI chat calls |
| Native Gemini | `POST /v1beta/models/{model}:generateContent` | Full native API — multimodal, grounding, thinking |
| Native Gemini streaming | `POST /v1beta/models/{model}:streamGenerateContent` | Same as above, server-sent events |
| Video generation | `POST /gemini/videos` | Text / image-to-video with `omni-flash` |
| Task polling | `POST /gemini/tasks` | Retrieve async video results |

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

### OpenAI-compatible chat

```bash
curl -X POST https://api.acedata.cloud/gemini/chat/completions \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Explain quantum entanglement simply."}]
  }'
```

### Native generateContent

```bash
curl -X POST "https://api.acedata.cloud/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "What is the capital of France?"}]}]
  }'
```

## Models

### Chat / Text generation

| Model | Notes |
|-------|-------|
| `gemini-3.1-pro` | Latest flagship |
| `gemini-3.0-pro` | Previous flagship |
| `gemini-3.5-flash` | Fast, high quality |
| `gemini-3.1-flash-lite-preview` | Compact flash preview |
| `gemini-3-flash-preview` | Flash preview |
| `gemini-2.5-pro` | Pro reasoning |
| `gemini-2.5-flash` | Balanced (recommended default) |
| `gemini-2.5-flash-lite` | Smallest / fastest |
| `gemini-2.0-flash` | Previous generation flash |

### Image generation (use with native generateContent)

| Model | Notes |
|-------|-------|
| `gemini-3.1-flash-image` | Gemini 3.1 image generation |
| `gemini-2.5-flash-image` | Gemini 2.5 image generation |
| `gemini-3-pro-image` | Gemini 3 Pro image generation |

### Video generation

| Model | Notes |
|-------|-------|
| `omni-flash` | Gemini Omni Flash (video only) |

## Workflows

### 1. OpenAI-compatible Chat

```json
POST /gemini/chat/completions
{
  "model": "gemini-2.5-flash",
  "messages": [
    {"role": "system", "content": "You are a concise technical assistant."},
    {"role": "user", "content": "Summarize the main ideas in the theory of relativity."}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1024
}
```

Parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | One of the supported Gemini models |
| `messages` | array | OpenAI-format message list |
| `stream` | boolean | Enable SSE streaming |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Nucleus sampling |
| `max_tokens` / `max_completion_tokens` | integer | Output token cap |
| `seed` | integer | Reproducibility seed |
| `reasoning_effort` | string | `minimal`, `low`, `medium`, `high` (thinking models) |
| `service_tier` | string | `auto`, `default`, `flex`, `scale`, `priority` |
| `response_format` | object | Force JSON output — `{"type": "json_object"}` |
| `tools` / `tool_choice` | array / string-object | Function-calling |
| `web_search_options` | object | Enable grounded web search |

### 2. Native generateContent (multimodal / thinking / grounding)

```json
POST /v1beta/models/gemini-2.5-pro:generateContent
{
  "contents": [
    {
      "parts": [
        {"text": "Describe what you see in this image."},
        {"inlineData": {"mimeType": "image/jpeg", "data": "<base64>"}}
      ]
    }
  ],
  "systemInstruction": {
    "parts": [{"text": "Respond in bullet points."}]
  },
  "generationConfig": {
    "temperature": 0.4,
    "maxOutputTokens": 2048,
    "responseMimeType": "application/json",
    "thinkingConfig": {
      "includeThoughts": true,
      "thinkingBudget": 1024
    }
  }
}
```

`generationConfig` fields:

| Field | Type | Description |
|-------|------|-------------|
| `temperature` | number | Sampling temperature |
| `topP` | number | Nucleus sampling |
| `topK` | integer | Top-K sampling |
| `maxOutputTokens` | integer | Output token cap |
| `candidateCount` | integer | Number of response candidates |
| `seed` | integer | Reproducibility |
| `stopSequences` | array | Stop generation at these strings |
| `responseMimeType` | string | `text/plain` or `application/json` |
| `responseSchema` | object | JSON schema for structured output |
| `responseModalities` | array | e.g. `["TEXT"]`, `["IMAGE"]` |
| `presencePenalty` | number | Penalise repeated topics |
| `frequencyPenalty` | number | Penalise repeated tokens |
| `thinkingConfig` | object | `includeThoughts` (bool), `thinkingBudget` (int) |
| `imageConfig` | object | For image-generation models — see below |
| `speechConfig` | object | Speech output configuration |

`imageConfig` fields (for `*-image` models):

| Field | Type | Description |
|-------|------|-------------|
| `aspectRatio` | string | Target aspect ratio (e.g. `"16:9"`, `"1:1"`) |
| `imageSize` | string | Output resolution: `"512"`, `"1K"`, `"2K"`, `"4K"` |

### 3. Image Generation

Use a `*-image` model with `responseModalities: ["IMAGE"]` and `imageConfig`:

```json
POST /v1beta/models/gemini-2.5-flash-image:generateContent
{
  "contents": [{"parts": [{"text": "A photorealistic cat on a moonlit rooftop"}]}],
  "generationConfig": {
    "responseModalities": ["IMAGE"],
    "imageConfig": {
      "aspectRatio": "16:9",
      "imageSize": "2K"
    }
  }
}
```

### 4. Video Generation

```json
POST /gemini/videos
{
  "model": "omni-flash",
  "prompt": "A white ceramic mug on a marble counter, camera slowly orbiting 360°",
  "aspect_ratio": "16:9"
}
```

Or animate an image:

```json
POST /gemini/videos
{
  "model": "omni-flash",
  "prompt": "The cat blinks and stretches",
  "image_urls": ["https://example.com/cat.jpg"],
  "aspect_ratio": "9:16",
  "async": true
}
```

Video parameters:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `omni-flash` | Video generation model |
| `prompt` | string | Scene description |
| `aspect_ratio` | `16:9`, `9:16` | Output aspect ratio |
| `image_urls` | array | Source images for image-to-video |
| `callback_url` | string | Webhook for async delivery |
| `async` | boolean | Return `task_id` immediately |

### 5. Async Task Polling

```json
POST /gemini/tasks
{"id": "<task_id>"}
```

Or batch:

```json
POST /gemini/tasks
{"ids": ["<id1>", "<id2>"], "action": "retrieve_batch"}
```

> **Async:** See [async task polling](../_shared/async-tasks.md).

## Gotchas

- The OpenAI-compatible endpoint lives at `/gemini/chat/completions`, not `/openai/chat/completions` — use the correct base URL.
- Image-generation models (`*-image`) require `responseModalities: ["IMAGE"]` and `imageConfig` in `generationConfig`.
- `reasoning_effort` only affects thinking-enabled models (`gemini-2.5-pro`, `gemini-3.1-pro`, etc.).
- For streaming with the native API, use `/v1beta/models/{model}:streamGenerateContent`.
- `thinkingConfig.thinkingBudget` controls the maximum tokens the model spends thinking; set to 0 to disable thinking.

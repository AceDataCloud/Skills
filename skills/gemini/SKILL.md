---
name: gemini
description: Access Google Gemini models for chat completions and video generation via AceDataCloud. Use when you need Gemini-specific features — latest Gemini 3.x/2.x models, reasoning, vision, video generation — through an OpenAI-compatible API or the native Gemini API.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Gemini — Chat Completions & Video Generation

Access Google Gemini models through AceDataCloud's Gemini API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/gemini/chat/completions \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-pro", "messages": [{"role": "user", "content": "Explain quantum computing"}]}'
```

## Chat Completions (`POST /gemini/chat/completions`)

OpenAI-compatible chat completions endpoint for Gemini models.

### Models

| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` | Latest, highest capability |
| `gemini-3.0-pro` | Pro-tier generation |
| `gemini-3.5-flash` | Fast, cost-effective |
| `gemini-3-flash-preview` | Preview of next-generation flash |
| `gemini-2.5-pro` | Proven high capability with reasoning |
| `gemini-2.5-flash` | Balanced speed and quality |
| `gemini-2.0-flash` | Fast, efficient |

### Basic Chat

```json
POST /gemini/chat/completions
{
  "model": "gemini-2.5-pro",
  "messages": [
    {"role": "user", "content": "What is the capital of France?"}
  ]
}
```

### Streaming

```json
POST /gemini/chat/completions
{
  "model": "gemini-3.5-flash",
  "messages": [{"role": "user", "content": "Write a short poem"}],
  "stream": true
}
```

### Vision (Multi-modal Input)

Pass images alongside text by using a content array:

```json
POST /gemini/chat/completions
{
  "model": "gemini-2.5-pro",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
      ]
    }
  ]
}
```

`image_url.url` supports:
- **Base64 data URI** (recommended): `"data:image/jpeg;base64,/9j/4AAQ..."` — MIME type is embedded in the prefix, no separate `media_type` field needed.
- **Public image URL**: `"https://cdn.example.com/image.jpg"`

Supported image types: `png`, `jpeg`, `webp`, `heic`, `heif`.

### Reasoning

Control reasoning depth with `reasoning_effort`:

```json
POST /gemini/chat/completions
{
  "model": "gemini-2.5-pro",
  "messages": [{"role": "user", "content": "Solve this math problem step by step: ..."}],
  "reasoning_effort": "high"
}
```

### Response Format (JSON Mode)

```json
POST /gemini/chat/completions
{
  "model": "gemini-2.5-flash",
  "messages": [{"role": "user", "content": "List 3 fruits as JSON"}],
  "response_format": {"type": "json_object"}
}
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Gemini model name (see Models table) |
| `messages` | array | Array of `{role, content}` objects — `role`: `"user"`, `"assistant"`, `"system"` |
| `stream` | boolean | Enable SSE streaming |
| `temperature` | number | Randomness 0–2 |
| `top_p` | number | Nucleus sampling 0–1 |
| `max_tokens` | integer | Maximum output tokens |
| `max_completion_tokens` | integer | Alias for `max_tokens` |
| `response_format` | object | `{"type": "json_object"}` for structured output |
| `reasoning_effort` | string | `"minimal"`, `"low"`, `"medium"`, `"high"` — thinking depth |
| `tools` | array | Function/tool definitions for tool calling |
| `tool_choice` | string/object | Tool selection strategy |
| `n` | integer | Number of completions to generate |
| `seed` | integer | Reproducibility seed |
| `stop` | string/array | Stop sequences |
| `logprobs` | boolean | Return log probabilities |
| `top_logprobs` | integer | Top N log probabilities per token |
| `frequency_penalty` | number | Penalty for token frequency |
| `presence_penalty` | number | Penalty for token presence |
| `user` | string | End-user identifier |
| `service_tier` | string | `"auto"`, `"default"`, `"flex"`, `"scale"`, `"priority"` |

### Response

```json
{
  "id": "chatcmpl-20251122212413908150493uPhjTUO9",
  "model": "gemini-2.5-pro",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I am a large language model, trained by Google.",
        "reasoning_content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 932,
    "total_tokens": 940
  }
}
```

The `reasoning_content` field (inside `message`) contains the model's internal chain-of-thought when `reasoning_effort` is set.

---

## Native Gemini API

For the native Gemini API format, use `POST /v1beta/models/{model}:generateContent` or `POST /v1beta/models/{model}:streamGenerateContent`.

### Generate Content

```json
POST /v1beta/models/gemini-2.5-pro:generateContent
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "Explain quantum entanglement"}]
    }
  ],
  "generationConfig": {
    "temperature": 0.7,
    "maxOutputTokens": 1024
  }
}
```

### Parameters (Native API)

| Parameter | Type | Description |
|-----------|------|-------------|
| `contents` | array | **Required.** Array of `{role, parts}` objects |
| `systemInstruction` | object | System-level instruction |
| `generationConfig` | object | Generation settings (temperature, maxOutputTokens, etc.) |
| `tools` | array | Tool definitions |
| `toolConfig` | object | Tool usage configuration |
| `safetySettings` | array | Content safety filters |
| `cachedContent` | string | Cached content reference |

---

## Video Generation (`POST /gemini/videos`)

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /gemini/tasks` with `{"id": "..."}`.

### Generate Video

```bash
curl -X POST https://api.acedata.cloud/gemini/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a glowing jellyfish drifting through deep ocean", "model": "omni-flash", "callback_url": "https://api.acedata.cloud/health"}'
```

```json
POST /gemini/videos
{
  "prompt": "a glowing jellyfish drifting through deep ocean",
  "model": "omni-flash",
  "aspect_ratio": "16:9"
}
```

### Video Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | **Yes** | string | Video description |
| `model` | No | `"omni-flash"` | Video model |
| `aspect_ratio` | No | `"16:9"`, `"9:16"` | Output aspect ratio |
| `image_urls` | No | array of strings | Reference image URLs for image-to-video |
| `callback_url` | No | string | Async webhook notification URL |
| `async` | No | boolean | Return immediately with a task ID |

### Task Polling

```json
POST /gemini/tasks
{
  "id": "<task_id>"
}
```

Batch polling:

```json
POST /gemini/tasks
{
  "ids": ["<task_id_1>", "<task_id_2>"],
  "action": "retrieve_batch"
}
```

---

## Gotchas

- `/gemini/chat/completions` is **100% OpenAI-compatible** — use the standard OpenAI SDK with `base_url="https://api.acedata.cloud"` and a Gemini model name
- `reasoning_content` in the response contains the model's thinking — only present for reasoning-capable models
- For vision, use the content-array format; the `image_url.url` field must be a full URL or a `data:` URI (no separate `media_type` field)
- The native `/v1beta/models/{model}:generateContent` endpoint uses `parts` (not `content`) inside each message
- Video generation with `omni-flash` is async — always set `callback_url` or poll via `/gemini/tasks`
- Task polling uses `id` (not `task_id`) in the `/gemini/tasks` request body

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

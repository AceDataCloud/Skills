---
name: ai-chat
description: Access 50+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, DeepSeek, Grok, or other models through a single endpoint. Also covers OpenAI image generation (gpt-image-2, gpt-image-1, dall-e-3) and the Tasks API for callback-mode async workflows. Supports streaming, function calling, vision, and image generation/editing.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Works as a drop-in replacement for the OpenAI SDK.
---

# AI Chat — Unified LLM Gateway

Access 50+ language models through a single OpenAI-compatible endpoint via AceDataCloud.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/v1/chat/completions \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4-20250514", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## OpenAI SDK Drop-in

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-token-here",
    base_url="https://api.acedata.cloud/v1"
)

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
```

## Available Models

### OpenAI GPT

| Model | Type | Best For |
|-------|------|----------|
| `gpt-4.1` | Latest | General-purpose, high quality |
| `gpt-4.1-mini` | Small | Fast, cost-effective |
| `gpt-4.1-nano` | Tiny | Ultra-fast, lowest cost |
| `gpt-4o` | Multimodal | Vision + text |
| `gpt-4o-mini` | Small multimodal | Fast vision tasks |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `gpt-5` | Latest gen | Next-gen intelligence |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5-mini` | Mini gen 5 | Fast next-gen |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-6` | Latest Opus | Highest capability |
| `claude-sonnet-4-6` | Latest Sonnet | Balanced quality/speed |
| `claude-opus-4-5-20251101` | Opus 4.5 | Premium tasks |
| `claude-sonnet-4-5-20250929` | Sonnet 4.5 | High-quality balance |
| `claude-sonnet-4-20250514` | Sonnet 4 | Reliable general-purpose |
| `claude-haiku-4-5-20251001` | Haiku 4.5 | Fast, efficient |
| `claude-3-5-sonnet-20241022` | Legacy 3.5 | Proven track record |
| `claude-3-opus-20240229` | Legacy Opus | Maximum quality (legacy) |

### Google Gemini

| Model | Best For |
|-------|----------|
| `gemini-1.5-pro` | Long context, complex tasks |
| `gemini-1.5-flash` | Fast, efficient |

### DeepSeek

| Model | Best For |
|-------|----------|
| `deepseek-r1` | Deep reasoning |
| `deepseek-r1-0528` | Latest reasoning |
| `deepseek-v3` | General-purpose |
| `deepseek-v3-250324` | Latest general |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4` | Latest, highest capability |
| `grok-3` | General-purpose |
| `grok-3-fast` | Speed-optimized |
| `grok-3-mini` | Compact, efficient |

## Features

### Streaming

```json
POST /v1/chat/completions
{
  "model": "claude-sonnet-4-20250514",
  "messages": [{"role": "user", "content": "Write a story"}],
  "stream": true
}
```

### Function Calling

```json
POST /v1/chat/completions
{
  "model": "gpt-4.1",
  "messages": [{"role": "user", "content": "What's the weather in Tokyo?"}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
      }
    }
  ]
}
```

### Vision

```json
POST /v1/chat/completions
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
      ]
    }
  ]
}
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (see tables above) |
| `messages` | array | Array of `{role, content}` objects |
| `temperature` | 0–2 | Randomness (default: 1) |
| `top_p` | 0–1 | Nucleus sampling |
| `max_tokens` | integer | Maximum output tokens |
| `stream` | boolean | Enable SSE streaming |
| `tools` | array | Function calling definitions |
| `tool_choice` | string/object | Tool selection strategy |

## Response

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "model": "claude-sonnet-4-20250514",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "Hello!"},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

## Gotchas

- **100% OpenAI-compatible** — use the standard OpenAI SDK with `base_url="https://api.acedata.cloud/v1"`
- Billing is token-based with per-model pricing (more expensive models cost more per token)
- Vision is supported on multimodal models (`gpt-4o`, `gpt-4o-mini`, `grok-2-vision-*`)
- Function calling works on most modern models (GPT-4+, Claude 3+)
- Streaming returns `chat.completion.chunk` objects via SSE
- `finish_reason` values: `"stop"` (complete), `"length"` (max tokens), `"tool_calls"` (function call), `"content_filter"` (filtered)

## Stateful Conversations Endpoint

For stateful, session-based chat (no need to send the full history each time), use the `/aichat/conversations` endpoint:

```bash
curl -X POST https://api.acedata.cloud/aichat/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (see Available Models above) |
| `question` | string | The prompt or question to answer |
| `id` | string | Conversation ID — pass the same ID to continue a session |
| `preset` | string | Preset/system prompt for the conversation |
| `stateful` | boolean | Enable stateful conversation (maintains history server-side) |
| `references` | array | Additional context documents to include |

## Image Generation

Generate images from text prompts using OpenAI image models via `POST /openai/images/generations`.

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-2", "prompt": "A watercolor painting of a mountain at sunset", "size": "1024x1024"}'
```

### Image Models

| Model | Description |
|-------|-------------|
| `gpt-image-2` | Latest generation — best text rendering, layout control, and image fidelity (recommended) |
| `gpt-image-1` | Previous generation GPT image model |
| `gpt-image-1.5` | Intermediate GPT image model |
| `dall-e-3` | Classic DALL·E 3 model |

### Image Generation Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Image model (see table above) |
| `prompt` | string | Text description of the desired image (max 32000 chars for GPT image models) |
| `size` | string | `"1024x1024"`, `"1536x1024"` (landscape), `"1024x1536"` (portrait), `"auto"` |
| `quality` | string | `"auto"` (default), `"high"`, `"medium"`, `"low"` |
| `n` | integer | Number of images to generate (1–10) |
| `output_format` | string | `"png"` (default), `"jpeg"`, `"webp"` |
| `output_compression` | integer | Compression level 0–100% for `webp`/`jpeg` |
| `background` | string | `"transparent"`, `"opaque"`, `"auto"` |
| `response_format` | string | `"url"` (default) or `"b64_json"` (for `dall-e-3` / `dall-e-2`) |
| `callback_url` | string | Async callback URL — returns `task_id` immediately and POSTs result when done |

### Image Editing

Edit existing images via `POST /openai/images/edits`. GPT image models accept image URLs directly as JSON; `dall-e-2` requires `multipart/form-data`.

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "image": "https://example.com/photo.png",
    "prompt": "Convert this image to dark mode while keeping the layout intact",
    "size": "1024x1024"
  }'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Same models as image generation above |
| `image` | string or array | Source image URL(s) — up to 16 images for GPT image models |
| `prompt` | string | Editing instruction |
| `size` | string | Output size |
| `quality` | string | `"auto"`, `"high"`, `"medium"`, `"low"` |
| `input_fidelity` | string | `"high"` or `"low"` — how closely to match the source image style |
| `output_format` | string | `"png"`, `"jpeg"`, `"webp"` |
| `callback_url` | string | Async callback URL (see Tasks API below) |

## Tasks API

Query previously submitted callback-mode image tasks via `POST /openai/tasks`. Tasks are only stored when the original request included a `callback_url`.

> **Note:** The Tasks API does not incur additional charges — only the original image generation/editing request is billed.

### Retrieve a Single Task

```bash
curl -X POST https://api.acedata.cloud/openai/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve", "id": "7489df4c-ef03-4de0-b598-e9a590793434"}'
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | `"retrieve"` |
| `id` | string | One of | Task ID returned when the image request was submitted |
| `trace_id` | string | One of | Custom `trace_id` passed in the original request |

### Retrieve Multiple Tasks

```bash
curl -X POST https://api.acedata.cloud/openai/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve_batch", "trace_ids": ["my-trace-001", "my-trace-002"]}'
```

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | `"retrieve_batch"` |
| `ids` | string[] | Query by task ID list |
| `trace_ids` | string[] | Query by custom `trace_id` list |
| `application_id` | string | Query all tasks for an application |
| `user_id` | string | Query all tasks for a user |
| `type` | string | Filter by task type, e.g. `"images_generations"`, `"images_edits"` |
| `offset` | integer | Pagination offset (default: `0`) |
| `limit` | integer | Page size (default: `12`) |
| `created_at_min` | float | Start of time window (Unix seconds) |
| `created_at_max` | float | End of time window (Unix seconds) |

### Task Response Fields

| Field | Description |
|-------|-------------|
| `id` | Task ID assigned at submission |
| `trace_id` | Custom trace identifier from the original request |
| `type` | Upstream task type (`images_generations`, `images_edits`, etc.) |
| `request` | Full original request body |
| `response` | Final upstream response (populated once the task finishes) |
| `created_at` / `finished_at` | Unix timestamps (seconds) |
| `duration` | Processing time in seconds |

---
name: ai-chat
description: Access 50+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, DeepSeek, Grok, or other models through a single endpoint. Supports streaming, function calling, and vision.
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
| `gpt-5.5` | Latest gen | Highest next-gen capability |
| `gpt-5.5-pro` | Latest gen Pro | Next-gen pro tasks |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5.4-pro` | Gen 5.4 Pro | Premium next-gen |
| `gpt-5.2` | Gen 5.2 | Balanced next-gen |
| `gpt-5.1` | Gen 5.1 | Next-gen intelligence |
| `gpt-5` | Gen 5 | Next-gen general-purpose |
| `gpt-5-mini` | Mini gen 5 | Fast next-gen |
| `gpt-5-nano` | Nano gen 5 | Ultra-fast next-gen |
| `gpt-4.1` | Latest GPT-4 | General-purpose, high quality |
| `gpt-4.1-mini` | Small | Fast, cost-effective |
| `gpt-4.1-nano` | Tiny | Ultra-fast, lowest cost |
| `gpt-4o` | Multimodal | Vision + text |
| `gpt-4o-mini` | Small multimodal | Fast vision tasks |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | O3 reasoning | Next-gen reasoning |
| `o3-mini` | O3 mini | Efficient reasoning |
| `o3-pro` | O3 pro | Advanced O3 reasoning |
| `o4-mini` | O4 mini | Latest compact reasoning |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-7` | Latest Opus | Highest capability |
| `claude-opus-4-6` | Opus 4.6 | Premium tasks |
| `claude-sonnet-4-6` | Latest Sonnet | Balanced quality/speed |
| `claude-opus-4-5-20251101` | Opus 4.5 | High-capability tasks |
| `claude-sonnet-4-5-20250929` | Sonnet 4.5 | High-quality balance |
| `claude-haiku-4-5-20251001` | Haiku 4.5 | Fast, efficient |
| `claude-opus-4-1-20250805` | Opus 4.1 | Reliable premium |
| `claude-sonnet-4-20250514` | Sonnet 4 | Reliable general-purpose |
| `claude-opus-4-20250514` | Opus 4 | High-capability legacy |
| `claude-3-7-sonnet-20250219` | Sonnet 3.7 | Extended thinking |
| `claude-3-5-sonnet-20241022` | Sonnet 3.5 | Proven track record |
| `claude-3-5-haiku-20241022` | Haiku 3.5 | Fast, cost-effective |
| `claude-3-opus-20240229` | Opus 3 | Maximum quality (legacy) |

### Google Gemini

| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` | Latest, highest capability |
| `gemini-3.0-pro` | Pro tasks |
| `gemini-3-flash-preview` | Fast preview |
| `gemini-2.5-pro` | Long context, complex tasks |
| `gemini-2.5-flash` | Fast, efficient |
| `gemini-2.0-flash` | Lightweight, quick |

### DeepSeek

| Model | Best For |
|-------|----------|
| `deepseek-r1` | Deep reasoning |
| `deepseek-r1-0528` | Latest reasoning |
| `deepseek-v3` | General-purpose |
| `deepseek-v3-250324` | Latest general |
| `deepseek-v3.2-exp` | Experimental next-gen |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4` | Latest, highest capability |
| `grok-4-1-fast` | Fast Grok 4.1 |
| `grok-4-1-fast-non-reasoning` | Non-reasoning fast tasks |
| `grok-3` | General-purpose |
| `grok-3-mini` | Compact, efficient |
| `grok-2-vision` | Vision tasks |

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

## Image Generation

Generate images from text using DALL-E, GPT-Image, or Nano Banana models via `/openai/images/generations`:

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-1", "prompt": "A futuristic city at sunset", "size": "1024x1024"}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Text description of the desired image (required) |
| `model` | string | `dall-e-2`, `dall-e-3`, `gpt-image-1`, `gpt-image-1.5`, `gpt-image-2`, `nano-banana`, `nano-banana-2`, `nano-banana-pro` (required) |
| `n` | integer | Number of images to generate (1–10) |
| `size` | string | `1024x1024`, `1536x1024`, `1024x1536`, `1792x1024`, `1024x1792`, `256x256`, `512x512`, `auto` |
| `quality` | string | `auto`, `high`, `medium`, `low`, `hd`, `standard` |
| `style` | string | `vivid` or `natural` (DALL-E 3 only) |
| `background` | string | `transparent`, `opaque`, or `auto` (GPT-Image models) |
| `output_format` | string | `png`, `jpeg`, or `webp` (GPT-Image models) |
| `response_format` | string | `url` or `b64_json` (DALL-E models) |
| `callback_url` | string | Optional webhook URL — returns `task_id` immediately |

## Image Editing

Edit existing images with a text prompt via `/openai/images/edits`:

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-1", "image": "https://example.com/photo.jpg", "prompt": "Remove the background"}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | string/array | Reference image URL(s) — up to 16 images for GPT-Image models (required) |
| `prompt` | string | Text description of the desired edit (required) |
| `model` | string | `dall-e-3`, `gpt-image-1`, `gpt-image-1.5`, `gpt-image-2`, `nano-banana`, `nano-banana-2`, `nano-banana-pro` |
| `mask` | string | Optional mask PNG — transparent areas indicate regions to edit |
| `n` | integer | Number of output images (1–10) |
| `size` | string | `1024x1024`, `1536x1024`, `1024x1536`, `256x256`, `512x512`, `auto` |
| `quality` | string | `auto`, `high`, `medium`, `low`, `standard` |
| `background` | string | `transparent`, `opaque`, or `auto` (GPT-Image models) |
| `input_fidelity` | string | `high` or `low` — how strongly to match input style |
| `output_format` | string | `png`, `jpeg`, or `webp` |
| `response_format` | string | `url` or `b64_json` |
| `callback_url` | string | Optional webhook URL — returns `task_id` immediately |

## Responses API

The OpenAI Responses API provides a stateless alternative to chat completions via `/openai/responses`:

```bash
curl -X POST https://api.acedata.cloud/openai/responses \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "input": [{"role": "user", "content": "Hello!"}]}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (supports all GPT-4/5 and O-series models) (required) |
| `input` | array | List of `{role, content}` message objects (required) |
| `stream` | boolean | Enable SSE streaming |
| `tools` | array | Tool/function definitions |
| `max_tokens` | number | Maximum output tokens |
| `temperature` | number | Sampling temperature (0–2) |
| `response_format` | object | Structured output format |
| `background` | boolean | Run in background (returns immediately) |

## Gotchas

- **100% OpenAI-compatible** — use the standard OpenAI SDK with `base_url="https://api.acedata.cloud/v1"`
- Billing is token-based with per-model pricing (more expensive models cost more per token)
- Vision is supported on multimodal models (`gpt-4o`, `gpt-4o-mini`, `grok-2-vision`)
- Function calling works on most modern models (GPT-4+, Claude 3+)
- Streaming returns `chat.completion.chunk` objects via SSE
- `finish_reason` values: `"stop"` (complete), `"length"` (max tokens), `"tool_calls"` (function call), `"content_filter"` (filtered)
- Image generation with GPT-Image models supports `callback_url` for async delivery

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
| `model` | string | Model name (see Available Models above; also supports `glm-5.1`, `glm-4.7`, `glm-4.6`, `glm-4.5-air`) |
| `question` | string | The prompt or question to answer |
| `id` | string | Conversation ID — pass the same ID to continue a session |
| `preset` | string | Preset/system prompt for the conversation |
| `stateful` | boolean | Enable stateful conversation (maintains history server-side) |
| `references` | array | Additional context documents to include |

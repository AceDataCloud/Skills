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
| `gpt-5.5` | Gen 5.5 | Highest-capability next-gen |
| `gpt-5.5-pro` | Gen 5.5 Pro | Pro-tier next-gen |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5.4-pro` | Gen 5.4 Pro | Pro-tier high-performance |
| `gpt-5.2` | Gen 5.2 | Balanced next-gen |
| `gpt-5.1` | Gen 5.1 | Efficient next-gen |
| `gpt-5.1-all` | Gen 5.1 All | All-access next-gen |
| `gpt-5` | Gen 5 | Next-gen intelligence |
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
| `o3` | Reasoning gen 3 | Latest advanced reasoning |
| `o3-mini` | Small reasoning gen 3 | Fast advanced reasoning |
| `o3-pro` | Pro reasoning gen 3 | Maximum reasoning quality |
| `o4-mini` | Reasoning gen 4 mini | Efficient next-gen reasoning |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-7` | Latest Opus | Highest capability |
| `claude-opus-4-6` | Opus 4.6 | High capability |
| `claude-sonnet-4-6` | Latest Sonnet | Balanced quality/speed |
| `claude-opus-4-5-20251101` | Opus 4.5 | Premium tasks |
| `claude-sonnet-4-5-20250929` | Sonnet 4.5 | High-quality balance |
| `claude-opus-4-1-20250805` | Opus 4.1 | Strong capability |
| `claude-sonnet-4-20250514` | Sonnet 4 | Reliable general-purpose |
| `claude-opus-4-20250514` | Opus 4 | Advanced tasks |
| `claude-haiku-4-5-20251001` | Haiku 4.5 | Fast, efficient |
| `claude-3-7-sonnet-20250219` | Sonnet 3.7 | Extended thinking |
| `claude-3-5-sonnet-20241022` | Sonnet 3.5 | Proven track record |
| `claude-3-5-haiku-20241022` | Haiku 3.5 | Fast 3.5 generation |
| `claude-3-5-sonnet-20240620` | Sonnet 3.5 (Jun) | Earlier 3.5 release |
| `claude-3-haiku-20240307` | Haiku 3 | Ultra-fast |
| `claude-3-sonnet-20240229` | Sonnet 3 | Balanced (legacy) |
| `claude-3-opus-20240229` | Opus 3 | Maximum quality (legacy) |

### Google Gemini

| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` | Latest, highest capability |
| `gemini-3.0-pro` | Advanced tasks |
| `gemini-3-flash-preview` | Fast preview generation |
| `gemini-2.5-pro` | Long context, complex tasks |
| `gemini-2.5-flash` | Fast, efficient |
| `gemini-2.0-flash` | Efficient multimodal |

### DeepSeek

| Model | Best For |
|-------|----------|
| `deepseek-r1` | Deep reasoning |
| `deepseek-r1-0528` | Latest reasoning |
| `deepseek-v3` | General-purpose |
| `deepseek-v3-250324` | Latest general |
| `deepseek-v3.2-exp` | Experimental v3.2 |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4` | Latest, highest capability |
| `grok-4-1-fast` | Fast generation |
| `grok-4-1-fast-non-reasoning` | Fast, non-reasoning mode |
| `grok-3` | General-purpose |
| `grok-3-mini` | Compact, efficient |
| `grok-2-vision` | Vision + text tasks |

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
- Vision is supported on multimodal models (`gpt-4o`, `gpt-4o-mini`, `grok-2-vision`)
- Function calling works on most modern models (GPT-4+, Claude 3+)
- Streaming returns `chat.completion.chunk` objects via SSE
- `finish_reason` values: `"stop"` (complete), `"length"` (max tokens), `"tool_calls"` (function call), `"content_filter"` (filtered)
- Use `reasoning_effort` parameter to control reasoning depth on reasoning models (o1/o3/o4/gpt-5 series)

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
| `model` | string | Model name — GPT, DeepSeek, Grok, or GLM models (Claude/Gemini not available here) |
| `question` | string | The prompt or question to answer |
| `id` | string | Conversation ID — pass the same ID to continue a session |
| `preset` | string | Preset/system prompt for the conversation |
| `stateful` | boolean | Enable stateful conversation (maintains history server-side) |
| `references` | array | Additional context documents to include |

> **Note:** The stateful endpoint supports GPT, o-series, DeepSeek, Grok, and GLM models. For Claude or Gemini, use the standard `/v1/chat/completions` endpoint instead.

## OpenAI Responses API

Use the `/openai/responses` endpoint for the OpenAI Responses API — a stateful alternative to chat completions:

```bash
curl -X POST https://api.acedata.cloud/openai/responses \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "input": [{"role": "user", "content": "Hello!"}]}'
```

Supports all GPT and o-series models (see OpenAI GPT table above). Accepts `input` (array of messages), `tools`, `max_tokens`, `temperature`, `stream`, and `background` parameters.

## OpenAI-Compatible Image Generation

Generate and edit images through the OpenAI-compatible endpoint supporting DALL-E, GPT-Image, and NanoBanana models:

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a photorealistic mountain landscape at sunset", "model": "gpt-image-1", "size": "1024x1024"}'
```

### Image Generation Models

| Model | Best For |
|-------|----------|
| `gpt-image-1` | High-quality GPT image generation |
| `gpt-image-1.5` | Improved GPT image generation |
| `gpt-image-2` | Latest GPT image generation |
| `dall-e-3` | DALL-E 3 (OpenAI) |
| `dall-e-2` | DALL-E 2 (OpenAI, legacy) |
| `nano-banana` | NanoBanana (Gemini-based) |
| `nano-banana-2` | NanoBanana second generation |
| `nano-banana-pro` | NanoBanana highest quality |

### Image Generation Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Image description |
| `model` | string | Model to use (see table above) |
| `size` | `"1024x1024"`, `"1792x1024"`, `"1024x1792"`, `"1536x1024"`, `"1024x1536"`, `"auto"` | Output dimensions |
| `quality` | `"auto"`, `"high"`, `"medium"`, `"low"`, `"hd"`, `"standard"` | Output quality |
| `n` | 1–10 | Number of images |
| `output_format` | `"png"`, `"jpeg"`, `"webp"` | Output file format |
| `background` | `"transparent"`, `"opaque"`, `"auto"` | Background type |
| `response_format` | `"url"`, `"b64_json"` | Return as URL or base64 |
| `callback_url` | string | Async callback URL; returns `task_id` immediately |

### Image Editing

Edit existing images with the `/openai/images/edits` endpoint:

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image": "https://example.com/photo.jpg", "prompt": "add snow to the mountains", "model": "gpt-image-1"}'
```

Supports the same models and most parameters as generations; `image` (URL or array of URLs) and `prompt` are required.

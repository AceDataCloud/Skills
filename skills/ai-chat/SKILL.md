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
| `gpt-5.5` | Latest | Top-tier next-gen intelligence |
| `gpt-5.5-pro` | Pro Latest | Highest-performance next-gen |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5.4-pro` | Pro Gen 5.4 | Premium next-gen quality |
| `gpt-5.2` | Gen 5.2 | Balanced next-gen |
| `gpt-5.1` | Gen 5.1 | Reliable next-gen |
| `gpt-5` | Gen 5 | General-purpose next-gen |
| `gpt-5-mini` | Mini Gen 5 | Fast next-gen |
| `gpt-5-nano` | Nano Gen 5 | Ultra-fast next-gen |
| `gpt-4.1` | GPT-4.1 | General-purpose, high quality |
| `gpt-4.1-mini` | Small | Fast, cost-effective |
| `gpt-4.1-nano` | Tiny | Ultra-fast, lowest cost |
| `gpt-4o` | Multimodal | Vision + text |
| `gpt-4o-mini` | Small multimodal | Fast vision tasks |
| `o1` | Reasoning | Complex reasoning |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | Next reasoning | Advanced next-gen reasoning |
| `o3-mini` | Small next reasoning | Fast next-gen reasoning |
| `o3-pro` | Pro next reasoning | Premium next-gen reasoning |
| `o4-mini` | Latest mini reasoning | Latest fast reasoning |

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

## Image Generation

Generate images using OpenAI-compatible DALL-E and GPT Image models via `POST /openai/images/generations`.

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-1", "prompt": "A futuristic city skyline at sunset", "size": "1536x1024"}'
```

### Image Generation Models

| Model | Best For |
|-------|----------|
| `gpt-image-1` | High-quality general images |
| `gpt-image-1.5` | Enhanced GPT Image v1 |
| `gpt-image-2` | Latest GPT Image, flexible size |
| `dall-e-3` | Expressive, artistic images |
| `dall-e-2` | Legacy, fast generation |
| `nano-banana` | Gemini-based, conversational |
| `nano-banana-2` | Improved Gemini-based |
| `nano-banana-pro` | Best Gemini-based quality |

### Image Generation Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Text description of the desired image (max 32,000 chars for GPT Image models) |
| `model` | see table above | Model to use (required) |
| `size` | `WIDTHxHEIGHT` or `"auto"` | `gpt-image-2`: any `WIDTHxHEIGHT`. `gpt-image-1`/`1.5`: `1024x1024`, `1536x1024`, `1024x1536`, `auto`. `dall-e-3`: `1024x1024`, `1024x1792`, `1792x1024`. `dall-e-2`: `256x256`, `512x512`, `1024x1024` |
| `n` | 1–10 | Number of images (dall-e-3: only `1`) |
| `quality` | `"auto"`, `"high"`, `"medium"`, `"low"`, `"hd"`, `"standard"` | GPT Image models: `auto` (default), `high`, `medium`, `low`. dall-e-3: `hd` or `standard`. |
| `output_format` | `"png"`, `"jpeg"`, `"webp"` | Return format (GPT Image models) |
| `output_compression` | 0–100 | Compression level for `webp`/`jpeg` |
| `background` | `"transparent"`, `"opaque"`, `"auto"` | Transparency handling (GPT Image models) |
| `moderation` | `"low"`, `"auto"` | Content-moderation level (GPT Image models) |
| `response_format` | `"url"`, `"b64_json"` | Return format for DALL-E models |
| `style` | `"vivid"`, `"natural"` | Style for dall-e-3 |
| `callback_url` | string | Async callback URL; returns `task_id` immediately |

## Image Editing

Edit existing images using `POST /openai/images/edits`.

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-1", "image": "https://example.com/photo.jpg", "prompt": "Add a rainbow in the sky"}'
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `image` | string or array | Reference image URL(s) — up to 16 for GPT Image models |
| `prompt` | string | Text description of the desired edit |
| `model` | same as image generation | Model to use (required) |
| `mask` | string | Optional PNG mask (<4 MB); transparent areas are editable |
| `input_fidelity` | `"high"`, `"low"` | How strongly to preserve input style (GPT Image models) |
| `size` | `WIDTHxHEIGHT` or `"auto"` | Same size options as image generation |
| `output_format` | `"png"`, `"jpeg"`, `"webp"` | Return format (GPT Image models) |
| `quality` | `"auto"`, `"high"`, `"medium"`, `"low"`, `"standard"` | Image quality |
| `background` | `"transparent"`, `"opaque"`, `"auto"` | Transparency handling |
| `callback_url` | string | Async callback URL |

## Embeddings

Create embedding vectors from text using `POST /openai/embeddings`.

```bash
curl -X POST https://api.acedata.cloud/openai/embeddings \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "text-embedding-3-small", "input": "The quick brown fox jumps over the lazy dog"}'
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `input` | string or array | Text to embed (single string, array of strings, or token arrays) |
| `model` | `"text-embedding-3-small"`, `"text-embedding-3-large"`, `"text-embedding-ada-002"` | Embedding model to use |
| `encoding_format` | `"float"`, `"base64"` | Format of the returned embeddings |
| `dimensions` | integer | Optional output embedding size (when supported by the model) |

## Responses (Stateful Completions)

Stateless-to-stateful responses using `POST /openai/responses` — no need to resend full history:

```bash
curl -X POST https://api.acedata.cloud/openai/responses \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "input": [{"role": "user", "content": "Explain quantum computing"}]}'
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | string | Model to use (same as chat completions) |
| `input` | array | Messages array (same format as chat completions `messages`) |
| `stream` | boolean | Enable SSE streaming |
| `max_tokens` | integer | Maximum output tokens |
| `temperature` | 0–2 | Sampling temperature |
| `response_format` | object | Structured output format |
| `tools` | array | Function calling tools |
| `background` | boolean | Run the model response in the background |

## Gotchas

- **100% OpenAI-compatible** — use the standard OpenAI SDK with `base_url="https://api.acedata.cloud/v1"`
- Billing is token-based with per-model pricing (more expensive models cost more per token)
- Vision is supported on multimodal models (`gpt-4o`, `gpt-4o-mini`, `grok-2-vision-*`)
- Function calling works on most modern models (GPT-4+, Claude 3+)
- Streaming returns `chat.completion.chunk` objects via SSE
- `finish_reason` values: `"stop"` (complete), `"length"` (max tokens), `"tool_calls"` (function call), `"content_filter"` (filtered)
- Image generation uses `POST /openai/images/generations` (not `/v1/images/generations`); same for edits
- `gpt-image-2` accepts any `WIDTHxHEIGHT` value and bills in two tiers based on megapixels
- Image edit async requests return a `task_id`; poll `/openai/tasks` (or use `callback_url`)

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

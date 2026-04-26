---
name: ai-chat
description: Access 50+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, DeepSeek, Grok, or other models. Also supports image generation and editing (dall-e-2/3, gpt-image-1/1.5/2, nano-banana) via the same service.
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

The same OpenAI-compatible service also exposes image generation at `POST /openai/images/generations`.

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-2", "prompt": "A cinematic portrait in a neon-lit city", "size": "1024x1536"}'
```

### Image Generation Models

| Model | Best For |
|-------|----------|
| `dall-e-2` | Classic DALL·E 2 generation |
| `dall-e-3` | High-quality DALL·E 3 generation |
| `gpt-image-1` | GPT image first generation |
| `gpt-image-1.5` | Improved GPT image generation |
| `gpt-image-2` | Latest GPT image — best instruction following and text rendering |
| `nano-banana` | Gemini-based, fast and cost-effective |
| `nano-banana-2` | Improved nano-banana quality |
| `nano-banana-pro` | Highest-quality nano-banana |

### Image Generation Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Text description of desired image. Max length: 32 000 chars (GPT image models), 4 000 chars (`dall-e-3`), 1 000 chars (`dall-e-2`) |
| `model` | string | Image model (see table above) |
| `size` | string | See model-specific sizes below |
| `quality` | string | `auto` / `high` / `medium` / `low` (GPT image); `hd` / `standard` (`dall-e-3`); `standard` (`dall-e-2`). Default: `auto` |
| `style` | string | `vivid` or `natural` — `dall-e-3` only |
| `n` | integer | Number of images (1–10); `dall-e-3` supports only `1` |
| `response_format` | string | `url` (default) or `b64_json` — `dall-e-2` / `dall-e-3` only (GPT image always returns base64) |
| `background` | string | `transparent`, `opaque`, or `auto` — GPT image models only |
| `output_format` | string | `png`, `jpeg`, or `webp` — GPT image models only |
| `output_compression` | integer | 0–100% compression for webp/jpeg output — GPT image models only |
| `callback_url` | string | Webhook URL for async delivery; returns `task_id` immediately |

**Model-specific sizes:**

| Model family | Supported `size` values |
|---|---|
| GPT image models | `1024x1024`, `1536x1024` (landscape), `1024x1536` (portrait), `auto` (default) |
| `dall-e-2` | `256x256`, `512x512`, `1024x1024` |
| `dall-e-3` | `1024x1024`, `1792x1024`, `1024x1792` |
| nano-banana | `1024x1024`, `1792x1024`, `1024x1792`, `256x256`, `512x512` (mapped to aspect ratios internally) |

## Image Editing

Edit existing images at `POST /openai/images/edits`. Pass source image(s) as URL(s).

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-image-2", "image": "https://example.com/photo.jpg", "prompt": "Convert to dark mode"}'
```

### Image Editing Models

| Model | Notes |
|-------|-------|
| `dall-e-3` | Classic editing |
| `gpt-image-1` | GPT image editing |
| `gpt-image-1.5` | Improved GPT image editing |
| `gpt-image-2` | Best structure preservation, text retention, and URL input support |
| `nano-banana` | Fast Gemini-based editing |
| `nano-banana-2` | Improved nano-banana editing |
| `nano-banana-pro` | Highest-quality nano-banana editing |

### Image Editing Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | string or array | Source image URL(s) — single URL or array of up to 16 URLs |
| `prompt` | string | Edit instruction (max 32 000 chars for GPT image; 1 000 chars for `dall-e-2`) |
| `model` | string | Editing model (see table above) |
| `size` | string | `1024x1024`, `1536x1024`, `1024x1536`, or `auto` (GPT image); `256x256`/`512x512`/`1024x1024` (`dall-e-2`) |
| `quality` | string | `auto`, `high`, `medium`, `low` (GPT image); `standard` (`dall-e-2`) |
| `background` | string | `transparent`, `opaque`, or `auto` — GPT image models only |
| `output_format` | string | `png`, `jpeg`, or `webp` — GPT image models only |
| `output_compression` | integer | 0–100% compression for webp/jpeg — GPT image models only |
| `response_format` | string | `url` (default) or `b64_json` |
| `callback_url` | string | Webhook URL for async delivery |

> **Nano-banana via OpenAI endpoint**: nano-banana models can also be called through `/openai/images/generations` and `/openai/images/edits` as shown above. For the native nano-banana endpoint with aspect-ratio control, see the [nano-banana-image](../nano-banana-image/SKILL.md) skill.

---
name: ai-chat
description: Access 50+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, Kimi, Grok, or other models through a single endpoint. Supports streaming, function calling, and vision.
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

Raw REST calls are also available under the OpenAI namespace, for example
`POST /openai/chat/completions`. If you are using the official OpenAI SDK, keep
using the compatible `base_url="https://api.acedata.cloud/v1"` form shown above.

## Available Models

### OpenAI GPT

| Model | Type | Best For |
|-------|------|----------|
| `gpt-4.1` | Latest | General-purpose, high quality |
| `gpt-4.1-mini` | Small | Fast, cost-effective |
| `gpt-4.1-nano` | Tiny | Ultra-fast, lowest cost |
| `gpt-4.1:free` | Free alias | Free-tier general chat |
| `gpt-4o` | Multimodal | Vision + text |
| `gpt-4o:free` | Free alias | Free-tier multimodal chat |
| `gpt-4o-mini` | Small multimodal | Fast vision tasks |
| `gpt-4o-mini:free` | Free alias | Free-tier fast multimodal chat |
| `gpt-4o-image` | Image chat | Generate or restyle images in chat completions |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | Reasoning | Stronger reasoning + tool use |
| `o3-mini` | Small reasoning | Faster lower-cost reasoning |
| `o3-pro` | Pro reasoning | Highest-end reasoning |
| `o4-mini` | Mini reasoning | Fast next-gen reasoning |
| `gpt-4` | Legacy flagship | Older GPT-4 compatibility |
| `gpt-5.5` | Latest gen | Highest-end GPT-5 generation |
| `gpt-5.5-pro` | Pro gen | Premium GPT-5.5 quality |
| `gpt-5` | Latest gen | Next-gen intelligence |
| `gpt-5:free` | Free alias | Free-tier GPT-5 chat |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5.2` | Gen 5.2 | Mid-cycle GPT-5 variant |
| `gpt-5.1` | Gen 5.1 | Earlier GPT-5 release |
| `gpt-5.1-all` | Gen 5.1 aggregate | Wider GPT-5.1 routing |
| `gpt-5-mini` | Mini gen 5 | Fast next-gen |
| `gpt-5-nano` | Nano gen 5 | Lowest-cost GPT-5 option |
| `gpt-5.5:free` | Free alias | Free-tier GPT-5.5 chat |
| `gpt-oss:free` | Free OSS alias | Free open-weight chat access |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-8` | Latest Opus | Highest capability |
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

### Image Generation in Chat

`gpt-4o-image` can generate images directly from chat completions, including from
text-only prompts or one or more reference images.

```json
POST /openai/chat/completions
{
  "model": "gpt-4o-image",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Generate an anime-style portrait with a hat"},
        {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
      ]
    }
  ],
  "stream": false
}
```

The generated image is returned inside `choices[0].message.content` as Markdown
with a temporary downloadable image URL.

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (see tables above) |
| `messages` | array | Array of `{role, content}` objects |
| `temperature` | 0–2 | Randomness (default: 1) |
| `top_p` | 0–1 | Nucleus sampling |
| `max_tokens` | integer | Maximum output tokens |
| `max_completion_tokens` | integer | Newer OpenAI-style cap for completion output |
| `stream` | boolean | Enable SSE streaming |
| `tools` | array | Function calling definitions |
| `tool_choice` | string/object | Tool selection strategy |
| `response_format` | object | Structured JSON/text output controls |
| `reasoning_effort` | string | Reasoning budget (`minimal`/`low`/`medium`/`high`) for supported models |

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

For stateful, session-based chat (no need to send the full history each time), use `POST /aichat2/conversations` (recommended). `POST /aichat/conversations` remains available for legacy compatibility.

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
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

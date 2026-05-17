---
name: ai-chat
description: Access 80+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, Kimi, Grok, or other models through a single endpoint. Supports streaming, function calling, and vision.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Works as a drop-in replacement for the OpenAI SDK.
---

# AI Chat — Unified LLM Gateway

Access 80+ language models through a single OpenAI-compatible endpoint via AceDataCloud.

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

Representative currently available public models include the following families and recent variants.

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
| `o3` | Reasoning | Advanced multi-step reasoning |
| `o3-mini` | Small reasoning | Faster reasoning tasks |
| `o3-pro` | Pro reasoning | Premium reasoning quality |
| `o4-mini` | Small reasoning | Lightweight next-gen reasoning |
| `gpt-5` | Latest gen | Next-gen intelligence |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5-mini` | Mini gen 5 | Fast next-gen |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-7` | Latest Opus | Highest capability |
| `claude-opus-4-6` | Latest Opus | Highest capability |
| `claude-opus-4-1-20250805` | Pinned Opus | Stable pinned release |
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
| `gemini-2.0-flash-lite` | Fast, lightweight chat |
| `gemini-2.5-flash-lite` | Newer low-latency chat |
| `gemini-3-pro-preview` | Preview flagship reasoning |
| `gemini-3.1-pro` | High-quality multimodal work |
| `gemini-3.1-pro-preview` | Preview of the latest pro model |
| `gemini-3.1-flash-lite-preview` | Fast preview model |
| `gemini-3.1-flash-image-preview` | Image-aware Gemini workflows |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4` | Latest, highest capability |
| `grok-4-0709` | Pinned Grok 4 snapshot |
| `grok-4-1-fast` | Faster Grok 4.1 |
| `grok-4-1-fast-non-reasoning` | Low-latency direct responses |
| `grok-4-1-fast-reasoning` | Fast reasoning-heavy workloads |
| `grok-3` | General-purpose |
| `grok-3-fast` | Speed-optimized |
| `grok-3-mini` | Compact, efficient |
| `grok-3-mini-fast` | Fast compact Grok |

### MoonshotAI Kimi

| Model | Best For |
|-------|----------|
| `kimi-k2-0711-preview` | Earlier K2 preview compatibility |
| `kimi-k2-0905-preview` | Latest preview release |
| `kimi-k2-instruct-0905` | Instruction-following chat |
| `kimi-k2-thinking` | Deliberate reasoning |
| `kimi-k2-thinking-turbo` | Faster reasoning |
| `kimi-k2-turbo-preview` | Speed-focused preview |
| `kimi-k2.5` | Latest public Kimi generation |

### Zhipu GLM

| Model | Best For |
|-------|----------|
| `glm-5` | Flagship GLM reasoning |
| `glm-5-turbo` | Faster GLM 5 responses |
| `glm-5.1` | Latest GLM iteration |
| `glm-4.7` | High-quality GLM 4 series |
| `glm-4.6` | Stable GLM 4 release |
| `glm-4.5` | General-purpose GLM |
| `glm-4.5-air` | Lower-latency GLM |
| `glm-4.5v` | Vision-capable GLM |
| `glm-4-plus` | Enhanced GLM 4 |
| `glm-4-air` | Lightweight GLM 4 |
| `glm-4-flash` | Fast GLM 4 responses |
| `glm-3-turbo` | Legacy compatibility |

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

For stateful, session-based chat (no need to send the full history each time), use the recommended `/aichat2/conversations` endpoint. The older `/aichat/conversations` path remains available for legacy compatibility.

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (see Available Models above); required for chat |
| `question` | string | Legacy plain-text prompt field |
| `message` | string or array | Multi-modal input with `text`, `image_url`, or `file_url` blocks |
| `id` | string | Conversation ID — pass the same ID to continue a session |
| `preset` | string | Preset/system prompt for the conversation |
| `stateful` | boolean | Persist the conversation server-side (defaults to `true`) |
| `references` | array | Reference URLs that are attached as image/file context |
| `max_turns` | integer | Maximum tool/agent loop turns for this request |
| `tool_results` | array | Resume data for pending `ask_user_question` tool calls |

`/aichat2/conversations` also supports retrieve, batch retrieve, update, delete, and streaming responses while keeping the same conversation ID.

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

## Conversations Endpoints

### Recommended: `/aichat2/conversations`

For stateful, session-based chat, use `/aichat2/conversations` (v2). It supports normal chat, streaming (`application/x-ndjson` / `text/event-stream`), multimodal input, agentic tool calling, and conversation CRUD actions.

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-5.4", "question": "What is quantum computing?", "stateful": true}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | `chat` (default), `retrieve`, `retrieve_batch`, `update`, `delete` |
| `id` | string | Conversation ID (required for retrieve/update/delete, reused for multi-turn chat) |
| `model` | string | Model name (required for chat) |
| `question` | string | The prompt or question to answer |
| `message` | array | Structured multimodal input blocks (`text`, `image_url`, `file_url`) |
| `preset` | string | Preset/system prompt for the conversation |
| `stateful` | boolean | Session persistence (default `true`) |
| `references` | array | Additional context documents to include |
| `max_turns` | integer | Max agent/tool turns per request |
| `tool_results` | array | Resume paused conversations that requested user input |
| `messages` | array | Conversation messages payload for update operations |
| `title` | string | Conversation title (used by update action) |
| `user_id` | string | Optional conversation owner filter |
| `application_id` | string | Optional application filter |
| `model_group` | string | Optional model family filter |
| `offset` / `limit` | integer | Pagination for `retrieve_batch` |

`Accept` supports `application/json`, `application/x-ndjson`, and `text/event-stream`.

### Legacy: `/aichat/conversations`

The legacy v1 endpoint remains available for backwards compatibility:

```bash
curl -X POST https://api.acedata.cloud/aichat/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

v1 fields: `model`, `question`, `id`, `preset`, `stateful`, `references`.

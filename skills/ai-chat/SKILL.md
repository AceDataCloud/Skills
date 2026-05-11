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
| `gpt-image-1` | Image | Image generation |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | Reasoning | Latest reasoning |
| `o3-mini` | Small reasoning | Fast reasoning |
| `o3-pro` | Pro reasoning | Max reasoning quality |
| `o4-mini` | Compact reasoning | Efficient reasoning |
| `gpt-5-all` | Latest gen | Next-gen intelligence |
| `gpt-5.1-all` | Gen 5.1 | High-performance next-gen |
| `gpt-5.2-pro` | Gen 5.2 | Pro next-gen |
| `gpt-5.4-mini` | Mini gen 5.4 | Fast next-gen |
| `gpt-5.4-nano` | Nano gen 5.4 | Ultra-fast next-gen |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-7` | Latest Opus | Highest capability |
| `claude-opus-4-6` | Opus 4.6 | High capability |
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
| `gemini-3.1-pro` | Best quality |
| `gemini-3.1-pro-preview` | Latest preview |
| `gemini-3.1-flash-image-preview` | Image + text |
| `gemini-3.1-flash-lite-preview` | Fast, efficient |
| `gemini-3-pro-preview` | General-purpose |
| `gemini-2.5-flash-lite` | Lightweight |
| `gemini-2.0-flash-lite` | Budget tasks |

### DeepSeek

| Model | Best For |
|-------|----------|
| `deepseek-v4-flash` | Latest, fast |
| `deepseek-v3.2-exp` | Experimental v3.2 |
| `deepseek-r1-0528` | Latest reasoning |
| `deepseek-r1` | Deep reasoning |
| `deepseek-v3` | General-purpose |
| `deepseek-v3-250324` | Stable general |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4` | Latest, highest capability |
| `grok-4-1-fast` | Fast latest |
| `grok-4-1-fast-reasoning` | Fast reasoning |
| `grok-3` | General-purpose |
| `grok-3-fast` | Speed-optimized |
| `grok-3-mini` | Compact, efficient |
| `grok-3-mini-fast` | Ultra-fast compact |

### Moonshot Kimi

| Model | Best For |
|-------|----------|
| `kimi-k2.5` | Latest, highest capability |
| `kimi-k2-thinking` | Deep reasoning |
| `kimi-k2-thinking-turbo` | Fast reasoning |
| `kimi-k2-instruct-0905` | Instruction following |

### Zhipu GLM

| Model | Best For |
|-------|----------|
| `glm-5.1` | Latest, highest quality |
| `glm-5` | General-purpose |
| `glm-5-turbo` | Fast general |
| `glm-4.7` | Stable quality |
| `glm-4.6` | Balanced |
| `glm-4.5v` | Vision tasks |
| `glm-4.5` | Cost-effective |
| `glm-4.5-air` | Lightweight |

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

## Stateful Conversations (Recommended: v2)

Use `/aichat2/conversations` for the full-featured stateful conversation API with multi-modal input, streaming, agentic tool calling, and CRUD session management.

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

### v2 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (required for `action: chat`) |
| `question` | string | Plain-text user prompt (v1-compatible) |
| `message` | string / array | Multi-modal content blocks: `{type: "text"/"image_url"/"file_url", ...}` |
| `id` | string | Conversation ID — pass the same ID to continue a session |
| `stateful` | boolean | Persist the conversation (default: `true`) |
| `preset` | string | Server-side system prompt preset |
| `references` | array | Reference URLs; image extensions become `image_url` blocks, others become `file_url` |
| `max_turns` | integer | Max agentic-loop iterations for this request |
| `tool_results` | array | Resume a conversation paused on `ask_user_question` |
| `action` | string | `chat` (default), `retrieve`, `retrieve_batch`, `update`, `delete` |
| `title` | string | Conversation title (only for `action: update`) |
| `messages` | array | Replacement message history (only for `action: update`) |
| `user_id` | string | Filter by user (only for `action: retrieve_batch`) |
| `application_id` | string | Filter by application (only for `action: retrieve_batch`) |
| `model_group` | string | Filter by provider: `chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, `deepseek` |
| `offset` | integer | Pagination offset (default: 0) |
| `limit` | integer | Pagination limit (default: 100) |

### Streaming

Set the `accept` header to get streaming responses:

| `accept` | Format |
|----------|--------|
| `application/json` (default) | Single `{answer, id}` response |
| `application/x-ndjson` | One JSON event per line |
| `text/event-stream` | SSE `data: {json}\n\n` |

Key streaming event types: `text_delta`, `thinking`, `tool_use`, `tool_result`, `card`, `citation`, `ask_user_question`, `artifact`, `done`.

### Multi-turn Conversation

```bash
# First turn
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "stateful": true, "question": "Remember: my favourite number is 42."}'
# Returns: {"answer": "...", "id": "f2f4b3e8-..."}

# Continue with same id
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "stateful": true, "id": "f2f4b3e8-...", "question": "What is my favourite number?"}'
```

### Session CRUD

```bash
# Retrieve a conversation
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve", "id": "f2f4b3e8-..."}'

# List conversation summaries
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve_batch", "model_group": "chatgpt", "limit": 20}'

# Delete a conversation
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "delete", "id": "f2f4b3e8-..."}'
```

## Stateful Conversations (Legacy: v1)

The original `/aichat/conversations` endpoint remains available for backward compatibility:

```bash
curl -X POST https://api.acedata.cloud/aichat/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name |
| `question` | string | The prompt or question to answer (required) |
| `id` | string | Conversation ID — pass the same ID to continue a session |
| `preset` | string | Preset/system prompt for the conversation |
| `stateful` | boolean | Enable stateful conversation (maintains history server-side) |
| `references` | array | Additional context documents to include |

To migrate from v1 to v2, replace the URL with `/aichat2/conversations` — the `model`/`question`/`stateful`/`id`/`references`/`preset` fields are fully backward-compatible.

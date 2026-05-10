---
name: ai-chat
description: Access 83+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, DeepSeek, Grok, or other models through a single endpoint. Supports streaming, function calling, and vision.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Works as a drop-in replacement for the OpenAI SDK.
---

# AI Chat — Unified LLM Gateway

Access 83+ language models through a single OpenAI-compatible endpoint via AceDataCloud.

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
| `gpt-image-1` | Image generation | Image synthesis |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | Latest reasoning | Next-gen reasoning |
| `o3-mini` | Mini reasoning | Fast next-gen reasoning |
| `o3-pro` | Pro reasoning | Advanced next-gen reasoning |
| `o4-mini` | Mini reasoning | Ultra-fast reasoning |
| `gpt-5-all` | Latest gen | Next-gen intelligence |
| `gpt-5.2-pro` | Gen 5.2 Pro | High-performance next-gen |
| `gpt-5.4-mini` | Mini gen 5.4 | Fast next-gen |
| `gpt-5.4-nano` | Nano gen 5.4 | Ultra-fast next-gen |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-7` | Latest Opus | Highest capability |
| `claude-opus-4-6` | Opus 4.6 | Premium long tasks |
| `claude-sonnet-4-6` | Latest Sonnet | Balanced quality/speed |
| `claude-opus-4-5-20251101` | Opus 4.5 | Premium tasks |
| `claude-sonnet-4-5-20250929` | Sonnet 4.5 | High-quality balance |
| `claude-opus-4-20250514` | Opus 4 | Reliable premium |
| `claude-sonnet-4-20250514` | Sonnet 4 | Reliable general-purpose |
| `claude-haiku-4-5-20251001` | Haiku 4.5 | Fast, efficient |
| `claude-3-7-sonnet-20250219` | Sonnet 3.7 | Extended thinking |
| `claude-3-5-sonnet-20241022` | Legacy 3.5 | Proven track record |
| `claude-3-opus-20240229` | Legacy Opus | Maximum quality (legacy) |

### Google Gemini

| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` | Latest, highest capability |
| `gemini-3.1-pro-preview` | Preview, cutting-edge |
| `gemini-3.1-flash-image-preview` | Image generation |
| `gemini-3.1-flash-lite-preview` | Fast, efficient |
| `gemini-3-pro-preview` | Gen 3 preview |
| `gemini-2.5-flash-lite` | Lightweight flash |
| `gemini-2.0-flash-lite` | Compact flash |

### DeepSeek

| Model | Best For |
|-------|----------|
| `deepseek-r1` | Deep reasoning |
| `deepseek-r1-0528` | Latest reasoning |
| `deepseek-reasoner` | Advanced reasoning |
| `deepseek-v3` | General-purpose |
| `deepseek-v3-250324` | Latest general |
| `deepseek-v3.2-exp` | Experimental v3.2 |
| `deepseek-v4-flash` | Fast v4 |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4` | Latest, highest capability |
| `grok-4-0709` | Grok 4 (July 2025) |
| `grok-4-1-fast` | Grok 4.1 fast |
| `grok-3` | General-purpose |
| `grok-3-fast` | Speed-optimized |
| `grok-3-mini` | Compact, efficient |
| `grok-3-mini-fast` | Ultra-fast compact |

### Kimi (Moonshot)

| Model | Best For |
|-------|----------|
| `kimi-k2` | General-purpose |
| `kimi-k2-thinking` | Reasoning tasks |
| `kimi-k2-turbo-preview` | Fast turbo |

### GLM (Zhipu AI)

| Model | Best For |
|-------|----------|
| `glm-5` | Latest, highest capability |
| `glm-5.1` | Latest v5.1 |
| `glm-4.7` | Advanced v4.7 |
| `glm-4.6` | Advanced v4.6 |
| `glm-4.5` | Balanced v4.5 |
| `glm-4.5v` | Vision v4.5 |
| `glm-4-plus` | High-quality v4 |
| `glm-4-flash` | Fast v4 |

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

### `/aichat2/conversations` — Recommended

The newer stateful endpoint with full agentic-loop support, multi-modal messages, SSE/NDJSON streaming, and CRUD conversation management.

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

**Response format** is controlled by the `Accept` header:
- `application/json` (default) — returns `{answer, id}` when generation completes
- `application/x-ndjson` — streams line-delimited JSON events
- `text/event-stream` — streams Server-Sent Events (SSE)

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name — required for `action=chat` |
| `action` | string | `chat` (default), `retrieve`, `retrieve_batch`, `update`, `delete` |
| `id` | string | Conversation ID — required for retrieve/update/delete; optional for chat (resumes session) |
| `question` | string | Plain-text user prompt (v1-compatible, ignored when `message` is set) |
| `message` | string/array | Multi-modal content: string or array of `{type, text}` / `{type, image_url}` / `{type, file_url}` blocks |
| `stateful` | boolean | Persist the conversation (default: `true`) |
| `references` | array | Reference URLs — image extensions become `image_url` blocks, others become `file_url` blocks |
| `preset` | string | Server-side system prompt preset name |
| `max_turns` | integer | Max agentic-loop iterations (clamped to platform default) |
| `tool_results` | array | Resume a conversation paused on `ask_user_question` — each entry has `tool_use_id` and `answer` |
| `title` | string | Conversation title (only for `action=update`) |
| `messages` | array | Replace full message history (only for `action=update`) |
| `offset` | integer | Pagination offset (only for `action=retrieve_batch`) |
| `limit` | integer | Pagination limit (only for `action=retrieve_batch`) |

### `/aichat/conversations` — Legacy (v1)

The original stateful endpoint. Supports 78 models. Use `/aichat2/conversations` for new integrations.

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

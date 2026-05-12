---
name: ai-chat
description: Access 83+ LLM models through a unified OpenAI-compatible API via AceDataCloud. Use when you need chat completions from GPT, Claude, Gemini, DeepSeek, Grok, Kimi, GLM, or other models through a single endpoint. Supports streaming, function calling, and vision.
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
| `gpt-4o-all` | Multimodal enhanced | Extended capabilities |
| `gpt-4o-image` | Image generation | Image creation via GPT-4o |
| `gpt-5-all` | Gen 5 | Next-gen intelligence |
| `gpt-5.1-all` | Gen 5.1 | Extended Gen 5 |
| `gpt-5.2-pro` | Gen 5.2 Pro | High-performance |
| `gpt-5.4-mini` | Gen 5.4 Mini | Fast next-gen |
| `gpt-5.4-nano` | Gen 5.4 Nano | Ultra-fast next-gen |
| `gpt-image-1` | Image generation | Native image model |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | Reasoning gen 3 | Latest reasoning |
| `o3-mini` | Small reasoning gen 3 | Fast reasoning |
| `o3-pro` | Pro reasoning gen 3 | Advanced reasoning |
| `o4-mini` | Reasoning gen 4 | Compact reasoning |

### Anthropic Claude

| Model | Type | Best For |
|-------|------|----------|
| `claude-opus-4-7` | Latest Opus | Highest capability |
| `claude-opus-4-6` | Opus 4.6 | High capability |
| `claude-opus-4-5-20251101` | Opus 4.5 | Premium tasks |
| `claude-opus-4-1-20250805` | Opus 4.1 | Reliable performance |
| `claude-opus-4-20250514` | Opus 4 | Flagship model |
| `claude-sonnet-4-6` | Latest Sonnet | Balanced quality/speed |
| `claude-sonnet-4-5-20250929` | Sonnet 4.5 | High-quality balance |
| `claude-sonnet-4-20250514` | Sonnet 4 | Reliable general-purpose |
| `claude-haiku-4-5-20251001` | Haiku 4.5 | Fast, efficient |
| `claude-3-7-sonnet-20250219` | Sonnet 3.7 | Extended reasoning |
| `claude-3-5-sonnet-20241022` | Legacy 3.5 | Proven track record |
| `claude-3-5-haiku-20241022` | Legacy Haiku 3.5 | Fast, affordable |
| `claude-3-opus-20240229` | Legacy Opus | Maximum quality (legacy) |

### Google Gemini

| Model | Best For |
|-------|----------|
| `gemini-3.1-pro` | Latest, highest quality |
| `gemini-3.1-pro-preview` | Latest preview |
| `gemini-3.1-flash-image-preview` | Image generation preview |
| `gemini-3.1-flash-lite-preview` | Fast and lightweight |
| `gemini-3-pro-preview` | Previous gen pro |
| `gemini-2.5-flash-lite` | Fast, efficient |
| `gemini-2.0-flash-lite` | Fast, cost-effective |

### DeepSeek

| Model | Best For |
|-------|----------|
| `deepseek-v4-flash` | Latest, fastest |
| `deepseek-v3.2-exp` | Experimental v3.2 |
| `deepseek-v3-250324` | Latest v3 stable |
| `deepseek-v3` | General-purpose |
| `deepseek-r1-0528` | Latest reasoning |
| `deepseek-r1` | Deep reasoning |
| `deepseek-chat` | Chat-optimized |

### xAI Grok

| Model | Best For |
|-------|----------|
| `grok-4-1-fast` | Latest, fastest |
| `grok-4-1-fast-reasoning` | Latest reasoning |
| `grok-4-1-fast-non-reasoning` | Latest non-reasoning |
| `grok-4-0709` | Stable Grok 4 |
| `grok-4` | Grok 4 |
| `grok-3` | General-purpose |
| `grok-3-fast` | Speed-optimized |
| `grok-3-mini` | Compact, efficient |
| `grok-3-mini-fast` | Ultra-fast compact |
| `grok-2-vision` | Vision model |

### Moonshot Kimi

| Model | Best For |
|-------|----------|
| `kimi-k2.5` | Latest Kimi |
| `kimi-k2-thinking` | Reasoning |
| `kimi-k2-thinking-turbo` | Fast reasoning |
| `kimi-k2-instruct-0905` | Instruction following |
| `kimi-k2-0905-preview` | Latest preview |
| `kimi-k2-0711-preview` | Preview version |
| `kimi-k2-turbo-preview` | Turbo preview |

### Zhipu GLM

| Model | Best For |
|-------|----------|
| `glm-5.1` | Latest GLM |
| `glm-5-turbo` | Fast GLM 5 |
| `glm-5` | GLM 5 |
| `glm-4.7` | High-quality |
| `glm-4.6` | General-purpose |
| `glm-4.5v` | Vision model |
| `glm-4.5-air` | Lightweight |
| `glm-4.5` | Balanced |
| `glm-4-plus` | Enhanced v4 |
| `glm-4-flash` | Fast v4 |
| `glm-4-air` | Lightweight v4 |

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
- Vision is supported on multimodal models (`gpt-4o`, `gpt-4o-mini`, `grok-2-vision`, Gemini vision models)
- Function calling works on most modern models (GPT-4+, Claude 3+)
- Streaming returns `chat.completion.chunk` objects via SSE
- `finish_reason` values: `"stop"` (complete), `"length"` (max tokens), `"tool_calls"` (function call), `"content_filter"` (filtered)

## Stateful Conversations — Recommended Endpoint

Use `POST /aichat2/conversations` for stateful, session-based chat with the full feature set: multi-modal content, agentic tool calls, SSE/NDJSON streaming, and CRUD operations on conversation history.

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "What is quantum computing?", "stateful": true}'
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Operation: `"chat"` (default), `"retrieve"`, `"retrieve_batch"`, `"update"`, `"delete"` |
| `model` | string | Model name (required for `action=chat`) |
| `question` | string | Plain-text user prompt (v1-compatible) |
| `message` | string/array | Multi-modal content: string or array of `{type, text/image_url/file_url}` blocks |
| `id` | string | Conversation ID — resume a session or target for retrieve/update/delete |
| `stateful` | boolean | Persist the conversation server-side (default: true) |
| `preset` | string | Name of a server-side system prompt preset |
| `references` | array | Reference URLs auto-converted to image or file blocks |
| `max_turns` | integer | Cap on agentic-loop iterations per request |
| `tool_results` | array | Resume payload for a conversation paused on `ask_user_question` |
| `messages` | array | Replacement message history (for `action=update` only) |
| `title` | string | Conversation title (for `action=update` only) |
| `offset` | integer | Pagination offset (for `action=retrieve_batch`) |
| `limit` | integer | Pagination limit (for `action=retrieve_batch`) |

### Multi-modal Example

```json
POST /aichat2/conversations
{
  "model": "gpt-4o",
  "message": [
    {"type": "text", "text": "What is in this image?"},
    {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
  ],
  "stateful": true
}
```

### Retrieve / Delete Conversation

```json
POST /aichat2/conversations
{"action": "retrieve", "id": "<conversation_id>"}

POST /aichat2/conversations
{"action": "delete", "id": "<conversation_id>"}
```

## Stateful Conversations — Legacy Endpoint

For basic stateful chat (legacy v1 compatibility), use `POST /aichat/conversations`:

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

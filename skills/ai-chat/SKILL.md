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
| `gpt-4o-search-preview` | Web search | GPT-4o with built-in web search |
| `gpt-4o-mini-search-preview` | Web search | Fast web search variant |
| `o1` | Reasoning | Complex reasoning tasks |
| `o1-mini` | Small reasoning | Quick reasoning |
| `o1-pro` | Pro reasoning | Advanced reasoning |
| `o3` | Reasoning | Latest reasoning model |
| `o3-mini` | Small reasoning | Efficient reasoning |
| `o4-mini` | Reasoning | Compact, fast reasoning |
| `gpt-5` | Latest gen | Next-gen intelligence |
| `gpt-5.4` | Gen 5.4 | High-performance next-gen |
| `gpt-5.5` | Gen 5.5 | Latest next-gen |
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
| `grok-4-1-fast` | Fast Grok 4 variant |
| `grok-3` | General-purpose |
| `grok-3-mini` | Compact, efficient |
| `grok-2-vision` | Vision tasks |

### Zhipu GLM

| Model | Best For |
|-------|----------|
| `glm-5.1` | Latest, high capability |
| `glm-4.7` | High quality |
| `glm-4.6` | General-purpose |
| `glm-4.5-air` | Fast, efficient |

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
| `reasoning_effort` | string | Effort level for reasoning models (`low`, `medium`, `high`); o1/o3/o4/gpt-5 series |
| `web_search_options` | object | Enable built-in web search on GPT-4o search-preview models |
| `response_format` | object | Force JSON output (`{"type": "json_object"}`) |
| `seed` | integer | Deterministic sampling seed |
| `stop` | string/array | Stop sequences (up to 4) |
| `frequency_penalty` | -2 to 2 | Penalize repeated tokens |
| `presence_penalty` | -2 to 2 | Penalize tokens already present |

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
- Use `reasoning_effort` (`"low"` / `"medium"` / `"high"`) to tune cost vs. quality on o1/o3/o4 and gpt-5 reasoning models
- Web search models (`gpt-4o-search-preview`, `gpt-4o-mini-search-preview`) accept an optional `web_search_options` object

## OpenAI Responses Endpoint

For stateless single-turn generation using OpenAI's Responses API format, use `POST /openai/responses`:

```bash
curl -X POST https://api.acedata.cloud/openai/responses \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1",
    "input": [{"role": "user", "content": "Summarize the Eiffel Tower in 3 sentences."}]
  }'
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model ID (REQUIRED) |
| `input` | array | Conversation turns as `{role, content}` objects (REQUIRED) |
| `stream` | boolean | Enable SSE streaming |
| `temperature` | number | Sampling temperature (0–2) |
| `max_tokens` | number | Token limit for the response |
| `tools` | array | Tools the model may call |
| `response_format` | object | Structured output format |
| `background` | boolean | Run the response in the background |

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

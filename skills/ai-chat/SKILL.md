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

Access GPT, Claude, Gemini, Grok, DeepSeek, Kimi, GLM, and reasoning models through AceDataCloud.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## OpenAI-Compatible Quick Start

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

## Stateful Conversations (OpenAPI)

The OpenAPI spec currently exposes two conversation endpoints:

| Endpoint | Status | Purpose |
|----------|--------|---------|
| `POST /aichat2/conversations` | Recommended | Next-generation stateful chat with multimodal input, tool calls, SSE/NDJSON streaming, and conversation CRUD actions |
| `POST /aichat/conversations` | Legacy compatibility | Older stateful endpoint using the simpler `question` + `model` request shape |

### Recommended: `/aichat2/conversations`

```json
POST /aichat2/conversations
{
  "action": "chat",
  "model": "gpt-4.1",
  "message": [
    {"type": "text", "text": "Summarize this image"},
    {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
  ],
  "stateful": true
}
```

#### `/aichat2/conversations` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Conversation operation: `chat`, `retrieve`, `retrieve_batch`, `update`, or `delete` |
| `id` | string | Conversation ID; optional for `chat`, required for `retrieve` / `update` / `delete` |
| `model` | string | Model name; required for `chat`, optional filter for `retrieve_batch` |
| `question` | string | Plain-text prompt in the older v1-compatible shape |
| `message` | string/array | Multimodal user content; plain string or content blocks such as text and `image_url` |
| `stateful` | boolean | Persist server-side conversation history (default behavior) |
| `references` | array | Reference URLs or documents to attach to the turn |
| `preset` | string | Server-side system prompt preset |
| `max_turns` | integer | Max agentic/tool-call loop iterations |
| `tool_results` | array | Resume payload for a conversation paused on `ask_user_question` |
| `messages` | array | Full replacement message history for `update` |
| `title` | string | Conversation title for `update` |
| `user_id` | string | Filter by user when using `retrieve_batch` |
| `application_id` | string | Filter by application when using `retrieve_batch` |
| `model_group` | string | Provider filter for `retrieve_batch`: `chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, `deepseek` |
| `offset` | integer | Pagination offset for `retrieve_batch` |
| `limit` | integer | Pagination limit for `retrieve_batch` |

### Legacy: `/aichat/conversations`

```json
POST /aichat/conversations
{
  "model": "gpt-4.1",
  "question": "What is quantum computing?",
  "stateful": true
}
```

#### `/aichat/conversations` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Conversation ID for continuing a session |
| `model` | string | Model name |
| `preset` | string | Preset/system prompt |
| `question` | string | Prompt or question to answer |
| `stateful` | boolean | Maintain history server-side |
| `references` | array | Additional context documents or URLs |

## Current `/aichat2` Model Families

### OpenAI + reasoning

`gpt-4`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-2024-05-13`, `gpt-4o-all`, `gpt-4o-image`, `gpt-4o-mini`, `gpt-5-all`, `gpt-5.1-all`, `gpt-5.2-pro`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-image-1`, `o1`, `o1-mini`, `o1-pro`, `o3`, `o3-mini`, `o3-pro`, `o4-mini`

### Anthropic Claude

`claude-3-5-haiku-20241022`, `claude-3-5-sonnet-20240620`, `claude-3-5-sonnet-20241022`, `claude-3-7-sonnet-20250219`, `claude-3-haiku-20240307`, `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-haiku-4-5-20251001`, `claude-opus-4-1-20250805`, `claude-opus-4-20250514`, `claude-opus-4-5-20251101`, `claude-opus-4-6`, `claude-opus-4-7`, `claude-sonnet-4-20250514`, `claude-sonnet-4-5-20250929`, `claude-sonnet-4-6`

### Google Gemini

`gemini-2.0-flash-lite`, `gemini-2.5-flash-lite`, `gemini-3-pro-preview`, `gemini-3.1-flash-image-preview`, `gemini-3.1-flash-lite-preview`, `gemini-3.1-pro`, `gemini-3.1-pro-preview`

### xAI Grok

`grok-2-vision`, `grok-2-vision-1212`, `grok-3`, `grok-3-fast`, `grok-3-mini`, `grok-3-mini-fast`, `grok-4`, `grok-4-0709`, `grok-4-1-fast`, `grok-4-1-fast-non-reasoning`, `grok-4-1-fast-reasoning`

### DeepSeek

`deepseek-chat`, `deepseek-r1`, `deepseek-r1-0528`, `deepseek-reasoner`, `deepseek-v3`, `deepseek-v3-250324`, `deepseek-v3.2-exp`, `deepseek-v4-flash`

### Moonshot Kimi

`kimi-k2-0711-preview`, `kimi-k2-0905-preview`, `kimi-k2-instruct-0905`, `kimi-k2-thinking`, `kimi-k2-thinking-turbo`, `kimi-k2-turbo-preview`, `kimi-k2.5`

### Zhipu GLM

`glm-3-turbo`, `glm-4-air`, `glm-4-flash`, `glm-4-plus`, `glm-4.5`, `glm-4.5-air`, `glm-4.5v`, `glm-4.6`, `glm-4.7`, `glm-5`, `glm-5-turbo`, `glm-5.1`

> Legacy `/aichat/conversations` keeps a wider snapshot-heavy model enum, including dated GPT and o-series variants such as `gpt-5.5`, `gpt-5.4-pro`, `gpt-4o-2024-11-20`, `o1-2024-12-17`, `o3-2025-04-16`, and `o4-mini-2025-04-16`.

## Features

### Streaming

- `/v1/chat/completions` supports standard OpenAI SSE streaming
- `/aichat2/conversations` additionally supports SSE/NDJSON streaming for stateful conversations and tool loops

### Function Calling and Tools

- OpenAI-compatible `tools` / `tool_choice` work on `/v1/chat/completions`
- `/aichat2/conversations` supports built-in tools and connection-bound MCP tools during agentic conversations

### Vision and multimodal input

- Use multimodal-capable models such as `gpt-4o`, `gpt-4o-mini`, `gpt-4o-image`, `grok-2-vision`, or Gemini image-capable variants
- `/aichat2/conversations` accepts content blocks such as text plus `image_url`

## Gotchas

- Prefer `POST /aichat2/conversations` for new stateful work; keep `/aichat/conversations` only for legacy compatibility
- `question` is the simple v1-style field; `message` is the richer multimodal field on `/aichat2/conversations`
- `action=retrieve_batch` is how you list/filter stored conversations
- `model_group` filters only work on `/aichat2/conversations`
- Model availability differs between `/aichat2/conversations` and legacy `/aichat/conversations`; choose the endpoint that matches the model enum you need
- For stateless chat completions with existing OpenAI SDKs, keep using `/v1/chat/completions`

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.

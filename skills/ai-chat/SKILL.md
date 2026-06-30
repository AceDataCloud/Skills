---
name: ai-chat
description: Access 50+ LLM models through AceDataCloud's unified chat APIs. Use when you need OpenAI-compatible chat/responses calls or the newer `/aichat2/conversations` API across GPT, Claude, Gemini, Grok, Kimi, GLM, and DeepSeek models. Supports streaming, multimodal input, and tool calling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Works with OpenAI-compatible SDKs against the `/openai/*` routes.
---

# AI Chat — Unified LLM Gateway

AceDataCloud exposes two documented chat surfaces:

| Endpoint | Use For |
|----------|---------|
| `POST /aichat2/conversations` | Recommended stateful / multimodal / agentic conversations |
| `POST /aichat/conversations` | Legacy conversation endpoint |
| `POST /openai/chat/completions` | OpenAI-compatible stateless chat completions |
| `POST /openai/responses` | OpenAI-compatible responses API |

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

### Recommended: stateful conversations

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: ******ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4.1","question":"Summarize the latest release notes.","stateful":true}'
```

### OpenAI-compatible SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-token-here",
    base_url="https://api.acedata.cloud/openai"
)

response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
```

## Currently Documented Model Families

The OpenAPI specs expose a broad, fast-moving model catalog. Representative current
models include:

| Family | Current examples |
|--------|------------------|
| OpenAI / reasoning | `gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4`, `gpt-5.4-pro`, `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini`, `o1`, `o3`, `o4-mini` |
| OpenAI free-tier chat-completions | `gpt-5.5:free`, `gpt-5:free`, `gpt-4.1:free`, `gpt-4o:free`, `gpt-4o-mini:free`, `gpt-oss:free` |
| Claude | `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-opus-4-5-20251101`, `claude-sonnet-4-6`, `claude-sonnet-4-5-20250929`, `claude-sonnet-4-20250514`, `claude-haiku-4-5-20251001`, `claude-3-7-sonnet-20250219` |
| Gemini | `gemini-3.1-pro`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-image-preview`, `gemini-3.1-flash-lite-preview`, `gemini-3-pro-preview`, `gemini-2.5-flash-lite`, `gemini-2.0-flash-lite` |
| Grok | `grok-4`, `grok-4-0709`, `grok-3`, `grok-3-fast` |
| DeepSeek | `deepseek-r1`, `deepseek-r1-0528`, `deepseek-v3`, `deepseek-v3-250324`, `deepseek-v3.2-exp`, `deepseek-v4-flash` |
| Kimi | `kimi-k2.5`, `kimi-k2-thinking-turbo`, `kimi-k2-thinking`, `kimi-k2-instruct-0905`, `kimi-k2-0905-preview`, `kimi-k2-turbo-preview`, `kimi-k2-0711-preview` |
| GLM | `glm-5.2`, `glm-5.1`, `glm-5`, `glm-5-turbo`, `glm-4.7`, `glm-4.6`, `glm-4.5`, `glm-4.5v`, `glm-3-turbo` |

`/aichat2/conversations` also accepts `model_group` values
`chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, and `deepseek`.

## OpenAI-Compatible Chat

```json
POST /openai/chat/completions
{
  "model": "gpt-4.1",
  "messages": [{"role": "user", "content": "Write a haiku about observability."}],
  "stream": true,
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

Common parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | One of the documented OpenAI-compatible models |
| `messages` | array | Standard OpenAI chat message list |
| `temperature` / `top_p` | number | Sampling controls |
| `max_tokens` | integer | Output cap |
| `stream` | boolean | Enable SSE streaming |
| `tools` / `tool_choice` | array / string-object | Function-calling controls |
| `service_tier` | string | Processing tier (`auto`, `default`, `flex`, `scale`, `priority`) |

## Stateful / Agentic Conversations

`POST /aichat2/conversations` generalizes the legacy conversation API with
multimodal user content, CRUD-style actions, and server-side conversation state.

```json
POST /aichat2/conversations
{
  "action": "chat",
  "model": "claude-sonnet-4-6",
  "message": [
    {"type": "text", "text": "Describe this image."},
    {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}}
  ],
  "stateful": true,
  "allowed_skills": ["google-search"],
  "allowed_mcp_servers": ["mcp-google-search"]
}
```

Useful parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | `chat`, `retrieve`, `retrieve_batch`, `update`, `delete` |
| `model` | string | Model name |
| `question` | string | Simple text prompt |
| `message` | string or array | Multimodal content using `text`, `image_url`, or `file_url` items |
| `stateful` | boolean | Keep conversation history server-side |
| `references` | array | Extra context documents |
| `preset` | string | Preset/system prompt |
| `max_turns` | integer | Trim retained turn history |
| `allowed_skills` / `allowed_mcp_servers` | array | Restrict tool-use scope |
| `unattended_policy` | object | Tool-use permission policy |
| `tool_results` | array | Return results for previously requested tool calls |
| `model_group` | string | Family selector (`chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, `deepseek`) |
| `offset` / `limit` | integer | Pagination for retrieval actions |
| `callback_url` / `async` | string / boolean | Async execution |

## Gotchas

- The documented OpenAI-compatible routes live under `/openai/*`, not `/v1/*`.
- `POST /aichat2/conversations` is the recommended stateful endpoint; `POST /aichat/conversations` remains for legacy clients.
- `message` on `/aichat2/conversations` can be multimodal (`text`, `image_url`, `file_url`); plain `question` still works for simple text prompts.
- `action` on `/aichat2/conversations` is not chat-only — it also supports `retrieve`, `retrieve_batch`, `update`, and `delete`.
- Free-tier model variants such as `gpt-5.5:free` are documented on `/openai/chat/completions`.

---
name: ai-chat
description: Access GPT, Claude, Gemini, Grok, DeepSeek, Kimi, GLM, and OpenAI reasoning models through AceDataCloud conversation APIs. Supports stateful chat, multimodal inputs, and conversation management.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# AI Chat — Unified LLM Gateway

Access GPT, Claude, Gemini, Grok, DeepSeek, Kimi, and GLM models through AceDataCloud's conversation APIs.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1", "question": "Explain quantum computing in simple terms."}'
```

## Endpoints

| Endpoint | Status | Purpose |
|----------|--------|---------|
| `POST /aichat2/conversations` | Recommended | Stateful chat, multimodal inputs, resume/retrieve/update/delete flows |
| `POST /aichat/conversations` | Legacy | Simpler text-only conversation flow kept for compatibility |

## Available Model Families

`/aichat2/conversations` supports a large cross-provider model catalog, including dated aliases. Common public families include:

| Family | Representative models |
|--------|------------------------|
| OpenAI GPT & reasoning | `gpt-4.1`, `gpt-4o`, `gpt-5-all`, `gpt-5.1-all`, `gpt-5.2-pro`, `o1`, `o3`, `o4-mini` |
| Anthropic Claude | `claude-sonnet-4-20250514`, `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-opus-4-7`, `claude-haiku-4-5-20251001` |
| Google Gemini | `gemini-2.0-flash-lite`, `gemini-2.5-flash-lite`, `gemini-3-pro-preview`, `gemini-3.1-pro`, `gemini-3.1-flash-image-preview` |
| xAI Grok | `grok-3`, `grok-3-fast`, `grok-3-mini`, `grok-4`, `grok-4-1-fast`, `grok-4-1-fast-reasoning` |
| DeepSeek | `deepseek-chat`, `deepseek-r1`, `deepseek-r1-0528`, `deepseek-v3`, `deepseek-v4-flash` |
| Moonshot Kimi | `kimi-k2-0711-preview`, `kimi-k2-0905-preview`, `kimi-k2-instruct-0905`, `kimi-k2-thinking`, `kimi-k2.5` |
| Zhipu GLM | `glm-3-turbo`, `glm-4-air`, `glm-4-flash`, `glm-4.5`, `glm-4.6`, `glm-4.7`, `glm-5`, `glm-5.1` |

## Recommended Workflow (`/aichat2/conversations`)

### 1. Chat with plain text

```json
POST /aichat2/conversations
{
  "model": "claude-sonnet-4-6",
  "question": "Summarize the latest release notes."
}
```

`action` defaults to `"chat"`.

### 2. Resume a stateful conversation

```json
POST /aichat2/conversations
{
  "id": "conv_123",
  "model": "gpt-4.1",
  "question": "Continue from the previous answer.",
  "stateful": true
}
```

### 3. Send multimodal input

```json
POST /aichat2/conversations
{
  "model": "gemini-3.1-pro",
  "message": [
    {"type": "text", "text": "Describe this file and image."},
    {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}},
    {"type": "file_url", "file_url": {"url": "https://example.com/report.pdf"}}
  ]
}
```

### 4. Retrieve, list, update, or delete conversations

```json
POST /aichat2/conversations
{
  "action": "retrieve",
  "id": "conv_123",
  "model": "gpt-4.1"
}
```

Other supported actions:
- `retrieve_batch` — list conversation summaries with optional filters
- `update` — patch `title` and/or `messages`
- `delete` — remove a conversation

## Parameters (`/aichat2/conversations`)

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | `chat` (default), `retrieve`, `retrieve_batch`, `update`, or `delete` |
| `id` | string | Conversation ID. Required for `retrieve`, `update`, and `delete`; optional for resumed `chat` |
| `model` | string | Model name. Required for `chat`; optional filter for `retrieve_batch` |
| `question` | string | Plain-text prompt. Ignored when `message` or `tool_results` is supplied |
| `message` | string/array | User content for this turn. Use a string or an array of `text`, `image_url`, and `file_url` blocks |
| `stateful` | boolean | Persist the conversation server-side (defaults to `true`) |
| `references` | array | URLs to attach as extra context. Image URLs become `image_url` blocks; others become `file_url` blocks |
| `preset` | string | Server-side preset / system prompt |
| `max_turns` | integer | Cap agentic-loop iterations for the request |
| `tool_results` | array | Resume a paused `ask_user_question` turn with `{tool_use_id, output, is_error?}` |
| `messages` | array | Replacement message history for `action: "update"` |
| `title` | string | Conversation title for `action: "update"` |
| `user_id` | string | Filter for `retrieve_batch` |
| `application_id` | string | Filter for `retrieve_batch` |
| `model_group` | string | Provider-family filter for `retrieve_batch`: `chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, `deepseek` |
| `offset` | integer | Pagination offset for `retrieve_batch` |
| `limit` | integer | Pagination limit (`1`-`100`) for `retrieve_batch` |

## Legacy Endpoint (`/aichat/conversations`)

Use the legacy endpoint only when you need its older, simpler request shape:

```json
POST /aichat/conversations
{
  "model": "gpt-5.4",
  "question": "What changed in this document?",
  "stateful": true,
  "references": ["https://example.com/spec.pdf"]
}
```

Legacy request fields:
- `id`
- `model`
- `preset`
- `question`
- `stateful`
- `references`

## Gotchas

- Prefer `POST /aichat2/conversations` for all new integrations; keep `POST /aichat/conversations` only for compatibility
- `question` is ignored when `message` is present, and both are ignored when `tool_results` resumes a paused conversation
- `message` blocks support `text`, `image_url`, and `file_url`; use them for vision and file inputs
- `retrieve_batch` returns conversation summaries rather than the full message history
- `limit` is capped at `100`
- The available model list changes over time; dated aliases may remain available alongside the representative models listed above

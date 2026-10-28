---
name: ai-chat
description: Access 50+ LLM models through AceDataCloud's unified chat APIs. Use when you need native Claude Messages, native Gemini audio analysis, OpenAI-compatible chat/responses calls, text embeddings for search or RAG, or stateful conversations and scheduled agent tasks across GPT, Claude, Gemini, Grok, Kimi, GLM, and DeepSeek models. Supports streaming, multimodal input, and tool calling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (get an API key at https://platform.acedata.cloud/console/applications). Works with OpenAI-compatible SDKs against the `/openai/*` routes and public `/v1/*` aliases.
---

# AI Chat — Unified LLM Gateway

AceDataCloud exposes the following documented chat surfaces:

| Endpoint | Use For |
|----------|---------|
| `POST /aichat2/conversations` | Recommended stateful / multimodal / agentic conversations |
| `POST /aichat/conversations` | Legacy conversation endpoint |
| `POST /openai/chat/completions` (public alias `/v1/chat/completions`) | OpenAI-compatible stateless chat completions |
| `POST /openai/responses` (public alias `/v1/responses`) | OpenAI-compatible responses API |
| `POST /kimi/chat/completions` (public alias `/v1/chat/completions`) | Kimi Chat Completions with model-specific reasoning controls |
| `POST /v1/messages` (alias `/claude/messages`) | Native Claude Messages, including thinking and tool calls |
| `POST /v1/messages/count_tokens` (alias `/claude/messages/count_tokens`) | Count native Claude input tokens without generating output |
| `POST /v1beta/models/{model}:generateContent` | Native Gemini content generation, including audio input |
| `POST /v1beta/models/{model}:streamGenerateContent?alt=sse` | Native Gemini SSE streaming |

## First-time setup

1. Install the official Skill with `clawhub install @acedatacloud/ai-chat`. Check that the ClawHub publisher is **@acedatacloud**.
2. Sign in at [AceDataCloud → Applications](https://platform.acedata.cloud/console/applications), open **General application**, and check AI Chat access, balance, and current pricing. Copy its API key, or select **Manage Keys → Create** for a separate key. Copy the key value without `Bearer `; a `platform-...` management token is not a service API key.
3. If you enable **Allowed APIs** restrictions, include `/aichat2/conversations` for the first example; other chat routes need their own access. Advanced workflows below may call additional routes.
4. On the OpenClaw Gateway host, put `ACEDATACLOUD_API_TOKEN=your_api_key_here` in `~/.openclaw/.env`, then restart the Gateway and start a new session. For a direct terminal test, run `export ACEDATACLOUD_API_TOKEN="your_api_key_here"` in that shell. Never put the key in a prompt or commit an `.env` file.
5. Run the **Quick Start** below. If this workflow returns a task ID, query that same task until it finishes; do not submit the same billable request again just to check progress.

[Illustrated key setup, first run, and troubleshooting](https://github.com/AceDataCloud/Skills#first-run-with-clawhub-and-openclaw) · [Token details](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md)

## Quick Start

### Recommended: stateful conversations

```bash
curl -X POST https://api.acedata.cloud/aichat2/conversations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4.1","question":"Summarize the latest release notes.","stateful":true}'
```

### OpenAI-compatible SDK

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["ACEDATACLOUD_API_TOKEN"],
    base_url="https://api.acedata.cloud/openai"
)

response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
```

### Dify: OpenAI-API-compatible provider

Set **Base URL** to `https://api.acedata.cloud/v1`, **API Key** to your AceDataCloud service token, **model** to `gpt-5.5` (or another supported chat model), and **model type** to LLM. Select **conversation type** Chat and **API type** Chat Completions. Dify appends `/chat/completions` itself; do not use `/openai/v1` or include the full endpoint in Base URL. Test the connection before selecting the model in a Workflow / Chatflow LLM node.

## Currently Documented Model Families

The OpenAPI specs expose a broad, fast-moving model catalog. Representative current
models include:

| Family | Current examples |
|--------|------------------|
| OpenAI / reasoning | `gpt-6-astra`, `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.6-sol-fast`, `gpt-5.6-sol`, `gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4`, `gpt-5.4-pro`, `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini`, `o1`, `o3`, `o4-mini` |
| OpenAI free-tier chat-completions | `gpt-5.5:free`, `gpt-5:free`, `gpt-4.1:free`, `gpt-4o:free`, `gpt-4o-mini:free`, `gpt-oss:free` |
| Claude | `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-fable-5-1`, `claude-fable-5`, `claude-opus-5`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`, `claude-opus-4-5-20251101`, `claude-sonnet-4-6`, `claude-sonnet-4-5-20250929`, `claude-sonnet-4-20250514`, `claude-haiku-4-5-20251001`, `claude-3-7-sonnet-20250219` |
| Gemini | `gemini-4-argon`, `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.1-pro`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite-preview`, `gemini-3-pro-preview`, `gemini-2.5-flash-lite`, `gemini-2.0-flash-lite` |
| Grok | `grok-4.7`, `grok-4.5`, `grok-4`, `grok-4-0709`, `grok-3`, `grok-3-fast` |
| DeepSeek | `deepseek-v4.1-flash`, `deepseek-v4-pro`, `deepseek-v4-flash`, `deepseek-r1`, `deepseek-r1-0528`, `deepseek-v3`, `deepseek-v3-250324`, `deepseek-v3.2-exp` |
| Kimi | `kimi-k3.1-pro`, `kimi-k3`, `kimi-k2.6`, `kimi-k2.5`, `kimi-k2-thinking-turbo`, `kimi-k2-thinking` |
| GLM | `glm-5.2`, `glm-5.1`, `glm-5`, `glm-5-turbo`, `glm-4.7`, `glm-4.6`, `glm-4.5`, `glm-4.5v`, `glm-3-turbo` |

When the user asks for a recommended model, read the current public `GET https://platform.acedata.cloud/api/v1/models/` response and prefer suitable entries with `recommended=true`. This is an editorial preference, not an access grant or a new API capability; `recommended=false` does not retire a model. Check the selected model's supported route and current pricing before calling it, and do not silently replace a model the user explicitly selected.

Catalog discovery follows the requesting visitor's IP, not the display language or a `?country=` override. Mainland-China views hide marked Claude, OpenAI, Gemini and Grok chat catalog entries. Check media visibility separately: OpenAI image generation/editing and companion guides are also hidden in mainland China. Read the service's `image_unavailable_regions` and API/document `unavailable_regions`; do not hide unrelated media or the entire mixed service based on chat-only or image-only restrictions. Raw catalog responses may retain marked rows, so presence alone is not visibility. Honor the current public visibility when recommending models; do not use a cached global list to advertise region-hidden chat or images. A missing catalog entry is not evidence of retirement or revoked API access: this presentation filtering does not change API routing or billing. Report the discovery limitation, check actual account access and pricing, and do not silently replace a user-selected model.

To select `gpt-5.6-sol-fast`, send that exact public model ID on Chat Completions, Responses, Messages, or either conversation endpoint above. It is listed in the public model/pricing catalog with vision capability, but has no public model introduction. Check account eligibility and current pricing before requesting it; catalog visibility does not guarantee access. Its pricing rules use a higher tier when total input exceeds 272,000 (not at exactly 272,000). For Chat Completions and Responses, input totals already include reported cache tokens; for Messages, add the separately reported cache-read and cache-creation tokens to uncached input before checking this threshold. Do not silently substitute `gpt-5.6-sol` after an access or parameter error; protocol-specific features remain model-dependent.

`gpt-6.1-sol` supports `low`, `medium`, `high`, `xhigh`, and `max` reasoning effort; do not send `none` or `minimal`. During its first week, access requires verified ACE T1+ holdings or an access grant. Check the platform access response for the opening time.

`claude-opus-5-5` is available on Claude Chat Completions (`POST /v1/chat/completions`) and native Messages (`POST /v1/messages`). Messages remains the recommended route for complete thinking blocks and native tool semantics. For Chat Completions, use `n=1`, omit non-default `temperature` and `top_p`, and use `tool_choice: "auto"` rather than forcing a tool. `claude-sonnet-5-5` remains a Messages model. Check the current public model list and account access before using another route; cross-protocol pricing rules do not establish identical feature support.

`/aichat2/conversations` also accepts `model_group` values
`chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, and `deepseek`.

> **Image-generating models are not chat models.** Names ending in `-image`
> (e.g. `gemini-*-image`, `gpt-4o-image`) are image-generation models; they
> do not work on the OpenAI-compatible chat, Claude Messages, or conversation
> routes. Generate images through the dedicated endpoints instead — Gemini via
> `POST /v1beta/models/{model}:generateContent`, or `/nano-banana/images`.

## Token billing across compatible protocols

1. Before submitting, check the selected route's current public model list, account access, key restrictions and current model pricing. A settlement rule is not a publication or access grant. Keep the requested public model ID; do not silently substitute another model or route after an error.
2. For accepted compatible-model requests, billing follows the model's actual input, output and cache usage. Switching between Chat Completions, Responses and Messages does not turn token billing into a fixed per-request fee or guarantee the same price across protocols.
3. Read the actual response `usage` using that protocol's fields:

   | Protocol | Input/cache accounting |
   |----------|------------------------|
   | Chat Completions | `usage.prompt_tokens` includes reported cache tokens. Treat `usage.prompt_tokens_details.cached_tokens` as a subset, not extra input; the reported cache portion uses its corresponding cache price. |
   | Responses | `usage.input_tokens` includes reported cache tokens. Treat reported cache tokens in `usage.input_tokens_details` as a subset, not extra input; the cache portion uses its corresponding cache price. |
   | Messages | `usage.input_tokens` excludes the separately reported `usage.cache_read_input_tokens` and `usage.cache_creation_input_tokens`. Account for these dimensions separately at their corresponding prices. If `usage.cache_creation` reports 5-minute/1-hour details, these partition creation usage; do not add them again to the creation total. |

4. Check the console's current model prices and the returned `usage.cost` for the actual charge. Report only returned usage/cost fields; missing cache or cost data is not evidence of a cache hit or a free request. Do not invent a charge from a reference USD price.

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

## Kimi Chat Completions

1. Check current Kimi access, pricing and **Allowed APIs** restrictions for `/kimi/chat/completions` before submitting with the same AceDataCloud service Bearer token. `kimi-k3.1-pro` and `kimi-k3` remain available; choose recommendations from the current public model catalog's `recommended` flag, not a fixed model preference. Do not silently replace an explicitly selected model.
2. Send `model` and `messages` to `POST /kimi/chat/completions` (public alias `/v1/chat/completions`). K3.1 Pro supports top-level `reasoning_effort` values `low`, `high` and `max`. Both K3.1 Pro and K3 always enable reasoning; do not send settings to disable it. For K3, use `max` or omit the field rather than relying on other values. K2.6 uses `thinking`, not this effort control.
3. For K3.1 Pro image understanding, use `image_url` content blocks alongside text in `messages`. The official context specification is up to 1,048,576 tokens, not a guaranteed per-request platform limit. Check the chosen route's own model list before using Responses or Messages; shared pricing rules do not establish protocol support.
4. Read text from `choices[].message.content`. Preserve the complete assistant message, including `reasoning_content` and `tool_calls` when returned, unchanged in subsequent turns and tool-result exchanges. Execute only authorized tools and verify their results; do not fabricate response or reasoning fields.
5. Read actual `usage` and check current input, output and cache-hit pricing in the public model catalog. Do not assume a cache hit or convert the official model price directly into an account charge.

```bash
curl -X POST https://api.acedata.cloud/kimi/chat/completions \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"kimi-k3.1-pro",
    "messages":[{"role":"user","content":"Review this code and suggest a repair plan."}],
    "reasoning_effort":"low"
  }'
```

`/aichat2/conversations` also lists `kimi-k3.1-pro`; use its conversation payload below rather than assuming the Kimi-specific effort field is available on that route.

## Native Gemini Generate Content

Use the native Gemini routes for audio analysis with the same AceDataCloud Bearer token. Confirm Gemini API access, current pricing, the selected public model, and any **Allowed APIs** restrictions before submitting. These routes use `contents` and `parts`, not OpenAI `messages`.

1. Put the prompt and audio in a user content item's `parts`. Use `inlineData` with `mimeType` and base64-encoded `data`, or `fileData` with `mimeType` and `fileUri`. Text, image and video inputs, thinking configuration and custom function declarations are also accepted on this native surface; this is not a promise of support on OpenAI-compatible or conversation routes.
2. For `fileData.fileUri`, use a file directly accessible over HTTPS without login. A signed URL must remain valid for the entire request. Replace `HTTPS_AUDIO_URL` below with the real file URL and set the actual audio MIME type; the example assumes WAV.
3. Set the client's total request timeout for the file size and workload. Non-streaming audio analysis returns only after model processing completes and may exceed 90 seconds; 90 seconds is not a server processing limit. If the client disconnects, the server may still be processing: do not automatically resubmit a potentially billable request.
4. Submit the native request below. For Gemini 3.x Flash thinking models, keep `generationConfig.maxOutputTokens` at least 512 so reasoning does not consume the entire output budget.

```json
POST /v1beta/models/gemini-3.5-flash:generateContent
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "Summarize this audio."},
        {"fileData": {"mimeType": "audio/wav", "fileUri": "HTTPS_AUDIO_URL"}}
      ]
    }
  ],
  "generationConfig": {"maxOutputTokens": 1024}
}
```

For streaming, send the same native body to `POST /v1beta/models/{model}:streamGenerateContent?alt=sse` and consume SSE events. Audio output, built-in tools (`codeExecution`, `googleSearch`, `urlContext`) and explicit context caching (`cachedContent`) have no uniform availability guarantee: use the selected model's actual response and surface errors rather than promising support or assuming those fields always return 400.

## OpenAI Embeddings

Use `POST /openai/embeddings` (public alias `/v1/embeddings`) with the same AceDataCloud Bearer token for semantic search or RAG, not chat generation. Choose `text-embedding-3-small` or `text-embedding-3-large`; `model` and `input` are required.

```json
POST /openai/embeddings
{
  "model": "text-embedding-3-small",
  "input": "Hello!"
}
```

`text-embedding-ada-002` is retired; do not send new requests with that model. Rebuild existing indexes with the selected supported model before querying them; do not mix vectors from different models in one index or silently switch models for an existing index.

## Native Claude Messages

Use `POST /v1/messages` (public alias `/claude/messages`) for native Claude calls, including `claude-opus-5-5` and `claude-sonnet-5-5`. Authenticate with the same AceDataCloud Bearer token. Required fields are `model`, `messages`, and `max_tokens`; use top-level `system` for system instructions.

```bash
curl -X POST https://api.acedata.cloud/v1/messages \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"claude-sonnet-5-5",
    "messages":[{"role":"user","content":"Review this implementation plan."}],
    "max_tokens":8192,
    "thinking":{"type":"adaptive"},
    "output_config":{"effort":"high"}
  }'
```

- Send `thinking`, `output_config`, effort, sampling parameters, and extension fields unchanged. The platform does not enforce a frozen per-model enum or rewrite thinking modes; the selected model decides which values and combinations it accepts and its parameter errors are returned to the caller. Pass-through is not a promise of feature support across models or protocols.
- Common `thinking.type` values are `adaptive`, `enabled`, and `disabled`; newer modes such as `between_tools`, fixed `budget_tokens`, and whether thinking can be disabled depend on the model. Common effort values include `low`, `medium`, `high`, `xhigh`, and `max`, but are not a closed enum.
- `thinking.display="summarized"` returns a readable summary, not raw reasoning. `omitted` hides the thinking text while retaining its opaque `signature`. Beta `updates` requests short progress updates between tool calls with hidden reasoning; send `anthropic-beta: thinking-display-updates-2026-08-18` and `thinking.display="updates"`. The value and beta header are forwarded, not rewritten to `summarized`; actual support and output depend on the selected model.
- Thinking shares the `max_tokens` budget with final text. Display settings do not disable thinking or reduce its token billing. Increase the budget or lower supported effort if the final answer is empty or truncated.
- In multi-turn/tool-use conversations, return complete assistant thinking blocks and signatures unchanged. Never invent or edit a signature. Cross-protocol handling of `redacted_thinking` depends on the model service; surface errors instead of dropping blocks or silently changing the request.

To estimate input size, send the native input to `POST /v1/messages/count_tokens` (alias `/claude/messages/count_tokens`) with the same model, messages, and applicable system/tools/thinking fields. Read `input_tokens`; this endpoint generates no model output and consumes no quota. Its thinking configuration is extensible too; do not substitute a locally hard-coded model validator.

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
| `max_turns` | integer | Agent iterations per request: 1–500, default 500; not retained history |
| `allowed_skills` / `allowed_mcp_servers` | array | Restrict tool-use scope |
| `unattended_policy` | object | Tool-use permission policy |
| `tool_results` | array | Return results for previously requested tool calls |
| `model_group` | string | Family selector (`chatgpt`, `claude`, `gemini`, `grok`, `kimi`, `glm`, `deepseek`) |
| `offset` / `limit` | integer | Pagination for retrieval actions |
| `callback_url` / `async` | string / boolean | Async execution |

Set `max_turns` deliberately for the expected tool chain. Each iteration is a model call, not a history-retention setting; `max_turns: 1` requests a single answer without tool calls. Omitting it allows up to 500 iterations, not a guarantee that all will run.

## Scheduled Agent Tasks

Use `POST /aichat2/scheduled-tasks` on `https://api.acedata.cloud` with the same service Bearer token and aichat API access. All operations use POST with an `action`; this is not a platform-management-token endpoint.

1. Confirm the prompt, model, accounts, permitted tools, schedule, IANA timezone and spending scope before creating or enabling a task. Runs are billable and unattended: finish third-party authorization interactively first and remove ambiguities that would require a follow-up question. Use the [unattended confirmation guard](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/unattended.md) for supported write helpers; scheduling is not blanket permission to publish or send.
2. Choose `schedule.type`: `cron` requires a five-field `cron` expression and `tz`; `interval` requires `interval_seconds` and `tz`; `once` requires a Unix-seconds `at` and `tz`. Use an IANA zone such as `UTC`, not `UTC+8`. The saved timezone governs Cron wall-clock time even if the device timezone changes.
3. Put the conversation prompt/model in `template`. Optional `template.max_turns` is 1–500, default 500, and caps iterations **per run**, not schedule frequency. Each model call is billed by actual usage; a run can end earlier due to timeout, authorization or other execution conditions. A run lasts at most 15 minutes. Set an explicit Unix-seconds `ends_at` when needed; otherwise tasks stop three months after creation.
4. After creation, retain the returned task `id`. List with `action="retrieve_batch"`; inspect executions with `action="retrieve_runs"` and that `id`, or `action="retrieve_runs_batch"` for all tasks (optional `status`, `offset`, `limit`). Read each run's `status`, `error_code` and `conversation_id`; retrieve the conversation through `/aichat2/conversations` for the full result. Task `state="enabled"` (shown as “running” in the list) is not evidence of a successful run.
5. Consecutive AI execution failures **do not auto-pause** the task: the next scheduled run still attempts execution. Auto-pause occurs after **five consecutive handoff failures** to the execution service, not five failed AI runs. Insufficient balance fails a run; a request for user input/consent fails with `awaiting_user_input`. Diagnose the run history, fix balance/authorization/prompt issues, and explicitly pause recurring failures to prevent further attempts.
6. Pause with `action="update"`, the task `id` and `state="disabled"`; resume with `state="enabled"` only after confirmation. Delete with `action="delete"` and `id` only after confirming permanent removal.

Creation payload (preview locally and obtain confirmation before sending):

```json
POST /aichat2/scheduled-tasks
{
  "action": "create",
  "name": "Daily AI news summary",
  "schedule": {"type": "cron", "cron": "0 9 * * *", "tz": "UTC"},
  "template": {
    "model": "gpt-4o-mini",
    "question": "Today is {{date}}. Search and summarize the three most important AI news items. Do not publish or send messages.",
    "max_turns": 5
  }
}
```

```json
POST /aichat2/scheduled-tasks
{"action": "retrieve_runs", "id": "TASK_ID"}
```

```json
POST /aichat2/scheduled-tasks
{"action": "update", "id": "TASK_ID", "state": "disabled"}
```

## Gotchas

- OpenAI-compatible routes under `/openai/*` retain public aliases `/v1/chat/completions`, `/v1/responses`, and `/v1/embeddings`. For clients that append `/chat/completions`, use Base URL `https://api.acedata.cloud/v1` (not `/openai/v1`); the SDK example above keeps the existing `/openai` base.
- `POST /aichat2/conversations` is the recommended stateful endpoint; `POST /aichat/conversations` remains for legacy clients.
- `message` on `/aichat2/conversations` can be multimodal (`text`, `image_url`, `file_url`); plain `question` still works for simple text prompts.
- `action` on `/aichat2/conversations` is not chat-only — it also supports `retrieve`, `retrieve_batch`, `update`, and `delete`.
- Free-tier model variants such as `gpt-5.5:free` are documented on `/openai/chat/completions`.

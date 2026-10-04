<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Gemini AI

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/gemini/chat/completions` | `n`, `model`, `stream`, `messages`, `max_tokens`, `temperature`, `response_format`, `top_p`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `max_completion_tokens`, `logprobs`, `top_logprobs`, `stream_options`, `parallel_tool_calls`, `user`, `reasoning_effort`, `service_tier`, `store`, `metadata`, `logit_bias`, `modalities`, `audio`, `prediction`, `web_search_options`, `tools`, `tool_choice` |
| POST | `/v1beta/models/{model}:generateContent` | `contents`, `systemInstruction`, `generationConfig`, `tools`, `toolConfig`, `safetySettings` |
| POST | `/v1beta/models/{model}:streamGenerateContent` | `contents`, `systemInstruction`, `generationConfig`, `tools`, `toolConfig`, `safetySettings` |
| POST | `/gemini/videos` | `prompt`, `model`, `aspect_ratio`, `resolution`, `image_urls`, `video_urls`, `callback_url`, `async` |
| POST | `/gemini/tasks` | `id`, `ids`, `action` |

Full schema: [gemini.json](openapi/gemini.json).

### Guides

- [development_gemini_chat_completions.md](guides/development_gemini_chat_completions.md)
- [development_gemini_generate_content.md](guides/development_gemini_generate_content.md)
- [development_gemini_tasks.md](guides/development_gemini_tasks.md)
- [development_gemini_videos.md](guides/development_gemini_videos.md)

## GLM

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/glm/chat/completions` | `n`, `model`, `stream`, `messages`, `max_tokens`, `temperature`, `response_format`, `top_p`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `max_completion_tokens`, `logprobs`, `top_logprobs`, `stream_options`, `parallel_tool_calls`, `user`, `reasoning_effort`, `service_tier`, `store`, `metadata`, `logit_bias`, `modalities`, `audio`, `prediction`, `web_search_options`, `tools`, `tool_choice` |

Full schema: [glm.json](openapi/glm.json).

### Guides

- [development_glm_chat_completions.md](guides/development_glm_chat_completions.md)

## OpenAI generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/openai/chat/completions` | `n`, `model`, `stream`, `messages`, `max_tokens`, `temperature`, `response_format`, `tools`, `tool_choice`, `top_p`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `max_completion_tokens`, `logprobs`, `top_logprobs`, `stream_options`, `parallel_tool_calls`, `user`, `reasoning_effort`, `service_tier`, `store`, `metadata`, `logit_bias`, `modalities`, `audio`, `prediction`, `web_search_options` |
| POST | `/openai/embeddings` | `model`, `input`, `encoding_format`, `dimensions` |
| POST | `/openai/images/generations` | `prompt`, `background`, `model`, `moderation`, `n`, `output_compression`, `output_format`, `partial_images`, `size`, `quality`, `response_format`, `style`, `callback_url`, `async` |
| POST | `/openai/responses` | `n`, `model`, `background`, `stream`, `input`, `tools`, `max_tokens`, `temperature`, `response_format`, `tool_choice`, `parallel_tool_calls`, `include`, `reasoning`, `text`, `max_output_tokens`, `store`, `stream_options` |
| POST | `/openai/images/edits` | `image`, `prompt`, `model`, `n`, `background`, `input_fidelity`, `output_format`, `output_compression`, `quality`, `size`, `response_format`, `callback_url`, `async` |
| POST | `/v1/audio/speech` | `model`, `input`, `voice`, `response_format`, `speed` |
| POST | `/v1/audio/transcriptions` | See OpenAPI |
| POST | `/openai/tasks` | `action`, `id`, `trace_id`, `ids`, `trace_ids`, `application_id`, `user_id`, `type`, `offset`, `limit`, `created_at_min`, `created_at_max`, `count_mode` |

Full schema: [openai.json](openapi/openai.json).

### Guides

- [development_openai_audio_speech.md](guides/development_openai_audio_speech.md)
- [development_openai_audio_transcriptions.md](guides/development_openai_audio_transcriptions.md)
- [development_openai_chat_completions.md](guides/development_openai_chat_completions.md)
- [development_openai_embeddings.md](guides/development_openai_embeddings.md)
- [development_openai_images_edits.md](guides/development_openai_images_edits.md)
- [development_openai_images_generations.md](guides/development_openai_images_generations.md)
- [development_openai_responses.md](guides/development_openai_responses.md)
- [development_openai_tasks.md](guides/development_openai_tasks.md)

## Claude AI

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/v1/chat/completions` | `n`, `model`, `stream`, `messages`, `max_tokens`, `temperature`, `response_format`, `top_p`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `max_completion_tokens`, `logprobs`, `top_logprobs`, `stream_options`, `parallel_tool_calls`, `user`, `reasoning_effort`, `service_tier`, `store`, `metadata`, `logit_bias`, `modalities`, `audio`, `prediction`, `web_search_options`, `tools`, `tool_choice` |
| POST | `/v1/messages` | `model`, `messages`, `max_tokens`, `metadata`, `stop_sequences`, `stream`, `system`, `temperature`, `tool_choice`, `tools`, `top_k`, `top_p`, `thinking`, `output_config`, `cache_control` |
| POST | `/v1/messages/count_tokens` | `model`, `messages`, `system`, `thinking`, `tool_choice`, `tools`, `cache_control` |

Full schema: [claude.json](openapi/claude.json).

### Guides

- [development_claude_messages.md](guides/development_claude_messages.md)
- [development_claude_messages_count_tokens.md](guides/development_claude_messages_count_tokens.md)

## Grok

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/grok/chat/completions` | `n`, `model`, `stream`, `messages`, `max_tokens`, `temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `max_completion_tokens`, `logprobs`, `top_logprobs`, `stream_options`, `parallel_tool_calls`, `user`, `reasoning_effort`, `service_tier`, `store`, `metadata`, `logit_bias`, `modalities`, `audio`, `prediction`, `web_search_options`, `tools`, `tool_choice`, `response_format` |
| POST | `/grok/videos` | `prompt`, `model`, `image_url`, `reference_image_urls`, `aspect_ratio`, `resolution`, `duration`, `callback_url`, `async` |
| POST | `/grok/tasks` | `id`, `ids`, `action` |

Full schema: [grok.json](openapi/grok.json).

### Guides

- [development_grok_chat_completions.md](guides/development_grok_chat_completions.md)
- [development_grok_tasks.md](guides/development_grok_tasks.md)
- [development_grok_videos.md](guides/development_grok_videos.md)

## Kimi

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/kimi/chat/completions` | `n`, `model`, `stream`, `messages`, `max_tokens`, `temperature`, `response_format`, `top_p`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `max_completion_tokens`, `logprobs`, `top_logprobs`, `stream_options`, `parallel_tool_calls`, `user`, `reasoning_effort`, `service_tier`, `store`, `metadata`, `logit_bias`, `modalities`, `audio`, `prediction`, `web_search_options`, `tools`, `tool_choice`, `thinking` |

Full schema: [kimi.json](openapi/kimi.json).

### Guides

- [development_kimi_chat_completions.md](guides/development_kimi_chat_completions.md)

## AI Dialogue

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/aichat2/conversations` | `action`, `id`, `model`, `question`, `message`, `stateful`, `references`, `preset`, `max_turns`, `async`, `callback_url`, `allowed_skills`, `allowed_mcp_servers`, `unattended_policy`, `tool_results`, `messages`, `title`, `user_id`, `application_id`, `model_group`, `offset`, `limit` |
| POST | `/aichat/conversations` | `id`, `model`, `preset`, `question`, `stateful`, `references` |

Full schema: [aichat.json](openapi/aichat.json).

### Guides

- [development_aichat2_conversations.md](guides/development_aichat2_conversations.md)
- [development_aichat_conversations.md](guides/development_aichat_conversations.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).

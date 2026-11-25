---
name: suno
description: Use Suno music tools through an Ace Data Cloud account in Claude Code, including setup and retrieval of the same task. Applies when the user requests Suno; it does not change Claude's chat model.
license: Apache-2.0
---

# Suno by Ace Data Cloud

This plugin supplies a service-specific workflow and connects the existing Ace MCP. Credentials come from the plugin's masked **Ace Data Cloud API Token** option, not from prompts or another vendor's environment variables.

## Setup and free check

If tools are absent or unauthorized, direct the user to `/plugin` → Installed → this plugin → Configure options. They need an Ace service API Token with the relevant allowed APIs and balance; see [the illustrated setup](../../README.md). Do not ask them to paste a token into this conversation or alter a global credential.

Call `suno_list_models` with no arguments to read local model reference information. It does not submit a paid generation or prove balance/authorization for generation.

## Use the service

The related tool names are `suno_list_models`, `suno_generate_music`, `suno_generate_custom_music`, `suno_get_task`. Inspect the connected tool's live input schema for currently supported model IDs and parameters; do not invent a model or rely on another service's defaults.

For generation/editing, collect the user's intended input, model and output limits, point out that this is paid through Ace Credits, and use the existing authorization for that exact request. If price or intended limits are unclear, resolve those before submitting. A setup request or a request to explain options does not authorize generation. Send only the prompt and any user-selected references needed for that operation, not the rest of the conversation or unrelated files.

When an operation returns only a task ID, retain that exact ID and poll the related get-task tool at the documented interval until success or failure. Do not submit again to check progress, automatically retry billable writes, or treat a task ID/partial preview as completion. If the result already contains terminal success and final media URLs, report those. Surface rate-limit, moderation, balance and internal errors accurately rather than claiming success.

## Section replacement and billing

For `/suno/audios` `replace_section`, inspect the connected edit schema before calling. Supply the source song's `audio_id` and a nonnegative start/end interval within its duration, with end greater than start. Put local new lyrics for that interval in `lyric` and preferably the same text in `prompt`, not full-song lyrics or a style description. Default `replace_section_result_mode="full_song"` returns two assembled songs without another `concat`; `"candidates"` returns unassembled candidates that need selection and `concat`.

Poll the same task to terminal success, then audition both results for new words, transitions and actual duration. Full-song output does not guarantee equal length; `duration` cannot lock a replacement interval. Returned `lyric` is metadata, not an audio transcript or proof of a successful lyric change. For another edit, use the selected complete result's audio ID and recheck its timing, not the prior task ID or original timestamps. Do not automatically submit another paid replacement to repair an unsatisfactory result.

Check current pricing before these auxiliary operations: successful `/suno/lyrics` costs **0.08 Credits per request**, `/suno/voices` creation **0.15 Credits per request**, and `/suno/audios` `action=stems` **0.56 Credits per request**. Multiple lyric candidates or the vocal/accompaniment pair count as one request, not per output. Failed requests are not charged; applicable discounts follow the actual bill. These rates do not apply to `all_stems`, `extract_stem`, or other actions.

## Custom inputs and processing failures

When the connected tool supports `negative_tags`, use it for generation with `custom: true` or for `replace_section`. The audio endpoint currently enforces no fixed character limit for this field; keep it concise because overly long input may still fail.

A downloadable audio file does not guarantee its `audio_id` remains usable for covers, extension or stem separation. Preserve the public HTTP 500 codes `suno_processing_unavailable` (processing unavailable), `suno_model_unavailable` (selected model unavailable for this operation), and `suno_processing_failed` (processing returned no audio). Also preserve HTTP 500 `api_error` with the message `the account may have been offline` when returned by `/suno/audios`. Retain `task_id` and `trace_id` when returned and contact support with those IDs, never the API key. Query the existing task if submission is uncertain; do not automatically retry a paid operation or silently switch models.

This plugin does not make Suno a native Claude chat model, and installation does not establish Anthropic directory approval. The full existing API reference remains maintained at https://github.com/AceDataCloud/Skills/tree/main/skills/suno-music; read it only when an advanced action needs it.

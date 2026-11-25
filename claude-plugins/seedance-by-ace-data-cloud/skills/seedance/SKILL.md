---
name: seedance
description: Use Seedance video tools through an Ace Data Cloud account in Claude Code, including setup and retrieval of the same task. Applies when the user requests Seedance; it does not change Claude's chat model.
license: Apache-2.0
---

# Seedance by Ace Data Cloud

This plugin supplies a service-specific workflow and connects the existing Ace MCP. Credentials come from the plugin's masked **Ace Data Cloud API Token** option, not from prompts or another vendor's environment variables.

## Setup and free check

If tools are absent or unauthorized, direct the user to `/plugin` → Installed → this plugin → Configure options. They need an Ace service API Token with the relevant allowed APIs and balance; see [the illustrated setup](../../README.md). Do not ask them to paste a token into this conversation or alter a global credential.

Call `seedance_list_models` with no arguments to read local model reference information. It does not submit a paid generation or prove balance/authorization for generation.

## Use the service

The related tool names are `seedance_list_models`, `seedance_list_actions`, `seedance_generate_video`, `seedance_generate_video_from_image`, `seedance_get_task`. Inspect the connected tool's live input schema for currently supported model IDs and parameters; do not invent a model or rely on another service's defaults.

For generation/editing, collect the user's intended input, model and output limits, point out that this is paid through Ace Credits, and use the existing authorization for that exact request. If price or intended limits are unclear, resolve those before submitting. A setup request or a request to explain options does not authorize generation. Send only the prompt and any user-selected references needed for that operation, not the rest of the conversation or unrelated files.

When an operation returns only a task ID, retain that exact ID and poll the related get-task tool at the documented interval until success or failure. Do not submit again to check progress, automatically retry billable writes, or treat a task ID/partial preview as completion. If the result already contains terminal success and final media URLs, report those. Surface rate-limit, moderation, balance and internal errors accurately rather than claiming success.

This plugin does not make Seedance a native Claude chat model, and installation does not establish Anthropic directory approval. The full existing API reference remains maintained at https://github.com/AceDataCloud/Skills/tree/main/skills/seedance-video; read it only when an advanced action needs it.

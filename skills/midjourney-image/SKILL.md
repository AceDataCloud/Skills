---
name: midjourney-image
description: Explain the private Midjourney integration and diagnose existing imagine requests. Midjourney is not currently published in the AceDataCloud public catalog.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Status and legacy-request guidance only; not a public generation workflow. The existing MCP package name is mcp-midjourney.
---

# Midjourney integration status

Midjourney's service and Imagine document are currently marked private. Do not submit legacy generation examples or configure `mcp-midjourney` as a public capability. An explicit API-spec lookup can still return a definition; that is not a publication or access grant. Check the current public catalog and let the user choose a published image service before changing their workflow; do not silently substitute a model or service.

## Diagnose an existing imagine request

1. Inspect the original payload locally without printing its API key. `POST /midjourney/imagine` selects a model version with `version`, not `model`. Remove the `model` key entirely, including when its value is an empty string or `null`.
2. A request containing `model` returns HTTP 400 `bad_request` before generation or asynchronous acceptance, without triggering generation or charging. For version selection the field is `"version": "8.2"`; omitting `version` keeps the default version. Correcting a payload does not authorize submitting it while the capability is private.
3. If an earlier authorized request returned a `task_id`, retain that exact ID. An accepted task is not a finished image. Only report success from the actual final `response.success: true` and usable `response.image_url` or `response.raw_image_url`; do not invent an artifact or treat a task ID as one.
4. A network disconnect, proxy timeout or `5xx` does not prove the original task stopped. Reconcile the existing task or usage record before considering another billable action. For a task with no terminal result for an extended period, contact support with its `trace_id` and task ID, never the API key.

For account-wide HTTP 429 `too_many_requests` recovery, follow the [trial-account concurrency procedure](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md#trial-account-concurrency) and [task-polling guidance](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/async-tasks.md). Changing keys or services does not bypass the trial-account slot.

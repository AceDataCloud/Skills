---
name: midjourney-image
description: Generate and edit Midjourney images or videos through Ace Data Cloud. Use for imagine, edit, blend, variations, upscale, describe, video generation, and querying the exact task ID.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires an Ace Data Cloud API token with Midjourney access. Optionally use the hosted mcp-midjourney server for tool calls.
---

# Midjourney via Ace Data Cloud

Use the [Midjourney API](https://platform.acedata.cloud/documents/midjourney-imagine) or the hosted MCP server. Follow the [shared authentication guide](../_shared/authentication.md) for a private `ACEDATACLOUD_API_TOKEN`; never paste the token into a prompt or saved file.

## First image

Check your current Midjourney pricing and balance in the Ace Data Cloud console before submitting a generation. One imagine request can produce a 2×2 grid. Use `async: true` so the request returns a `task_id` promptly:

```bash
curl -X POST https://api.acedata.cloud/midjourney/imagine \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A small red sailboat on a calm lake at sunrise --ar 1:1","mode":"fast","async":true}'
```

Save the returned `task_id`. Poll **that same ID**; do not repeat the imagine call to check progress:

```bash
curl -X POST https://api.acedata.cloud/midjourney/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"retrieve","id":"TASK_ID_FROM_FIRST_CALL"}'
```

An accepted task is not a finished image. Only present the final artifact after the retrieved task contains `response.success: true` and a usable `response.image_url` or `response.raw_image_url`. Stop and report the error when the task fails. Keep the task ID when a query or network connection is interrupted; querying the same ID does not submit another generation. See the [task API guide](https://platform.acedata.cloud/documents/midjourney-tasks).

## Other actions

- Transform a completed grid with its `image_id` and an action such as `upscale1`, `variation1`, or `reroll` through `POST /midjourney/imagine`. These are new billable actions, not task queries.
- Edit an input image with a prompt through `POST /midjourney/edits`.
- Describe an image through `POST /midjourney/describe`.
- Generate or extend video through `POST /midjourney/videos`. Save its task ID and query the same task.
- Use the `version` parameter or prompt flags only for a version documented by the live API. Midjourney V8.1 supports `fast` and `relax`, not `turbo`, and does not accept a `quality` parameter.

## MCP tools

The hosted Streamable HTTP server is `https://midjourney.mcp.acedata.cloud/mcp`. Configure `Authorization: Bearer <Ace token>` privately in the MCP client. Its named tools include `midjourney_imagine`, `midjourney_edit`, `midjourney_blend`, `midjourney_describe`, `midjourney_generate_video`, `midjourney_get_task`, and `midjourney_get_tasks_batch`. Use `midjourney_get_task` with the exact ID returned by a generation tool until the final success or failure is clear. The [MCP server source](https://github.com/AceDataCloud/MidjourneyMCP) documents the full tool surface.

The server can also run locally from the published `mcp-midjourney` package. Do not add a substitute model or service if an operation fails.

## Troubleshooting

- `401`: check the token value and expiry. `403`: check Midjourney access or content policy. `429`: wait for the advised rate-limit interval. A `5xx` or transport timeout after task submission is not a reason to create another task; query the saved ID first.
- If the task is complete but no URL is present, inspect the full task response and report the missing artifact; do not treat the task ID as a result.
- Review the Ace Data Cloud usage or billing record for the completed action. Task queries do not create another imagine request.

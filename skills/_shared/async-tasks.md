# Async Task Polling

Most generation APIs (images, video, music) are asynchronous — they return a `task_id` immediately, and you poll for the result.

## Pattern

**Step 1:** Submit with `callback_url` to force async mode and get a `task_id` immediately.

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "callback_url": "https://api.acedata.cloud/health"}'
```

Using `"callback_url": "https://api.acedata.cloud/health"` as a placeholder forces async mode even without a real webhook endpoint.

**Step 2:** Poll the task endpoint every 3-5 seconds until the status is terminal.

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from step 1>"}'
```

For batch polling, use:

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve_batch", "ids": ["<task_id_1>", "<task_id_2>"]}'
```

## Task Response Fields

The task endpoint returns the same envelope for every service:

| Field | Description |
|-------|-------------|
| `id` | Task id (same as the `task_id` returned on submit) |
| `request` | The original request payload |
| `response` | The generation result — service-specific, and only populated once the task succeeds |
| `created_at` | Unix timestamp (seconds) when the task was created |
| `started_at` | Unix timestamp (seconds) when processing began |
| `finished_at` | Unix timestamp (seconds) when processing finished |
| `elapsed` | Total processing time in seconds |
| `trace_id` | Trace id for support requests |
| `type` | Task type identifier |
| `user_id`, `actor_user_id`, `api_id`, `application_id`, `credential_id`, `authorization_id` | Ownership metadata — which user, API, application, credential and authorization the task belongs to |

## Important Notes

- Always use `callback_url` to avoid long-running HTTP connections that time out
- Poll every 3-5 seconds for music, every 5 seconds for images/video
- Terminal states vary by service (e.g., `succeeded`, `succeed`, `completed`, `failed`) — check each skill's Gotchas section
- Task polling uses `id` (single) or `ids` (batch). `action` defaults to `retrieve`; set `action: "retrieve_batch"` for `ids`.

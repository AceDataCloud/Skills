# Async Task Polling

Many generation APIs (images, video, music) can run asynchronously — they return a `task_id` immediately, and you poll for the result. Some endpoints wait synchronously by default; pass `async: true` or `callback_url` when documented to force async mode.

## Pattern

**Step 1:** Submit with `async: true` or `callback_url` to force async mode and get a `task_id` immediately.

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "async": true}'
```

When an endpoint does not expose an explicit `async` flag, using `"callback_url": "https://api.acedata.cloud/health"` as a placeholder forces async mode even without a real webhook endpoint.

**Step 2:** Poll the task endpoint until the status is terminal.

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve", "id": "<task_id from step 1>"}'
```

For batch polling, use:

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve_batch", "ids": ["<task_id_1>", "<task_id_2>"]}'
```

## Response Shapes

Task endpoints commonly return one of these shapes:

- Single task record for `retrieve` (usually includes `id`, `type`, `trace_id`, `request`, `response`, `created_at`, `started_at`, `finished_at`, and `elapsed`).
- Batch/list response such as `{ "items": [...], "count": n }` or `{ "items": [...], "total": n }`.
- Service-specific delete/not-found response where documented.

## Important Notes

- Prefer `async: true` or `callback_url` to avoid long-running HTTP connections that time out
- Poll every 3-5 seconds for music, every 5-10 seconds for images/video
- Terminal states vary by service (e.g., `succeeded`, `succeed`, `completed`, `failed`) — check each skill's Gotchas section
- Task polling uses `id`/`trace_id` (single) or `ids`/`trace_ids` (batch) where supported. `action` often defaults to `retrieve`; set `action: "retrieve_batch"` for `ids` or `trace_ids`.
- List/retrieve-batch endpoints may accept pagination and time filters such as `limit`, `offset`, `created_at_min`, and `created_at_max`.

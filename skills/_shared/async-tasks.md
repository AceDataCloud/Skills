# Async Task Polling

Generation APIs (images, video, music) can run asynchronously. Some endpoints wait for a completed result by default; set `async: true` when supported, or provide a `callback_url`, to get a task identifier immediately and poll for the result.

## Pattern

**Step 1:** Submit with `async: true` (preferred when the skill lists it) or `callback_url` to force async mode and get a `task_id` immediately.

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "async": true, "callback_url": "https://api.acedata.cloud/health"}'
```

Creation responses usually include `task_id` and may also include `trace_id`; save both when present. Using `"callback_url": "https://api.acedata.cloud/health"` as a placeholder forces async mode even without a real webhook endpoint.

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

## Important Notes

- Use async mode for long-running jobs to avoid HTTP connections that time out
- Prefer `async: true` on endpoints that document it; `callback_url` also enables async mode and receives the final result
- Poll every 3-5 seconds for music, every 5 seconds for images/video
- Terminal states vary by service (e.g., `succeeded`, `succeed`, `completed`, `failed`) — check each skill's Gotchas section
- Task polling uses `id` (single) or `ids` (batch). Some services also accept `trace_id` or `trace_ids`. `action` defaults to `retrieve` unless the service requires it; set `action: "retrieve_batch"` for `ids`.
- Batch/list responses generally return `items` plus `count` (or a service-specific total field). Individual task records include the original `request`, final `response` when available, `trace_id`, and timing fields such as `created_at`, `started_at`, `finished_at`, and `elapsed`.

# Async Task Polling

Many generation APIs (images, video, music) support asynchronous requests. When
the endpoint supports `async: true`, it returns a `task_id` immediately without
requiring a webhook. Check the individual Skill for its exact request and task
endpoint.

## Pattern

**Step 1:** Submit once with `async: true` when that endpoint supports it.

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "async": true}'
```

Use `callback_url` only when you operate a real public webhook that can receive
the completed result. Do not send callbacks to a health endpoint as a shortcut.
Endpoints without `async: true` may return a final result synchronously or
offer a separate callback workflow; follow their service guide.

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

- Save the returned `task_id`. If the response is already terminal, use that
  result; do not assume every call needs polling.
- Poll every 3-5 seconds for music, every 5 seconds for images/video
- Terminal states vary by service (e.g., `succeeded`, `succeed`, `completed`, `failed`) — check each skill's Gotchas section
- Task polling uses `id` (single) or `ids` (batch). `action` defaults to `retrieve`; set `action: "retrieve_batch"` for `ids`.
- A pending task is not a reason to resubmit the generation request. Re-query
  the same task ID so you do not create another billable job.

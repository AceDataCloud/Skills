# Async media tasks

Submit a generation once with `"async": true`, save its `task_id` immediately,
and poll the corresponding `/tasks` endpoint with `{"id":"<original task ID>"}`.
Use `callback_url` only for a real webhook you control. A health endpoint is not a
webhook. Do not submit a replacement generation to check progress.

## Read the task envelope correctly

The task endpoint can return a persisted envelope with `request`, `response`,
`started_at` and `finished_at`. The model result is inside **`response`**; a
missing top-level `status` does not mean the job is still running.

- `response.success == false` or `response.error`: stop and report failure.
- `response` contains the expected media URL: deliver that real URL.
- `finished_at` is set but no deliverable exists: stop and inspect the original
  result; do not generate again.
- A valid task is still pending: wait and query the same ID.
- Submission timed out before an ID was returned: outcome is unknown. Reconcile
  the original request before any replacement generation.

A synchronous response may already contain the media URL. Deliver it directly.
Never treat an HTTP 200/202 or a task ID alone as completed generation.

## Fixed, bounded media jobs

For small autonomous jobs, the standard-library Python helper
[`scripts/media_job.py`](scripts/media_job.py) keeps a private state file before
submission. Repeating the command with that **same state file and brief** resumes
the original task. A lost submission response never causes an automatic retry.
The state file is a recovery record, not a credential store.

```bash
# ACEDATACLOUD_API_TOKEN must already be in this process's environment.
# Allocate one private state path per customer task, then keep it for recovery.
python3 skills/_shared/scripts/media_job.py video \
  --state /private/jobs/your-original-task-id.json \
  --prompt 'Morning mist above a calm lake, a slow camera move, no text.'
```

Supported fixed recipes:

| Kind | Output | Bound |
|---|---|---|
| `video` | Wan 3 video | 5 seconds, 720P, 16:9, no audio |
| `image` | Seedream 5.0 Lite image | One 2K image |
| `audio` | Fish s2-pro MP3 | Up to 300 characters, preset public voice |

`completed` includes actual URLs. `failed` is a terminal provider result.
`pending` includes the original task ID and state path; resume it later.
Do not create a new state file just because the original job is slow. Do not
print credentials or use shell tracing. Quote user text as an argument; never
execute it as shell code. The helper does not change subscription prices or
credential spending limits. Check current API pricing before first use.

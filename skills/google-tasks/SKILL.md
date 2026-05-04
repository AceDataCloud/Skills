---
name: google-tasks
description: Read and manage Google Tasks task lists and individual tasks via the Tasks v1 REST API. Use when the user mentions Google Tasks, todo / pending / overdue tasks, weekly task recap, grouping todos by list, adding or completing a task, or moving / deleting tasks.
when_to_use: |
  Trigger when the user wants to inspect or manage their Google
  Tasks — list task lists, surface pending items, group by due date,
  pull details for one task, add new todos, mark items complete,
  re-order or delete tasks. The installed connector always grants
  `tasks.readonly`; the user opts in to the broader `tasks` scope
  (full read + write) at install — confirm before destructive writes.
connections: [google/tasks]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

Drive Google Tasks via `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_TASKS_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_TASKS_TOKEN`. At minimum the token
carries `tasks.readonly` plus the identity scopes
(`openid email profile`); if the user opted in to write at install
time it also carries the broader `tasks` scope (read + write).

The Tasks API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim. `401` means the token expired (re-install). `403
insufficientPermissions` on a write means the user only granted
`tasks.readonly` — ask them to re-install with the read+write box
checked.

**Always start with `users/@me/lists`** to discover which task lists
the account has — the user's default plus any extras they created on
calendar.google.com or in the Tasks app.

**Before bulk creates / completions / deletes** echo the exact
titles back to the user and ask them to confirm. Don't trash a
task by guessing an id.

## Recipes

### Verify auth + list all task lists (always run first)

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  | jq '.items[] | {id, title, updated}'
```

The default list is usually titled "我的任务" / "My Tasks" but the
**id** (a long opaque string like `MTAxMjM0NTY3OA`) is what every
subsequent `lists/{id}/tasks` call needs.

### List all unfinished tasks across every list

```sh
curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  | jq -r '.items[] | "\(.id)\t\(.title)"' | while IFS=$'\t' read LIST_ID LIST_TITLE; do
    curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
      --get "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
      --data-urlencode 'showCompleted=false' \
      --data-urlencode 'maxResults=100' \
      | jq --arg list "$LIST_TITLE" '.items[]? | {list: $list, title, due, status, notes}'
  done | jq -s '. | sort_by(.due // "9999")'
```

`showCompleted=false` filters out done items at the API level. The
default `showCompleted=true&showHidden=false` returns done tasks too.

### Pending tasks in one specific list, sorted by due date

```sh
LIST_ID='MTAxMjM0NTY3OA'
curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  --get "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
  --data-urlencode 'showCompleted=false' \
  --data-urlencode 'maxResults=100' \
  | jq '.items // [] | sort_by(.due // "9999") | .[] | {title, due, notes, status, position}'
```

`position` is the user's drag-to-reorder rank inside the list — useful
when the user says "what's at the top of my tasks". Tasks without a
`due` field are open-ended.

### Tasks due today

```sh
TODAY=$(date -u +%Y-%m-%d)
TOMORROW=$(date -u -d "+1 day" +%Y-%m-%d 2>/dev/null \
  || date -u -v+1d +%Y-%m-%d)
TODAY_START="${TODAY}T00:00:00.000Z"
TOMORROW_START="${TOMORROW}T00:00:00.000Z"

curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  | jq -r '.items[] | "\(.id)\t\(.title)"' | while IFS=$'\t' read LIST_ID LIST_TITLE; do
    curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
      --get "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
      --data-urlencode "dueMin=$TODAY_START" \
      --data-urlencode "dueMax=$TOMORROW_START" \
      --data-urlencode 'showCompleted=false' \
      | jq --arg list "$LIST_TITLE" '.items[]? | {list: $list, title, due, notes}'
  done | jq -s
```

`dueMin` / `dueMax` are RFC 3339 timestamps. The Tasks API stores
`due` at midnight UTC, so the local-day window is approximate around
the date boundary — that's fine for "due today" semantics, mention
the caveat only if the user pushes back.

### Overdue tasks (everything still pending with a due date in the past)

```sh
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  | jq -r '.items[] | "\(.id)\t\(.title)"' | while IFS=$'\t' read LIST_ID LIST_TITLE; do
    curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
      --get "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
      --data-urlencode "dueMax=$NOW" \
      --data-urlencode 'showCompleted=false' \
      | jq --arg list "$LIST_TITLE" '.items[]? | {list: $list, title, due, daysOverdue: (((now * 1000) - (.due | sub("Z"; "+00:00") | fromdateiso8601 * 1000)) / 86400000 | floor)}'
  done | jq -s
```

### Recently completed tasks (this week, for a recap)

```sh
ONE_WEEK_AGO=$(date -u -d "-7 days" +%Y-%m-%dT%H:%M:%S.000Z 2>/dev/null \
  || date -u -v-7d +%Y-%m-%dT%H:%M:%S.000Z)

curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  | jq -r '.items[] | "\(.id)\t\(.title)"' | while IFS=$'\t' read LIST_ID LIST_TITLE; do
    curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
      --get "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
      --data-urlencode 'showCompleted=true' \
      --data-urlencode 'showHidden=true' \
      --data-urlencode "completedMin=$ONE_WEEK_AGO" \
      | jq --arg list "$LIST_TITLE" '.items[]? | select(.status=="completed") | {list: $list, title, completed}'
  done | jq -s '. | sort_by(.completed)'
```

`completedMin` / `completedMax` mirror `dueMin`/`Max` and only apply
to tasks already moved to the "completed" state. You **must** pass
`showCompleted=true` AND `showHidden=true` to see them — Google hides
completed tasks from the default list.

### Get one task's details

```sh
LIST_ID='MTAxMjM0NTY3OA'
TASK_ID='dGFza0lkRXhhbXBsZQ'
curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID" \
  | jq '{title, due, status, notes, completed, position, links: .links}'
```

`links` exposes the user's manual hyperlinks (e.g. an attached email
or Drive doc) — render them as a list to the user when present.

### Pagination

`maxResults` caps at 100 per page. Use `nextPageToken`:

```sh
LIST_ID='MTAxMjM0NTY3OA'
PAGE_TOKEN=''
while : ; do
  RESP=$(curl -sS -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
    --get "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
    --data-urlencode 'maxResults=100' \
    --data-urlencode 'showCompleted=false' \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"})
  echo "$RESP" | jq -c '.items[]?'
  PAGE_TOKEN=$(echo "$RESP" | jq -r '.nextPageToken // empty')
  [ -z "$PAGE_TOKEN" ] && break
done
```

## Write recipes

These all need the broader `tasks` scope. If the user only granted
`tasks.readonly` you'll get `403 insufficientPermissions` — surface
that and ask them to re-install with the read+write box checked.

### Add a new task

```sh
LIST_ID='MTAxMjM0NTY3OA'
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"title":"Draft Q2 plan","notes":"Outline + risks + asks.","due":"2026-05-15T00:00:00.000Z"}' \
  "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
  | jq '{id, title, due, status}'
```

Google stores `due` as midnight UTC of the chosen day — the time of
day is ignored in the UI. To insert at the very top of the list,
add `?previous=` (no value) to the URL.

### Bulk add three tasks under user confirmation

```sh
LIST_ID='MTAxMjM0NTY3OA'
DUE='2026-05-12T00:00:00.000Z'
for T in 'Reply to Alice' 'Review PR #404' 'Send meeting recap'; do
  curl -sS -X POST -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
    -H 'Content-Type: application/json' \
    --data "{\"title\":$(jq -nr --arg t "$T" '$t'),\"due\":\"$DUE\"}" \
    "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
    | jq -c '{id, title, due}'
done
```

Always list the titles you're about to create and ask for the user's
go-ahead before running this loop — there is no atomic batch endpoint.

### Mark a task complete

```sh
LIST_ID='MTAxMjM0NTY3OA'
TASK_ID='dGFza0lkRXhhbXBsZQ'
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"status\":\"completed\",\"completed\":\"$NOW\"}" \
  "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID" \
  | jq '{id, title, status, completed}'
```

Reverse with `{"status":"needsAction","completed":null}`.

### Edit a task's title / notes / due date

```sh
LIST_ID='MTAxMjM0NTY3OA'
TASK_ID='dGFza0lkRXhhbXBsZQ'
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"title":"Draft Q2 plan (rev2)","notes":"Cover risks + asks + budget.","due":"2026-05-20T00:00:00.000Z"}' \
  "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID" \
  | jq '{id, title, due, notes}'
```

### Delete a task

```sh
LIST_ID='MTAxMjM0NTY3OA'
TASK_ID='dGFza0lkRXhhbXBsZQ'
curl -sS -X DELETE -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID" \
  -o /dev/null -w 'HTTP %{http_code}\n'
```

`204` = success. There is no soft-delete — once gone the task is
gone. Echo the title back before deleting.

### Re-order: move a task to a position

```sh
LIST_ID='MTAxMjM0NTY3OA'
TASK_ID='dGFza0lkRXhhbXBsZQ'
PREV='dGFza0lkUHJldg'  # task id this one should appear AFTER; omit to move to top
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  --data '' \
  "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID/move?previous=$PREV" \
  | jq '{id, title, parent, position}'
```

Use `?parent=...` instead of `?previous=...` to nest a task under
another task as a sub-task.

### Create a brand-new task list

```sh
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"title":"Q2 follow-ups"}' \
  "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  | jq '{id, title}'
```

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Tasks connector on the Connections page." |
| `403 insufficientPermissions` | write scope missing | "This action needs the Tasks read+write scope, but only `tasks.readonly` was granted. Re-install the connector with the read+write box checked." |
| `404 notFound` | wrong list / task id | re-list with `users/@me/lists` to find the right id. |
| `429 quotaExceeded` | quota / throttling | back off ~5s, then retry once. |

Never log or echo `$GOOGLE_TASKS_TOKEN` — treat it as a secret.

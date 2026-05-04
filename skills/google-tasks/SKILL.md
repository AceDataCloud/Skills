---
name: google-tasks
description: Read Google Tasks task lists and individual tasks via the Tasks v1 REST API. Use when the user mentions Google Tasks, todo / pending / overdue tasks, weekly task recap, or grouping todos by list.
when_to_use: |
  Trigger when the user wants to inspect their Google Tasks — list
  task lists, surface pending items, group by due date, or pull
  details for one task. The installed connector grants read-only
  scope (`tasks.readonly`); creating / updating / deleting tasks is
  out of scope.
connections: [google/tasks]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive Google Tasks via `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_TASKS_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_TASKS_TOKEN`. The token already
carries the `tasks.readonly` scope the user agreed to at install plus
the identity scopes (`openid email profile`).

The Tasks API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim. `401` means the token expired (re-install). `403
insufficientPermissions` means the user is asking for a write this
connector cannot satisfy — say so.

**Always start with `users/@me/lists`** to discover which task lists
the account has — the user's default plus any extras they created on
calendar.google.com or in the Tasks app.

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

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Tasks connector on the Connections page." |
| `403 insufficientPermissions` | scope missing | "This connector is read-only — adding or completing tasks isn't possible." |
| `404 notFound` | wrong list / task id | re-list with `users/@me/lists` to find the right id. |
| `429 quotaExceeded` | quota / throttling | back off ~5s, then retry once. |

Never log or echo `$GOOGLE_TASKS_TOKEN` — treat it as a secret.

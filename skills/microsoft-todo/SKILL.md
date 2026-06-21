---
name: microsoft-todo
description: Read and manage Microsoft To Do task lists and tasks via Microsoft Graph v1.0. Use when the user mentions Microsoft To Do, their Outlook tasks, todo / pending items, due dates or reminders, adding or completing a task, or organising task lists.
when_to_use: |
  Trigger when the user wants to inspect or manage Microsoft To Do —
  list task lists, surface pending / overdue items, add todos, mark
  complete, or update / delete tasks. The connector grants
  `Tasks.ReadWrite` (or `Tasks.Read` if the user chose read-only) —
  confirm before destructive writes.
connections: [microsoft/todo]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive **Microsoft To Do** via Microsoft Graph with `curl + jq`. The user's OAuth
bearer token is in `$MICROSOFT_TODO_TOKEN`; every call needs
`Authorization: Bearer $MICROSOFT_TODO_TOKEN`. Base URL:
`https://graph.microsoft.com/v1.0`.

Failures are `{"error":{"code","message"}}` — show `message` verbatim. `401`
means the token expired (re-install). `403`/`ErrorAccessDenied` on a write means
the user only granted `Tasks.Read` → ask them to re-connect with read+write.

```bash
G="https://graph.microsoft.com/v1.0"; AUTH=(-H "Authorization: Bearer $MICROSOFT_TODO_TOKEN")
# Task lists
curl -sS "${AUTH[@]}" "$G/me/todo/lists" | jq '.value[] | {id, displayName, wellknownListName}'
```

## Tasks

```bash
LIST="LIST_ID"
# Open tasks in a list (filter notStarted/inProgress; $top caps page size)
curl -sS "${AUTH[@]}" \
  "$G/me/todo/lists/$LIST/tasks?\$filter=status ne 'completed'&\$top=50" \
  | jq '.value[] | {id, title, status, due: .dueDateTime.dateTime}'

# Create (confirm first). dueDateTime/reminderDateTime are optional.
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"title":"Follow up with Alex","dueDateTime":{"dateTime":"2026-06-30T17:00:00","timeZone":"UTC"}}' \
  "$G/me/todo/lists/$LIST/tasks" | jq '{id, title, status}'

# Complete: PATCH the task with {"status":"completed"}
curl -sS -X PATCH "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"status":"completed"}' "$G/me/todo/lists/$LIST/tasks/TASK_ID" | jq '{title, status}'
```

## Gotchas

- OData params (`$filter`, `$top`, `$select`) need the `$` escaped in the shell
  (`\$filter`) and URL-encoded spaces — quote the whole URL.
- `wellknownListName: "defaultList"` is the user's default "Tasks" list — a good
  fallback when they don't name a list.
- Pagination via `@odata.nextLink`; follow it for "all tasks".

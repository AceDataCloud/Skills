---
name: microsoft-outlook
description: Read, search, draft, send and manage Outlook / Microsoft 365 email AND calendar events via Microsoft Graph. Use when the user mentions Outlook (mail or calendar), Microsoft 365 inbox, sending mail, replying / forwarding, today's agenda, scheduling a meeting, finding free time, or modifying / cancelling an event.
when_to_use: |
  Trigger when the user wants to read or write Outlook **mail or
  calendar** — list / search / read / triage / archive messages,
  draft and send new mail, reply or forward, manage folders, download
  attachments, see today / this week's events, find conflicts, find a
  free slot, create / update / cancel a meeting, accept / decline an
  invite, check shared mailboxes or shared calendars.
connections: [microsoft/outlook]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive Microsoft Graph for Outlook / Microsoft 365 — both **mail** and
**calendar** — via `curl + jq`. The user's OAuth bearer token is in
`$MICROSOFT_OUTLOOK_TOKEN`; every call needs it as
`Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN`. The token already
carries the scopes the user agreed to at install: any of `Mail.Read`,
`Mail.ReadWrite`, `Mail.Send`, `MailboxSettings.Read`,
`MailboxSettings.ReadWrite`, `Calendars.Read`, `Calendars.ReadWrite`,
plus `*.Shared` variants. Mail and calendar are unified into one
connector (and one OAuth grant) because Microsoft Graph treats them as
sibling features of the same mailbox — there is no value in splitting
them at the skill layer.

The Graph API returns JSON; failures surface as
`{"error": {"code": "...", "message": "..."}}` — show that error
verbatim to the user.

**Always start with `/me`** to confirm the connection works AND learn
which mailbox you're operating against. For calendar work, also fetch
`mailboxSettings.timeZone` so dates render right.

---

# Mail — Recipes

### Verify auth (always run first)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  https://graph.microsoft.com/v1.0/me \
  | jq '{displayName, mail, userPrincipalName}'
```

### List recent messages

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages?\$top=10&\$select=id,subject,from,receivedDateTime,isRead,hasAttachments&\$orderby=receivedDateTime desc" \
  | jq '.value[] | {subject, from: .from.emailAddress.address, received: .receivedDateTime, unread: (.isRead | not)}'
```

Filters: append to URL with `&` (URL-encode the spaces).

| Want | Append |
|---|---|
| Unread only | `&$filter=isRead eq false` |
| With attachments | `&$filter=hasAttachments eq true` |
| From a specific sender | `&$filter=from/emailAddress/address eq 'user@example.com'` |
| Date range | `&$filter=receivedDateTime ge 2026-04-01T00:00:00Z and receivedDateTime lt 2026-05-01T00:00:00Z` |
| Combine | Use `and` / `or` between filter clauses |

### Search messages (full-text on subject + body)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  --data-urlencode '$search="quarterly report"' \
  --data-urlencode '$top=10' \
  --data-urlencode '$select=id,subject,from,receivedDateTime' \
  --get https://graph.microsoft.com/v1.0/me/messages
```

> `$search` cannot be combined with `$filter` or `$orderby` in the same
> query — pick one. `$search` returns relevance-ranked results.

### Read a message body

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}?\$select=subject,body,from,toRecipients,receivedDateTime" \
  | jq '{subject, from: .from.emailAddress.address, received: .receivedDateTime, body: .body.content}'
```

`body.contentType` is usually `"HTML"`. Use `jq -r .body.content` if
you want the raw HTML.

### Send an email

> **⚠️ ALWAYS use draft → confirm → send. NEVER call `/me/sendMail`
> directly — it sends immediately with no undo.**

```sh
# Step 1: create draft
DRAFT=$(curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc \
        --arg subj "Project update" \
        --arg body "<p>Wanted to share the latest numbers.</p>" \
        --arg to "alice@example.com" \
        '{subject:$subj, body:{contentType:"HTML", content:$body}, toRecipients:[{emailAddress:{address:$to}}]}')" \
  https://graph.microsoft.com/v1.0/me/messages)
DRAFT_ID=$(echo "$DRAFT" | jq -r .id)

# Step 2: present the draft to the user — subject, recipients, body preview
echo "$DRAFT" | jq '{subject, to: .toRecipients[0].emailAddress.address, body: .body.content}'

# Step 3: ONLY after user confirms — send (returns 202 No Content)
curl -sS -X POST -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${DRAFT_ID}/send" \
  -w "HTTP %{http_code}\n"
```

CC / BCC: include `ccRecipients` / `bccRecipients` arrays in the same
shape as `toRecipients`.

### Reply / reply-all / forward

> **⚠️ Show the user your draft text + recipients before sending.**

```sh
# Quick reply (sends immediately on /reply — for explicit user-confirmed flow)
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment":"Thanks for the update!"}' \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}/reply"

# Or: createReply → review → /send (preferred for non-trivial replies)
DRAFT=$(curl -sS -X POST -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}/createReply")
DRAFT_ID=$(echo "$DRAFT" | jq -r .id)
# PATCH body if needed, then /send

# Forward
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg to "bob@example.com" \
        '{comment:"FYI", toRecipients:[{emailAddress:{address:$to}}]}')" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}/forward"
```

### Mark read / unread

```sh
curl -sS -X PATCH \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"isRead": true}' \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}"
```

### List folders + read a specific folder

```sh
# Well-known folder names: Inbox, Drafts, SentItems, DeletedItems, Archive, JunkEmail
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/mailFolders('SentItems')/messages?\$top=5&\$select=subject,toRecipients,sentDateTime" \
  | jq '.value[] | {subject, sent: .sentDateTime}'
```

### List + download attachments

```sh
# Metadata
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}/attachments?\$select=id,name,size,contentType" \
  | jq '.value[] | {id, name, size}'

# Download a single attachment
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}/attachments/${ATT_ID}/\$value" \
  -o "$SKILL_DIR/tmp/attachment.bin"
```

### Mailbox settings (timezone, signature, automatic replies)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/mailboxSettings"
```

Set an out-of-office reply:

> **⚠️ Confirm with user before changing — auto-reply will fire on every incoming mail.**

```sh
curl -sS -X PATCH \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"automaticRepliesSetting":{
        "status":"scheduled",
        "scheduledStartDateTime":{"dateTime":"2026-05-10T09:00:00","timeZone":"China Standard Time"},
        "scheduledEndDateTime":{"dateTime":"2026-05-15T18:00:00","timeZone":"China Standard Time"},
        "internalReplyMessage":"<p>I'm out this week, back Monday.</p>"}}' \
  "https://graph.microsoft.com/v1.0/me/mailboxSettings"
```

Requires `MailboxSettings.ReadWrite` scope.

### Delete a message

> **⚠️ Always fetch the subject first and confirm with the user.**

```sh
# 1) show what's about to be deleted
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}?\$select=subject,from,receivedDateTime" \
  | jq '"Delete \"\(.subject)\" from \(.from.emailAddress.address) (\(.receivedDateTime))?"'

# 2) after user confirms (moves to Deleted Items, returns 204)
curl -sS -X DELETE -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/messages/${MSG_ID}" \
  -w "HTTP %{http_code}\n"
```

---

# Calendar — Recipes

### Get user timezone (run once at start of any calendar work)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/me/mailboxSettings" \
  | jq '.timeZone'
# → e.g. "China Standard Time"
```

Pass that timezone in the `Prefer: outlook.timezone` header on every
calendar call so `start.dateTime` / `end.dateTime` come back rendered
in the user's local time:

```sh
TZ_HEADER='Prefer: outlook.timezone="China Standard Time"'
```

### Today's agenda (calendarView)

`calendarView` expands recurring series into individual occurrences
within the window — exactly what you want for an agenda. Plain
`/events` returns only the recurrence master.

```sh
START=$(date -u +'%Y-%m-%dT00:00:00Z')
END=$(date -u -v+1d +'%Y-%m-%dT00:00:00Z')   # macOS; use -d on Linux
curl -sS \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Prefer: outlook.timezone=\"China Standard Time\"" \
  --data-urlencode "startDateTime=$START" \
  --data-urlencode "endDateTime=$END" \
  --data-urlencode '$select=id,subject,start,end,location,attendees,onlineMeeting,isCancelled' \
  --data-urlencode '$orderby=start/dateTime' \
  --get https://graph.microsoft.com/v1.0/me/calendarView \
  | jq '.value[] | {subject, start: .start.dateTime, end: .end.dateTime, location: .location.displayName, attendees: [.attendees[].emailAddress.address]}'
```

### This week's events (Mon–Sun)

```sh
START=$(date -u -v-Mon +'%Y-%m-%dT00:00:00Z' 2>/dev/null || date -u -d 'last monday' +'%Y-%m-%dT00:00:00Z')
END=$(date -u -v+7d -v-Mon +'%Y-%m-%dT00:00:00Z' 2>/dev/null || date -u -d 'next monday' +'%Y-%m-%dT00:00:00Z')
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Prefer: outlook.timezone=\"China Standard Time\"" \
  --data-urlencode "startDateTime=$START" \
  --data-urlencode "endDateTime=$END" \
  --data-urlencode '$select=subject,start,end' \
  --data-urlencode '$orderby=start/dateTime' \
  --get https://graph.microsoft.com/v1.0/me/calendarView
```

### Find free / busy slots (`getSchedule`)

Best way to find a slot that works for multiple people. Returns
30-minute buckets of free / busy / tentative across the requested
window.

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc '{
        schedules: ["me", "alice@example.com", "bob@example.com"],
        startTime: {dateTime: "2026-05-05T09:00:00", timeZone: "China Standard Time"},
        endTime:   {dateTime: "2026-05-05T18:00:00", timeZone: "China Standard Time"},
        availabilityViewInterval: 30
      }')" \
  https://graph.microsoft.com/v1.0/me/calendar/getSchedule \
  | jq '.value[] | {who: .scheduleId, view: .availabilityView}'
# availabilityView is a string of digits: 0=free 1=tentative 2=busy 3=oof 4=workingElsewhere
```

### Read a single event (incl. attendees + body)

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Prefer: outlook.timezone=\"China Standard Time\"" \
  "https://graph.microsoft.com/v1.0/me/events/${EVENT_ID}?\$select=subject,start,end,location,attendees,body,organizer,onlineMeeting" \
  | jq '{subject, start: .start.dateTime, attendees: [.attendees[] | {addr: .emailAddress.address, response: .status.response}], body: .body.content}'
```

### Create an event

> **⚠️ ALWAYS show subject / time / attendees to the user before
> creating — invitations fire automatically the moment the event is
> POSTed.**

```sh
PAYLOAD=$(jq -nc \
  --arg subj "Project sync" \
  --arg body "<p>Quarterly review.</p>" \
  --arg start "2026-05-06T10:00:00" \
  --arg end   "2026-05-06T10:30:00" \
  --arg tz    "China Standard Time" \
  --arg loc   "Meeting room 3F" \
  --arg a1    "alice@example.com" \
  '{
    subject: $subj,
    body:    {contentType:"HTML", content:$body},
    start:   {dateTime:$start, timeZone:$tz},
    end:     {dateTime:$end,   timeZone:$tz},
    location:{displayName:$loc},
    attendees:[{emailAddress:{address:$a1}, type:"required"}],
    isOnlineMeeting: true,
    onlineMeetingProvider: "teamsForBusiness"
  }')
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  https://graph.microsoft.com/v1.0/me/events \
  | jq '{id, subject, start: .start.dateTime, joinUrl: .onlineMeeting.joinUrl}'
```

`isOnlineMeeting: true` + `onlineMeetingProvider: "teamsForBusiness"`
auto-generates a Teams meeting link. Drop both for an in-person event.

### Update / reschedule (PATCH)

> **⚠️ Updating sends an "Updated" notice to all attendees. Confirm first.**

```sh
curl -sS -X PATCH \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc \
        --arg start "2026-05-06T14:00:00" \
        --arg end   "2026-05-06T14:30:00" \
        --arg tz    "China Standard Time" \
        '{start:{dateTime:$start, timeZone:$tz}, end:{dateTime:$end, timeZone:$tz}}')" \
  "https://graph.microsoft.com/v1.0/me/events/${EVENT_ID}"
```

### Cancel a meeting (sends cancellation notice)

> **⚠️ Confirm with the user — every attendee is notified.**

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment":"Need to reschedule, sorry."}' \
  "https://graph.microsoft.com/v1.0/me/events/${EVENT_ID}/cancel" \
  -w "HTTP %{http_code}\n"
```

### Accept / decline / tentative an incoming invite

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comment":"See you there", "sendResponse":true}' \
  "https://graph.microsoft.com/v1.0/me/events/${EVENT_ID}/accept"

# Or /decline, /tentativelyAccept
```

### Read a shared calendar

Requires `Calendars.Read.Shared`.

```sh
curl -sS -H "Authorization: Bearer $MICROSOFT_OUTLOOK_TOKEN" \
  "https://graph.microsoft.com/v1.0/users/${USER_UPN}/calendarView?startDateTime=${START}&endDateTime=${END}&\$select=subject,start,end" \
  -G
```

### Working with timezones

| Field | Meaning |
|---|---|
| `start.dateTime` / `end.dateTime` | The local wall-clock time. |
| `start.timeZone` / `end.timeZone` | IANA-ish name (`"Pacific Standard Time"`, `"China Standard Time"`, `"UTC"`). |
| `Prefer: outlook.timezone="..."` request header | Re-renders all returned `dateTime` values into this zone. |

Always set `Prefer: outlook.timezone` on read calls so the JSON arrives
in the user's expected timezone instead of UTC.

### Recurrence

Use `calendarView` (it expands occurrences for you) — not `?$expand=`.
To create a recurring event, include `recurrence`:

```json
{
  "recurrence": {
    "pattern":  {"type":"weekly", "interval":1, "daysOfWeek":["monday","wednesday"]},
    "range":    {"type":"endDate", "startDate":"2026-05-06", "endDate":"2026-08-06"}
  }
}
```

To modify a single occurrence of a series, PATCH that occurrence's id
(returned by `calendarView`), NOT the series master.

---

# OData quick reference (mail + calendar)

| Param | Mail example | Calendar example |
|---|---|---|
| `$select` | `id,subject,from,receivedDateTime,isRead` | `subject,start,end,location,attendees` |
| `$filter` | `isRead eq false` | `start/dateTime ge '2026-05-01T00:00:00'` |
| `$orderby` | `receivedDateTime desc` | `start/dateTime` |
| `$top` | `10` browse, `25` search | `10` browse |
| `$search` | `"keyword"` (mail only — cannot combine with $filter / $orderby) | n/a |
| `$expand` | `attachments` | `attendees`, `attachments` |

Use `--data-urlencode "$key=$value" --get` with curl to avoid
shell-quoting `$` and spaces.

# Rules

- **Always pass `$select`** — defaults return 30+ fields per item.
- **`$top=10`** for browse, `25` for search. Don't paginate past 50 unless asked.
- **HTML bodies only** for mail. `contentType: "Text"` collapses whitespace.
- **Use `calendarView`** for any agenda / "what's on my calendar"
  question. `/events` returns recurrence masters only.
- **Set `Prefer: outlook.timezone`** on calendar read calls; otherwise
  `dateTime` comes back in UTC.
- **URL-encode message / event / attachment IDs** if using them in a
  path — IDs can contain `+`, `/`, `=`. Use `jq -sRr @uri`.
- **Date math**: `date -u -v+1d` works on macOS, `date -u -d 'tomorrow'` on Linux.

# CRITICAL: User consent for destructive / notifying actions

**Sent emails cannot be unsent. Calendar writes fan out emails to
attendees. Deleted messages may be permanently lost.**
Pattern: **prepare → present → execute**.

| Action | Prepare step | Show user |
|---|---|---|
| Send mail | `POST /me/messages` (draft) | subject, recipients, body preview |
| Reply / forward | createReply / createForward | quote snippet + your reply text |
| Delete mail | fetch `subject` first | "Delete '{subject}' from {sender}?" |
| Out-of-office | show current setting first | new schedule + message preview |
| Create event | build payload | subject, time, attendees, online-meeting on/off |
| Update event | diff with current | what's changing, attendee count being notified |
| Cancel event | fetch event first | subject, time, attendee count |
| Accept / decline invite | fetch event first | event subject + organizer |
| Bulk | list affected | count + sample |

**Never call `/me/sendMail`** — it sends immediately with no undo. Always draft → confirm → `/send`.

# Errors

- `401 InvalidAuthenticationToken` → token expired; user must reinstall the connector.
- `403 ErrorAccessDenied` → write scope missing (e.g. trying `Mail.Send` without it granted, or `Calendars.ReadWrite` for create / cancel); ask user to reinstall and tick the write scope.
- `429 TooManyRequests` → respect `Retry-After` header.
- `404 ErrorItemNotFound` → wrong message / event id (or it was already deleted / cancelled).

# Reference

- Mail API: <https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview>
- Message resource: <https://learn.microsoft.com/en-us/graph/api/resources/message>
- Calendar resource: <https://learn.microsoft.com/en-us/graph/api/resources/calendar>
- Event resource: <https://learn.microsoft.com/en-us/graph/api/resources/event>
- calendarView: <https://learn.microsoft.com/en-us/graph/api/calendar-list-calendarview>
- getSchedule: <https://learn.microsoft.com/en-us/graph/api/calendar-getschedule>
- MailboxSettings: <https://learn.microsoft.com/en-us/graph/api/resources/mailboxsettings>

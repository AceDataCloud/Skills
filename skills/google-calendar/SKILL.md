---
name: google-calendar
description: Read and manage Google Calendar events / agenda / free-busy / invitations via the Calendar v3 REST API. Use when the user mentions Google Calendar events, today's agenda, this week's meetings, finding conflicts, listing invitations, checking free time, or scheduling / rescheduling / cancelling a meeting.
when_to_use: |
  Trigger when the user wants to read or manage events on their
  Google Calendar — list / search / inspect events, build today's
  or this week's agenda, check free / busy windows, pull invite
  details, or have the AI create / update / cancel events on their
  behalf and email invites to attendees. The installed connector
  always grants `calendar.readonly`; the user opts in to the
  broader `calendar` scope (full read + write) at install — confirm
  before destructive writes.
connections: [google/calendar]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
---

Drive Google Calendar via `curl + jq`. The user's OAuth bearer token
is in `$GOOGLE_CALENDAR_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_CALENDAR_TOKEN`. At minimum the token
carries `calendar.readonly` plus the identity scopes
(`openid email profile`); if the user opted in to write at install
time it also carries the broader `calendar` scope (read + write).

The Calendar API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim. `401` means the token expired (re-install). `403
insufficientPermissions` on a write means the user only granted
`calendar.readonly` — ask them to re-install the connector with the
read+write box checked.

**Always start with `users/me/calendarList`** to learn which calendars
the account can see (the user's primary plus any subscribed / shared
ones), AND with `users/me/settings/timezone` so you render times in
the user's local zone instead of UTC.

**Before any destructive write** (creating, moving, or cancelling an
event that has attendees) show the exact event details and ask the
user to confirm. When attendees are involved, also confirm whether
they want Google to email the attendees — that's controlled by the
`sendUpdates` query parameter.

## Recipes

### Verify auth + discover calendars (always run first)

```sh
# Account confirmation + calendars the user can read
curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/calendarList" \
  | jq '.items[] | {id, summary, primary, accessRole, timeZone}'

# User's preferred display zone (use this when formatting times)
curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" \
  | jq -r .value
```

The `id` of each calendar (`primary`, or an email-shaped id like
`team-monday@group.calendar.google.com`) is what subsequent
`calendars/{id}/events` calls take.

### Today's agenda on the primary calendar

```sh
TZ=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" | jq -r .value)
TODAY=$(TZ=$TZ date +%Y-%m-%d)
START="${TODAY}T00:00:00Z"
END="${TODAY}T23:59:59Z"

curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  --get "https://www.googleapis.com/calendar/v3/calendars/primary/events" \
  --data-urlencode "timeMin=$START" \
  --data-urlencode "timeMax=$END" \
  --data-urlencode 'singleEvents=true' \
  --data-urlencode 'orderBy=startTime' \
  --data-urlencode "timeZone=$TZ" \
  | jq '.items[] | {summary, start: (.start.dateTime // .start.date), end: (.end.dateTime // .end.date), location, attendees: [.attendees[]?.email], hangout: .hangoutLink, status, htmlLink}'
```

`singleEvents=true` flattens recurring meetings into individual
instances — almost always what you want for an agenda. Without it,
you'd get the recurrence rule once and have to expand it client-side.

### This week's meetings (Mon–Sun)

```sh
TZ=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" | jq -r .value)
# Bash date math: Monday-of-this-week
MON=$(TZ=$TZ date -d "$(TZ=$TZ date +%Y-%m-%d) -$(($(TZ=$TZ date +%u) - 1)) days" +%Y-%m-%d 2>/dev/null \
  || TZ=$TZ date -v-mondayw +%Y-%m-%d)  # macOS fallback
SUN=$(TZ=$TZ date -d "$MON +6 days" +%Y-%m-%d 2>/dev/null \
  || TZ=$TZ date -v+6d -j -f %Y-%m-%d "$MON" +%Y-%m-%d)

curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  --get "https://www.googleapis.com/calendar/v3/calendars/primary/events" \
  --data-urlencode "timeMin=${MON}T00:00:00Z" \
  --data-urlencode "timeMax=${SUN}T23:59:59Z" \
  --data-urlencode 'singleEvents=true' \
  --data-urlencode 'orderBy=startTime' \
  | jq -r '.items[] | "\(.start.dateTime // .start.date)\t\(.summary)\t\((.attendees // []) | length) attendees"'
```

### Search events by query

```sh
Q='quarterly review'
curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  --get "https://www.googleapis.com/calendar/v3/calendars/primary/events" \
  --data-urlencode "q=$Q" \
  --data-urlencode 'singleEvents=true' \
  --data-urlencode 'maxResults=20' \
  | jq '.items[] | {start: .start.dateTime, summary, htmlLink}'
```

`q` matches against summary, description, location, attendee emails,
and creator/organizer.

### Get one event's full details (incl. attendees, location, link)

```sh
EVENT_ID='abc123def4567890ghijklmnop'
curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events/$EVENT_ID" \
  | jq '{summary, start, end, location, description, attendees, organizer, hangoutLink, conferenceData}'
```

### Free / busy across multiple calendars (next 7 days)

```sh
TZ=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" | jq -r .value)
NOW=$(TZ=$TZ date -u +%Y-%m-%dT%H:%M:%SZ)
NEXT_WEEK=$(TZ=$TZ date -u -d "+7 days" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
  || TZ=$TZ date -u -v+7d +%Y-%m-%dT%H:%M:%SZ)

cat > /tmp/freebusy.json <<JSON
{
  "timeMin": "$NOW",
  "timeMax": "$NEXT_WEEK",
  "timeZone": "$TZ",
  "items": [
    {"id": "primary"},
    {"id": "team-monday@group.calendar.google.com"}
  ]
}
JSON

curl -sS -X POST -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  -H 'Content-Type: application/json' \
  --data @/tmp/freebusy.json \
  "https://www.googleapis.com/calendar/v3/freeBusy" \
  | jq '.calendars'
```

Each calendar's response is `{"busy": [{"start": "...", "end": "..."}]}`
— gaps between are free.

### List events on a non-primary calendar

```sh
CAL_ID='team-monday@group.calendar.google.com'
# URL-encode the @ in the path
CAL_ENCODED=$(printf %s "$CAL_ID" | jq -sRr @uri)
curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  --get "https://www.googleapis.com/calendar/v3/calendars/$CAL_ENCODED/events" \
  --data-urlencode 'singleEvents=true' \
  --data-urlencode 'orderBy=startTime' \
  --data-urlencode 'maxResults=20' \
  | jq '.items[] | {start: .start.dateTime, summary}'
```

### Pagination

```sh
PAGE_TOKEN=''
while : ; do
  RESP=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
    --get "https://www.googleapis.com/calendar/v3/calendars/primary/events" \
    --data-urlencode 'singleEvents=true' \
    --data-urlencode 'orderBy=startTime' \
    --data-urlencode 'maxResults=250' \
    ${PAGE_TOKEN:+--data-urlencode "pageToken=$PAGE_TOKEN"})
  echo "$RESP" | jq -c '.items[]?'
  PAGE_TOKEN=$(echo "$RESP" | jq -r '.nextPageToken // empty')
  [ -z "$PAGE_TOKEN" ] && break
done
```

## Write recipes

These all need the broader `calendar` scope. If the user only granted
`calendar.readonly` you'll get `403 insufficientPermissions` —
surface that and ask them to re-install with the read+write box
checked. **Always echo the event summary, time and attendee list
back to the user before creating or cancelling anything.**

### Create a single event (with optional attendees + Google Meet link)

```sh
TZ=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" | jq -r .value)

cat > /tmp/_cal_event.json <<JSON
{
  "summary": "Sync — Q2 OKR review",
  "location": "Online",
  "description": "Drafted by AceDataCloud.",
  "start": {"dateTime": "2026-05-12T10:00:00", "timeZone": "$TZ"},
  "end":   {"dateTime": "2026-05-12T10:30:00", "timeZone": "$TZ"},
  "attendees": [
    {"email": "alice@example.com"},
    {"email": "bob@example.com"}
  ],
  "reminders": {"useDefault": true},
  "conferenceData": {
    "createRequest": {
      "requestId": "meet-$(date +%s)",
      "conferenceSolutionKey": {"type": "hangoutsMeet"}
    }
  }
}
JSON

# sendUpdates: 'all' = email all attendees; 'externalOnly' = only non-org; 'none' = silent
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  -H 'Content-Type: application/json' \
  --data @/tmp/_cal_event.json \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1&sendUpdates=all" \
  | jq '{id, htmlLink, hangoutLink, summary, start, end, attendees}'
```

Drop the `conferenceData` block if the user didn't ask for a Meet
link — it'll fall back to a plain event.

### Create a recurring event

```sh
TZ=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" | jq -r .value)
cat > /tmp/_cal_recur.json <<JSON
{
  "summary": "Weekly 1:1",
  "start": {"dateTime": "2026-05-12T15:00:00", "timeZone": "$TZ"},
  "end":   {"dateTime": "2026-05-12T15:30:00", "timeZone": "$TZ"},
  "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=TU;COUNT=12"]
}
JSON
curl -sS -X POST -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  -H 'Content-Type: application/json' \
  --data @/tmp/_cal_recur.json \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events" \
  | jq '{id, recurrence, summary}'
```

RRULE follows RFC 5545. Common patterns: `FREQ=DAILY`, `FREQ=WEEKLY;BYDAY=MO,WE,FR`,
`FREQ=MONTHLY;BYMONTHDAY=15`. Add `UNTIL=20261231T235959Z` or `COUNT=12`
for a hard stop.

### Update an existing event (PATCH — partial update)

```sh
EVENT_ID='abc123def4567890ghijklmnop'
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"location":"Conference Room 4","description":"Now in-person."}' \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events/$EVENT_ID?sendUpdates=all" \
  | jq '{id, summary, location, description}'
```

`PATCH` only changes the fields you send; `PUT` replaces the entire
event payload. Prefer `PATCH`.

### Reschedule an event

```sh
EVENT_ID='abc123def4567890ghijklmnop'
TZ=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/users/me/settings/timezone" | jq -r .value)
cat > /tmp/_cal_resched.json <<JSON
{
  "start": {"dateTime": "2026-05-12T14:00:00", "timeZone": "$TZ"},
  "end":   {"dateTime": "2026-05-12T14:30:00", "timeZone": "$TZ"}
}
JSON
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  -H 'Content-Type: application/json' \
  --data @/tmp/_cal_resched.json \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events/$EVENT_ID?sendUpdates=all" \
  | jq '{id, summary, start, end}'
```

### Add or change attendees

Google requires you to send the **complete** attendee list when
patching attendees — fetch the current list, mutate, send back:

```sh
EVENT_ID='abc123def4567890ghijklmnop'
CURRENT=$(curl -sS -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events/$EVENT_ID?fields=attendees" \
  | jq '.attendees // []')
NEW=$(echo "$CURRENT" | jq '. + [{"email":"carol@example.com"}]')
curl -sS -X PATCH -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  -H 'Content-Type: application/json' \
  --data "{\"attendees\": $NEW}" \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events/$EVENT_ID?sendUpdates=all" \
  | jq '{id, attendees}'
```

### Cancel / delete an event

```sh
EVENT_ID='abc123def4567890ghijklmnop'
curl -sS -X DELETE -H "Authorization: Bearer $GOOGLE_CALENDAR_TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events/$EVENT_ID?sendUpdates=all" \
  -o /dev/null -w 'HTTP %{http_code}\n'
```

`204` = success. To cancel one occurrence of a recurring event, fetch
the instance with `events.instances` first, then `DELETE` the
specific instance id (it has a longer `EVENT_ID_YYYYMMDDTHHMMSSZ`
shape).

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Calendar connector on the Connections page." |
| `403 insufficientPermissions` | write scope missing | "This action needs the Calendar read+write scope, but only `calendar.readonly` was granted. Re-install the connector with the read+write box checked." |
| `403 forbidden` | calendar id not visible to this account | check `calendarList` first; if it's a shared calendar, the owner needs to share it. |
| `404 notFound` | wrong event / calendar id | double-check the id and try `calendarList` to confirm the calendar exists. |
| `409 conflict` | recurring event id collision | append a UUID to your `requestId` and retry. |
| `429 quotaExceeded` | quota / throttling | back off ~5s, then retry once. |

Never log or echo `$GOOGLE_CALENDAR_TOKEN` — treat it as a secret.

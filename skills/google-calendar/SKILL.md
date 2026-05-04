---
name: google-calendar
description: Read Google Calendar events / agenda / free-busy / invitations via the Calendar v3 REST API. Use when the user mentions Google Calendar events, today's agenda, this week's meetings, finding conflicts, listing invitations, or checking free time on a specific calendar.
when_to_use: |
  Trigger when the user wants to read events from their Google
  Calendar — list / search / inspect events, build today's or this
  week's agenda, check free / busy windows, or pull invite details
  for a specific meeting. The installed connector grants read-only
  scope (`calendar.readonly`); creating / updating / cancelling
  events is out of scope.
connections: [google/calendar]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Drive Google Calendar via `curl + jq`. The user's OAuth bearer token
is in `$GOOGLE_CALENDAR_TOKEN`; every call needs it as
`Authorization: Bearer $GOOGLE_CALENDAR_TOKEN`. The token already
carries the `calendar.readonly` scope the user agreed to at install
plus the identity scopes (`openid email profile`).

The Calendar API returns standard JSON; failures surface as
`{"error": {"code": 401|403|..., "message": "..."}}` — show that
error verbatim. `401` means the token expired (re-install). `403
insufficientPermissions` means the user is asking for a write this
connector cannot satisfy — say so.

**Always start with `users/me/calendarList`** to learn which calendars
the account can see (the user's primary plus any subscribed / shared
ones), AND with `users/me/settings/timezone` so you render times in
the user's local zone instead of UTC.

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

## Common error codes

| HTTP | meaning | what to tell the user |
|---|---|---|
| `401 UNAUTHENTICATED` | token expired / revoked | "Reconnect the Google Calendar connector on the Connections page." |
| `403 insufficientPermissions` | scope missing | "This connector is read-only — creating or modifying events isn't possible." |
| `403 forbidden` | calendar id not visible to this account | check `calendarList` first; if it's a shared calendar, the owner needs to share it. |
| `404 notFound` | wrong event / calendar id | double-check the id and try `calendarList` to confirm the calendar exists. |
| `429 quotaExceeded` | quota / throttling | back off ~5s, then retry once. |

Never log or echo `$GOOGLE_CALENDAR_TOKEN` — treat it as a secret.

---
name: wecom
description: Read your WeCom (企业微信 / WeCom / Work Weixin) contacts, send app & group messages, create and read WeDoc docs/smart sheets, and manage schedules (日程) and meetings (会议) via the WeCom server-side API as a self-built app. Use when the user mentions 企业微信, WeCom, 通讯录成员/部门, 应用消息, 群机器人/应用群聊, 企业微信文档/智能表格, 企业微信日程 or 会议, or a qyapi.weixin.qq.com call.
when_to_use: |
  Trigger when the user wants to operate their WeCom (企业微信) via a
  self-built app: list departments / members, look up a member's userid,
  send an app message or push to an app group chat, create or read a
  WeDoc document / smart sheet, or create / list / cancel a schedule
  (日程) or meeting (会议).
connections: [wecom]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

We drive the [WeCom server-side API](https://developer.work.weixin.qq.com/document/path/90664)
(`https://qyapi.weixin.qq.com`) with `curl + jq` as a **self-built app (自建应用)**.

> **Setup:** see [WeCom authentication](../_shared/wecom.md) for how to create the self-built app,
> collect **CorpID / Secret / AgentId**, and grant it the contacts / docs / calendar / meeting
> permissions. The skill reads `WECOM_CORP_ID`, `WECOM_CORP_SECRET` and `WECOM_AGENT_ID` from the
> environment; on AceDataCloud they are injected automatically by the 企业微信 connector.

WeCom uses a two-step token flow (identical in shape to the WeChat MP API):

1. Exchange `CorpID + Secret` for an `access_token` (TTL 7200s).
2. Pass that `access_token` as a **query string parameter** on every other call.

**Never log or echo `$WECOM_CORP_SECRET`** — treat it like a password.

Responses are JSON returned with **HTTP 200**; `errcode == 0` means success. On any non-zero
`errcode`, show the original `errmsg` to the user verbatim (see the error table in
[the setup doc](../_shared/wecom.md#response-shape--error-handling)).

## Recipes

### Step 0 — get an access_token (do this first, cache the result)

Every recipe below assumes `$AT` holds a valid token from this step.

```sh
# Fail loudly if credentials are missing/blank. WECOM_AGENT_ID must be a plain
# integer because message/meeting recipes pass it to jq via --argjson (numeric JSON).
: "${WECOM_CORP_ID:?WECOM_CORP_ID not set}" "${WECOM_CORP_SECRET:?WECOM_CORP_SECRET not set}"
case "${WECOM_AGENT_ID:?WECOM_AGENT_ID not set}" in *[!0-9]*|"") echo "WECOM_AGENT_ID must be an integer" >&2; exit 1;; esac

# Cache to $TMPDIR so subsequent calls in the same session reuse it (WeCom
# rate-limits gettoken). Refresh 5 minutes early to avoid edge-of-window failures.
TOKEN_CACHE="${TMPDIR:-/tmp}/wecom-token-${WECOM_CORP_ID}-${WECOM_AGENT_ID}.json"
NOW=$(date +%s)
if [ -f "$TOKEN_CACHE" ] && [ "$(jq -r '.exp_at // 0' "$TOKEN_CACHE")" -gt "$((NOW + 300))" ]; then
  AT=$(jq -r '.access_token' "$TOKEN_CACHE")
else
  RESP=$(curl -sS "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${WECOM_CORP_ID}&corpsecret=${WECOM_CORP_SECRET}")
  AT=$(echo "$RESP" | jq -r 'if .errcode == 0 then .access_token else empty end')
  if [ -z "$AT" ]; then
    echo "Failed to fetch access_token: $RESP" >&2
    exit 1
  fi
  EXPIRES=$(echo "$RESP" | jq -r '.expires_in // 7200')
  echo "$RESP" | jq --argjson now "$NOW" --argjson ttl "$EXPIRES" \
    '{access_token, exp_at: ($now + $ttl)}' > "$TOKEN_CACHE"
  chmod 600 "$TOKEN_CACHE"
fi
```

A tiny helper keeps the recipes short — GET with the token appended, erroring on non-zero `errcode`:

```sh
wc_get()  { curl -sS "https://qyapi.weixin.qq.com/cgi-bin/$1&access_token=${AT}" \
              | jq 'if .errcode == 0 then . else error("WeCom \(.errcode): \(.errmsg)") end'; }
wc_post() { curl -sS -X POST "https://qyapi.weixin.qq.com/cgi-bin/$1?access_token=${AT}" \
              -H 'Content-Type: application/json' -d "$2" \
              | jq 'if .errcode == 0 then . else error("WeCom \(.errcode): \(.errmsg)") end'; }
```

### 通讯录 Contacts (read)

> Reading real names / mobiles requires the app to have **通讯录读取** privilege; otherwise names
> come back masked. Members outside the app's 可见范围 return `errcode 60011` / `81013`.

List the department tree (root department id is `1`):

```sh
wc_get "department/list?id=1" | jq '[.department[] | {id, name, parentid}]'
```

**Preferred enumeration — `user/list_id` (cursor).** This is the robust way to list members:
it works for a self-built app with only its own Secret. `user/simplelist` / `user/list` still
work *within the app's 可见范围*, but WeCom has been tightening those (the 2022‑08‑15 change blocks
newly‑added 通讯录同步 IPs from calling them), so lead with `user/list_id` and fall back to
`simplelist` only if you need names in one shot.

```sh
wc_post "user/list_id" '{"cursor":"","limit":10000}' \
  | jq '{next_cursor, userids: [.dept_user[] | .userid] | unique}'
```

Get one member's full profile — this is how you resolve a **name → userid** for messaging:

```sh
wc_get "user/get?userid=USERID" \
  | jq '{userid, name, department, position, mobile, email, status}'
```

List members of a department in one call (convenience; needs 通讯录 view on that department —
if it returns `60011`, use `user/list_id` + `user/get` above instead):

```sh
wc_get "user/simplelist?department_id=1&fetch_child=1" \
  | jq '[.userlist[] | {userid, name, department}]'
```

Search by name — robust path (enumerate ids, then read each profile and filter):

```sh
for uid in $(wc_post "user/list_id" '{"cursor":"","limit":10000}' | jq -r '.dept_user[].userid' | sort -u); do
  wc_get "user/get?userid=${uid}" | jq -c '{userid, name}'
done | jq -s --arg q "张三" '[.[] | select(.name | contains($q))]'
```

> Shortcut when `simplelist` is available to the app: `wc_get "user/simplelist?department_id=1&fetch_child=1" | jq --arg q "张三" '[.userlist[] | select(.name | contains($q)) | {userid, name}]'`.

### 应用消息 App messages (send) — GATED

`message/send` pushes a notification from your app to members. `agentid` is required and comes from
`$WECOM_AGENT_ID`. `touser` is a `|`-joined list of **userid**s (use `@all` for everyone in scope);
`toparty` / `totag` target departments / tags.

> Sending fans out to real people. **Always show the exact recipients + content and get explicit
> user confirmation before running `message/send` / `appchat/send`**, even if the instruction says
> "just send it".

Send a text message to one or more members:

```sh
wc_post "message/send" "$(jq -nc --arg to "USERID1|USERID2" --argjson agent "${WECOM_AGENT_ID}" \
  --arg content "构建已通过，请查看。" \
  '{touser:$to, msgtype:"text", agentid:$agent, text:{content:$content}, safe:0}')" \
  | jq '{msgid, invaliduser}'
```

Send a Markdown card (richer formatting, members only):

```sh
wc_post "message/send" "$(jq -nc --arg to "@all" --argjson agent "${WECOM_AGENT_ID}" \
  --arg md "**发布通知**\n>版本：v1.2.0\n>状态：<font color=\"info\">成功</font>" \
  '{touser:$to, msgtype:"markdown", agentid:$agent, markdown:{content:$md}}')" \
  | jq '{msgid}'
```

Send a clickable text-card:

```sh
wc_post "message/send" "$(jq -nc --arg to "USERID1" --argjson agent "${WECOM_AGENT_ID}" \
  '{touser:$to, msgtype:"textcard", agentid:$agent,
    textcard:{title:"周报已生成", description:"点击查看本周汇总", url:"https://example.com/report", btntxt:"详情"}}')" \
  | jq '{msgid}'
```

### 应用群聊 App group chat

Create a group the app owns, then push messages into it. `chatid` is a custom id you choose (reuse it later).

```sh
# Create (owner + members are userids). Omit chatid to let WeCom assign one.
wc_post "appchat/create" '{"name":"项目组","owner":"USERID1","userlist":["USERID1","USERID2","USERID3"],"chatid":"proj_alpha"}' \
  | jq '{chatid}'

# Send into it (same GATED confirmation rule as app messages).
wc_post "appchat/send" '{"chatid":"proj_alpha","msgtype":"text","text":{"content":"今晚 8 点线上同步。"}}' \
  | jq '{errcode, errmsg}'

# Inspect a group the app created.
wc_get "appchat/get?chatid=proj_alpha" | jq '.chat_info | {name, owner, userlist}'
```

### 企业微信文档 WeDoc (docs & smart sheets)

Requires the app's **文档 (WeDoc)** permission. `doc_type`: `3` = 文档 (document), `4` = 表格 (spreadsheet),
`10` = 智能表格 (smart sheet).

Create a document and get its edit URL:

```sh
wc_post "wedoc/create_doc" "$(jq -nc --arg name "项目周报 2026-07" \
  '{doc_type:3, doc_name:$name}')" \
  | jq '{docid, url}'
```

Get a shareable link for an existing doc:

```sh
wc_post "wedoc/doc_share" '{"docid":"DOCID"}' | jq '{share_url: .share_url}'
```

Read a document's structured content. WeCom returns a `document` object (keyed by `document_id`,
not `doc_id`) whose body is a tree of typed blocks, **not** Markdown — inspect the real shape before
relying on inner field names:

```sh
wc_post "wedoc/document/get" '{"docid":"DOCID"}' \
  | jq '{document_id: .document.document_id, top_level_keys: (.document | keys)}'
```

> Smart-sheet (智能表格) sub-tables, fields and records use the `wedoc/smartsheet/*` endpoints
> (`get_sheet`, `get_fields`, `get_records`, `add_records`, …) — same `wc_post` pattern, keyed by
> `docid` + `sheet_id`. Reach for them when the user asks to read/write rows of a 智能表格.

### 日程 Schedule (日程)

Requires the app's **日历/日程** permission. Times are **epoch seconds**; convert with GNU `date`:

```sh
START=$(date -d "2026-07-10 15:00" +%s); END=$(date -d "2026-07-10 16:00" +%s)
```

Create a schedule (organizer + attendees are userids):

```sh
wc_post "oa/schedule/add" "$(jq -nc --arg org "USERID1" --argjson s "$START" --argjson e "$END" \
  '{schedule:{organizer:$org, start_time:$s, end_time:$e, summary:"项目评审",
    description:"评审 v1.2 需求", location:"会议室 A",
    attendees:[{userid:"USERID2"},{userid:"USERID3"}],
    reminders:{is_remind:1, remind_before_event_secs:900}}}')" \
  | jq '{schedule_id}'
```

Read schedules by id, and cancel one:

```sh
wc_post "oa/schedule/get" '{"schedule_id_list":["SCHEDULE_ID"]}' \
  | jq '[.schedule_list[] | {schedule_id, summary, start_time, end_time, organizer}]'

wc_post "oa/schedule/del" '{"schedule_id":"SCHEDULE_ID"}' | jq '{errcode, errmsg}'
```

> To *list* a member's upcoming schedules you need their calendar id (`cal_id`) and
> `oa/schedule/get_by_calendar` — create/query calendars via the `oa/calendar/*` endpoints first.

### 会议 Meeting (会议)

Requires the app's **会议** permission. `meeting_start` is epoch seconds, `meeting_duration` is seconds.

Create a scheduled meeting:

```sh
wc_post "meeting/create" "$(jq -nc --arg admin "USERID1" --argjson start "$(date -d '2026-07-11 10:00' +%s)" \
  '{admin_userid:$admin, title:"周例会", meeting_start:$start, meeting_duration:3600,
    description:"同步本周进展", invitees:{userid:["USERID2","USERID3"]}}')" \
  | jq '{meetingid}'
```

List a member's meetings, read details, and cancel (`get_user_meetingid` is a **POST** with a
cursor body, mirroring WeCom's other `get_user_*_id` list endpoints):

```sh
wc_post "meeting/get_user_meetingid" '{"userid":"USERID1","cursor":"","limit":100}' \
  | jq '{meetingid_list, next_cursor}'

wc_post "meeting/get_info" '{"meetingid":"MEETINGID"}' \
  | jq '.meeting_info | {title, meeting_start, meeting_duration, state}'

wc_post "meeting/cancel" '{"meetingid":"MEETINGID"}' | jq '{errcode, errmsg}'
```

## Safety rules

- **Never print `$WECOM_CORP_SECRET`.** It is equivalent to full app access.
- **Confirm before anything outward-facing** — `message/send`, `appchat/send`, `oa/schedule/add`
  and `meeting/create` all notify real colleagues. Show the exact recipients / attendees and the
  content, get explicit approval, *then* run the call. Never infer consent from vague wording.
- Messaging / schedules / meetings act on **userids**, not display names — resolve a name to a
  userid with the contact recipes first, and confirm the person if the name is ambiguous.
- On `errcode 48002` (API forbidden) or `60011` / `301002` (no privilege), the app is missing a
  permission or the target is outside its 可见范围 — tell the user which capability to grant rather
  than retrying blindly.

## Not supported here

- **Reading inbound chat history** (会话内容存档 / msgaudit) — a separate paid capability needing a
  dedicated Secret, an RSA key and the native WeCom Finance SDK; it can't run in this sandbox. The
  skill *sends* messages but can't *read* members' private conversations.
- **A generic todo (待办) CRUD** — WeCom's open API exposes none for self-built apps; use
  **schedules (日程)** for time-bound reminders instead.

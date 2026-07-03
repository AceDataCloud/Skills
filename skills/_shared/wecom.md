# 企业微信 (WeCom) Authentication

The `wecom` skill talks to the [WeCom server-side API](https://developer.work.weixin.qq.com/document/path/90664)
(`https://qyapi.weixin.qq.com`) as a **self-built app (企业内部开发 / 自建应用)**.
Unlike OAuth-bearer connectors, WeCom uses a two-step token flow that is
identical in shape to the WeChat Official Account API:

1. Exchange `CorpID + Secret` for an `access_token` (TTL 7200s).
2. Pass that `access_token` as a **query string parameter** on every other call.

## Create a self-built app & collect three values

1. Sign in to the [WeCom admin console](https://work.weixin.qq.com/wework_admin/) as an
   administrator → **应用管理 (App Management) → 自建 (Self-built) → 创建应用 (Create App)**.
2. After the app is created, open it and read off:
   - **CorpID** — 我的企业 (My Company) → 企业信息 (Company Info), at the bottom (`ww...` / `wc...`).
   - **Secret** — the app's own Secret, shown on the app detail page (click "查看"/"获取"; it is
     sent to the admin's WeCom, not displayed inline).
   - **AgentId** — the app's AgentId, shown on the same app detail page.

## Grant the app the permissions the skill needs

An app only sees what you grant it. On the app detail page configure:

| Capability the skill uses | What to enable on the app |
|---|---|
| Read members / departments (通讯录) | **通讯录 (Contacts)** → set the app's "可见范围" (visible scope) to the members/departments it may act on; to read real names/mobiles, grant **通讯录同步/读取** privilege |
| Send app messages (应用消息) | enabled by default for a self-built app (uses its AgentId) |
| Docs / smart sheets (文档/智能表格) | **文档 (WeDoc)** interface permission |
| Schedules (日程) | **日历/日程 (Calendar)** interface permission |
| Meetings (会议) | **会议 (Meeting)** interface permission |

> ⚠️ **Server IP allowlist.** WeCom rejects calls whose source IP is not in the app's
> **企业可信IP (trusted IP)** list. If you see `errcode 60020` ("not allow to access from your ip"),
> add the caller's egress IP shown in `errmsg` to the app's trusted-IP list and retry.

## Environment variables

The skill reads three variables. On AceDataCloud they are injected automatically for you
(see below); for local runs, export them yourself.

| Variable | Description | Example |
|---|---|---|
| `WECOM_CORP_ID` | Enterprise CorpID | `ww1234567890abcdef` |
| `WECOM_CORP_SECRET` | The self-built app's Secret (sensitive) | `xxxxxxxxxxxxxxxxxxxx` |
| `WECOM_AGENT_ID` | The self-built app's AgentId | `1000002` |

**Local dev — `.env` file**:

```bash
WECOM_CORP_ID=ww1234567890abcdef
WECOM_CORP_SECRET=your-app-secret
WECOM_AGENT_ID=1000002
```

Load it before running the skill:

```bash
set -a; source .env; set +a
```

> ⚠️ **Never commit `.env`** — the Secret is equivalent to full app access. Add it to `.gitignore`.

**Agent usage** (Claude / Studio / etc.): install the
[企业微信 connector](https://auth.acedata.cloud/user/connections) on AceDataCloud once. Your
CorpID / Secret / AgentId are AES-256-GCM encrypted at rest and injected as the env vars above
only inside the sandbox while the skill runs — no manual `.env` setup needed. Revoke anytime from
the connections page.

## Response shape & error handling

Every WeCom response is JSON returned with **HTTP 200**; success is `errcode == 0`:

```json
{"errcode": 0, "errmsg": "ok", "...": "..."}
```

Any non-zero `errcode` is an error — surface `errmsg` to the user verbatim. Common codes:

| errcode | meaning | what to do |
|---|---|---|
| `40014` / `42001` | invalid / expired `access_token` | refresh the token (the recipe caches it — delete the cache and retry) |
| `40056` | invalid AgentId | check `WECOM_AGENT_ID` matches the app whose Secret you used |
| `48002` | API forbidden — app lacks this interface permission | grant the matching capability (docs/calendar/meeting) to the app |
| `60011` | no privilege to access this user/department/resource | the target is outside the app's visible scope — widen 可见范围 |
| `60020` | caller IP not in trusted-IP list | add the egress IP from `errmsg` to 企业可信IP |
| `301002` | no privilege to read contacts detail | grant 通讯录读取 privilege to the app |
| `81013` | user not in app scope | add the user to the app's 可见范围 |

## What is intentionally out of scope

- **Reading inbound chat history (会话内容存档 / msgaudit).** That is a separate paid
  enterprise capability requiring a dedicated Secret, an RSA private key, and the native
  WeCom Finance SDK — it cannot run inside this stdlib sandbox. The skill can *send* app
  messages but cannot *read* members' private conversations.
- **A general todo (待办) CRUD.** WeCom's open API exposes no self-built-app todo endpoints;
  use **schedules (日程)** for time-bound reminders instead.

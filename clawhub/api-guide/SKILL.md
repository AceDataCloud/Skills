---
name: api-guide
description: Set up an AceDataCloud API key, make a first request, and troubleshoot authentication, access, billing, and asynchronous tasks. Use before calling an AceDataCloud service for the first time.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
compatibility: Requires an AceDataCloud account; get a service API key at https://platform.acedata.cloud/console/applications.
---

# AceDataCloud API: from account to first result

This guide is the source for the existing
[@acedatacloud/api-guide](https://clawhub.ai/acedatacloud/skills/api-guide)
ClawHub listing. A ClawHub login installs Skills; an AceDataCloud API key
authorizes calls to `api.acedata.cloud`. They are different credentials.

## 1. Install the right Skill

Install the [ClawHub CLI](https://github.com/openclaw/clawhub/blob/main/docs/cli.md)
if needed, then install the service Skill you intend to use:

```bash
npm install -g clawhub
clawhub install @acedatacloud/suno
clawhub list
```

For a different first workflow, choose its Skill, such as
`clawhub install @acedatacloud/google-search`. Verify that the publisher is
**@acedatacloud**. The general API guide explains setup; the service Skill
contains its exact request fields, models, and task endpoint.

## 2. Find or create your API key

1. Sign in at [AceDataCloud → Applications](https://platform.acedata.cloud/console/applications).
   Create an account if needed.
2. Open **General application**; initialize it if prompted. Its API key can
   access multiple services enabled for your account. A service-specific
   application key is limited to that service. Check access, balance, and the
   current price of the service you want to call.
3. Copy an existing key, or select **Manage Keys → Create**. Name a new key
   (for example, `OpenClaw`), set expiration and restrictions if needed, and
   copy the key value from the application card or key list. If **Allowed APIs**
   is restricted, include every route needed for your first workflow. An
   asynchronous generation needs both the submit and task-query routes.

The [illustrated repository guide](https://github.com/AceDataCloud/Skills#first-run-with-clawhub-and-openclaw)
shows where to copy a key and how to create a separate one. Copy only the key
value. Do not include `Bearer ` in the value, put it in a prompt, or commit it.
A `platform-...` management token is for the separate account-management API,
not for service generation, chat, or search.

## 3. Configure the key

On the OpenClaw Gateway host, add this line to `~/.openclaw/.env`:

```dotenv
ACEDATACLOUD_API_TOKEN=your_api_key_here
```

Keep the file private with `chmod 600 ~/.openclaw/.env`, restart the Gateway,
and start a new session. [OpenClaw loads this global file](https://docs.openclaw.ai/help/faq/env-vars#how-does-openclaw-load-environment-variables)
even when the Gateway runs as a service. For a direct terminal test instead:

```bash
export ACEDATACLOUD_API_TOKEN="your_api_key_here"
```

## 4. Make one first request

This Google Search example returns a result without a separate task query.
Check current service pricing first; API requests may be billable. The key
must allow `/serp/google`:

```bash
curl -X POST https://api.acedata.cloud/serp/google \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"AceDataCloud","type":"search"}'
```

For image, video, or music generation, follow that service Skill's Quick Start.
If a submission returns a `task_id`, save it and query the matching `/tasks`
endpoint until the task is terminal. Use `async: true` where the service
supports it; set `callback_url` only for a real public webhook that you own.
Do not resubmit a pending generation merely to check it: a second submission
can incur a second charge. See the
[task-polling guide](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/async-tasks.md).

## 5. Troubleshoot the first run

| Symptom | Check |
|---|---|
| 401 | Key copied completely, not expired, and available to the running Gateway. `Bearer ` belongs in the HTTP header, not the key value. |
| 403 | Service entitlement, key restrictions, and **Allowed APIs**. A content-moderation rejection may also be 403; read the response. |
| 400 | Exact endpoint, model, and JSON shape from the service Skill. |
| 429 | Reduce request rate or concurrency. Do not automatically retry a billable submit. |
| Pending, timeout, or 5xx | Query the original task or request history before submitting again. |

The [AceDataCloud account console](https://platform.acedata.cloud) shows
balance and usage. Share a task or trace ID with [support](mailto:dev@acedata.cloud),
never your API key. For service-specific examples, see
[@acedatacloud/suno](https://clawhub.ai/acedatacloud/skills/suno),
[@acedatacloud/nano-banana](https://clawhub.ai/acedatacloud/skills/nano-banana),
and [@acedatacloud/ai-chat](https://clawhub.ai/acedatacloud/skills/ai-chat).

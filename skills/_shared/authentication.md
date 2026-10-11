# Authentication

AceDataCloud generation, chat, search, and other service APIs use an API key in
the `Authorization: Bearer <key>` header. A ClawHub login is only for installing
Skills; it is not an AceDataCloud API key.

## Get Your Token

1. Register an account if needed, then sign in at [AceDataCloud → Applications](https://platform.acedata.cloud/console/applications?utm_source=agent_skill&utm_medium=referral&utm_campaign=evergreen&utm_content=skills_setup_api_key).
2. Open **General application**; if it is missing, choose **Initialize General Application**. Its API key can access multiple services your
   account is entitled to use. You can also use a service-specific application
   and key for that service. Check access, balance, and current pricing first.
3. Copy an existing key, or select **Manage Keys → Create** to make a separate
   key for your agent. Name it, choose expiration and restrictions if needed,
   then copy the key value. If **Allowed APIs** is restricted, include every
   endpoint the Skill calls, including task lookup for asynchronous generation.

The [repository README](../../README.md#first-run-with-clawhub-and-openclaw)
shows the two key-management screens and a complete Suno first run.

## Setup

For OpenClaw, put this line in `~/.openclaw/.env` on the Gateway host:

```dotenv
ACEDATACLOUD_API_TOKEN=your_api_key_here
```

OpenClaw [loads that file](https://docs.openclaw.ai/help/faq/env-vars#how-does-openclaw-load-environment-variables)
even when the Gateway runs as a service. Restart the Gateway and start a fresh
session after editing it. Keep the file private (`chmod 600 ~/.openclaw/.env`).

For direct commands outside OpenClaw, export the key in that shell:

```bash
export ACEDATACLOUD_API_TOKEN="your_api_key_here"
```

If your agent uses a project `.env` file, follow that agent's documented loading
behavior. A plain `ACEDATACLOUD_API_TOKEN=...` line followed by `source .env`
sets a shell variable but does not export it to child processes. Do not assume
an agent will automatically source the file. Add `.env` to `.gitignore` and
never commit or paste keys into chat.

## Usage

```bash
curl -X POST https://api.acedata.cloud/<endpoint> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

## Token Types

| Type | Scope | Use Case |
|------|-------|----------|
| **Service API key** | One application/service | Use for one Skill when you want narrow access |
| **General application API key** | Services enabled for the account, subject to key restrictions | Use for multiple Skills |
| [**Platform-management token**](https://platform.acedata.cloud/console/platform-tokens?utm_source=agent_skill&utm_medium=referral&utm_campaign=evergreen&utm_content=skills_setup_account_token) (`platform-...`) | Account-management API | Use with the `acedatacloud` management Skill, not generation/search |

## Gotchas

- A 401 usually means a missing, invalid, or expired key. Check that the Gateway
  actually received `ACEDATACLOUD_API_TOKEN`.
- A 403 can mean missing service access, an API allowlist restriction, or content
  moderation. Read the response before changing the key.
- Do not include `Bearer ` inside `ACEDATACLOUD_API_TOKEN`; the request header
  adds it. Do not place a `platform-...` token there.
- Query the same task ID when generation is pending; a second submit can incur
  a second charge.

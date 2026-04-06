# Authentication

All AceDataCloud APIs use Bearer token authentication.

## Get Your Token

1. Register at [platform.acedata.cloud](https://platform.acedata.cloud)
2. Subscribe to a service (most include free quota)
3. Go to your service's **Credentials** page and create an API token

## Setup

Create a `.env` file in your project root:

```bash
ACEDATACLOUD_API_TOKEN=your_token_here
```

Then load it before making API calls:

```bash
source .env
```

> **Agent usage:** If you're running skills through Claude Code or another AI agent, the agent will automatically `source .env` from the project root before calling any API.

> **Important:** Add `.env` to your `.gitignore` — never commit tokens to version control.

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
| **Service Token** | Single service | Default. Created per-subscription |
| **Global Token** | All services | Create from the platform's global credentials page |

## Gotchas

- Tokens are **service-scoped** by default — if you get a 401 on a different service, create a global token or a token for that specific service
- Tokens do not expire, but can be revoked from the platform

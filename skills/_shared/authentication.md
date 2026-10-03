# Authentication

For a paired hosted MCP in an OAuth-capable client, add the server URL, sign in, and authorize.
Do not ask the user to copy an API token for an already-authorized MCP tool. DCR registers the
client; user authorization and metered service usage still apply.

Direct HTTP API calls and local scripts use Bearer token authentication. A hosted MCP login
does not inject an API token into your shell. Local-only skills need no API token; third-party
connectors follow their declared connection requirements.

## Get Your Token

1. Register at [platform.acedata.cloud](https://platform.acedata.cloud/api/v1/marketing-attribution/entry/skills/?utm_source=skills&utm_medium=readme&utm_campaign=opensource_activation&utm_content=api_token)
2. Choose the service and check its current pricing and your account balance
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

> Use the environment configured by the user. Never assume a client automatically loads `.env`, and never print a token.

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

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

Service and global API tokens are distinct from `platform-*` management tokens and OAuth access tokens. OAuth access tokens are scope-bound JWTs whose lifetime is given by `expires_in` (currently 15 days); request `offline_access` when a refresh token is needed.

## Gotchas

- Tokens are **service-scoped** by default — if you get a 401 on a different service, create a global token or a token for that specific service
- Service and global API tokens are long-lived until their configured expiration or manual revocation; do not assume OAuth access tokens are non-expiring
- Do not interchange service API tokens, `platform-*` management tokens, and OAuth access tokens
- OAuth refresh-token lifetime is deployment-dependent; handle refresh failure by reauthorizing. HTTP 200 from `/oauth2/revoke` does not currently guarantee immediate JWT invalidation

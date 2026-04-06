# Authentication

All AceDataCloud APIs use Bearer token authentication.

## Setup

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

Get your token at [platform.acedata.cloud](https://platform.acedata.cloud):

1. Register an account
2. Browse and subscribe to a service (most include free quota)
3. Create an API credential (token)

## Usage

```bash
curl -X POST https://api.acedata.cloud/<endpoint> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

### Token Types

| Type | Scope |
|------|-------|
| **Service Token** | Access to one subscribed service only |
| **Global Token** | Access to all subscribed services |

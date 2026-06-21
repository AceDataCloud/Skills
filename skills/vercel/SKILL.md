---
name: vercel
description: Inspect Vercel projects, deployments, build logs and domains via the Vercel REST API. Use when the user mentions Vercel, a deployment that failed / is building, build or runtime logs, a preview URL, project domains, or wants to check / redeploy a Vercel project.
when_to_use: |
  Trigger when the user wants to list Vercel projects, list recent
  deployments, read a deployment's build logs to diagnose a failure,
  check domains, or trigger a redeploy. The connector stores a Vercel
  access token with the granted scope; treat env-var values as secret
  (never echo them) and confirm before any redeploy / mutation.
connections: [vercel]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Vercel REST API** with `curl + jq`. The user's token is in
`$VERCEL_ACCESS_TOKEN`; every call needs `Authorization: Bearer
$VERCEL_ACCESS_TOKEN`. Base URL: `https://api.vercel.com`. If the resource is
team-scoped, append `?teamId=$VERCEL_TEAM_ID` (set only when the user connected a
team token).

Errors come back as `{"error":{"code","message"}}` — show `message` verbatim.
`403 forbidden` usually means the token can't see that team/project →
re-connect with the right scope.

Helper for the optional team param:

```bash
TEAM=""; [ -n "$VERCEL_TEAM_ID" ] && TEAM="?teamId=$VERCEL_TEAM_ID"
AUTH=(-H "Authorization: Bearer $VERCEL_ACCESS_TOKEN")
```

## Projects & deployments

```bash
# Projects
curl -sS "${AUTH[@]}" "https://api.vercel.com/v9/projects$TEAM" \
  | jq '.projects[] | {name, framework, latestProduction: .latestDeployments[0].url}'

# Recent deployments (optionally filter by ?projectId=… or &state=ERROR)
curl -sS "${AUTH[@]}" "https://api.vercel.com/v6/deployments${TEAM:-?}&limit=20" \
  | jq '.deployments[] | {uid, name, url, state, readyState, created}'
```

## Diagnose a failed build

```bash
# Deployment detail
curl -sS "${AUTH[@]}" "https://api.vercel.com/v13/deployments/DEPLOYMENT_ID${TEAM:+&teamId=$VERCEL_TEAM_ID}" \
  | jq '{name, url, state: .readyState, error: .errorMessage}'

# Build / runtime events (the actual logs)
curl -sS "${AUTH[@]}" "https://api.vercel.com/v3/deployments/DEPLOYMENT_ID/events${TEAM:+?teamId=$VERCEL_TEAM_ID}" \
  | jq -r '.[] | select(.type=="stdout" or .type=="stderr") | .payload.text'
```

## Domains & redeploy

```bash
# Project domains
curl -sS "${AUTH[@]}" "https://api.vercel.com/v9/projects/PROJECT_ID/domains${TEAM:+?teamId=$VERCEL_TEAM_ID}" \
  | jq '.domains[] | {name, verified}'
```

To **redeploy**, POST to `https://api.vercel.com/v13/deployments` with a
`deploymentId` (or git source) body — **confirm with the user first**, it ships
to production.

## Gotchas

- **Never print env-var values.** Listing project env vars returns metadata;
  the `/v1/.../env/{id}` decrypt route returns secrets — don't call it unless the
  user explicitly asks, and even then summarize, don't echo.
- Deployment `state`/`readyState`: `QUEUED → BUILDING → READY | ERROR | CANCELED`.
- `created`/`ready` are epoch ms — divide by 1000 for human time.

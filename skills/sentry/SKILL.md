---
name: sentry
description: Monitor errors, issues, releases and projects in Sentry via the REST API v0. Use when the user mentions Sentry, error tracking, an unresolved issue, a stack trace / crash, error rate, a release, or wants to triage / resolve / assign issues across their Sentry projects.
when_to_use: |
  Trigger when the user wants to list or search Sentry issues, read a
  crash's latest event + stack trace, list projects or releases, or
  resolve / assign an issue. The connector stores a Sentry auth token
  with the granted org scope — confirm before any write (resolve /
  assign / delete), and prefer read-only triage first.
connections: [sentry]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Sentry REST API v0** with `curl + jq`. The user's auth token is in
`$SENTRY_AUTH_TOKEN` and their org slug in `$SENTRY_ORG_SLUG`; every call needs
`Authorization: Bearer $SENTRY_AUTH_TOKEN`. Base URL: `https://sentry.io/api/0`
(SaaS). For a self-hosted Sentry the user supplies `$SENTRY_BASE_URL` — use it
instead when set.

Errors come back as JSON with a `detail` field — show it verbatim. `401` means
the token is invalid → the user must re-connect Sentry. `403` means the token
lacks the scope for that action (e.g. write) → ask them to re-connect with a
broader token.

Always confirm the org + list projects first:

```bash
BASE="${SENTRY_BASE_URL:-https://sentry.io/api/0}"
curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "$BASE/organizations/$SENTRY_ORG_SLUG/projects/" \
  | jq '.[] | {slug, name, platform}'
```

## Search & read issues

```bash
# Unresolved issues for a project, most frequent first.
curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "$BASE/projects/$SENTRY_ORG_SLUG/PROJECT_SLUG/issues/?query=is:unresolved&sort=freq" \
  | jq '.[] | {id, shortId, title, count, userCount, lastSeen}'

# A single issue + its latest event (stack trace, tags, breadcrumbs).
curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "$BASE/issues/ISSUE_ID/" | jq '{shortId, title, status, count, firstSeen, lastSeen}'
curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "$BASE/issues/ISSUE_ID/events/latest/" \
  | jq '{message, culprit, entries: [.entries[] | .type]}'
```

`query=` uses Sentry's search syntax: `is:unresolved`, `is:assigned`,
`environment:production`, `release:1.2.3`, free-text, etc.

## Releases

```bash
curl -sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "$BASE/organizations/$SENTRY_ORG_SLUG/releases/?per_page=20" \
  | jq '.[] | {version, dateCreated, newGroups, projects: [.projects[].slug]}'
```

## Triage (writes — confirm first)

```bash
# Resolve (or set status: unresolved | ignored). Assign with assignedTo (username/email).
curl -sS -X PUT -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" -d '{"status":"resolved"}' \
  "$BASE/issues/ISSUE_ID/" | jq '{shortId, status}'
```

## Gotchas

- **Pagination** is `Link` header cursor-based (`per_page` max 100). For "all
  issues" follow the `rel="next"; results="true"` cursor.
- **Org/project slugs**, not numeric ids, in the issue-search URL; the issue
  detail/triage routes take the numeric/short issue id.
- Don't dump tokens or PII from event payloads back to the user unprompted.

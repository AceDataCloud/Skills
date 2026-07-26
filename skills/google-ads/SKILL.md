---
name: google-ads
description: Query Google Ads campaigns, ad groups, keywords and spend via the Google Ads API (GAQL searchStream). Use when the user mentions Google Ads, ad campaigns, ad spend / cost, impressions / clicks / conversions on ads, or campaign performance.
when_to_use: |
  Trigger when the user wants Google Ads reporting — list accessible
  customers, campaign / ad-group / keyword performance, spend and
  conversions. Read via GAQL. Needs the OAuth token PLUS a platform
  developer token; if the developer token is absent the connector
  isn't fully provisioned yet — tell the user.
connections: [google/ads]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Query the **Google Ads API** via `curl + jq`. Two credentials plus one context
header:

- `$GOOGLE_ADS_TOKEN` — the user's OAuth bearer (`adwords` scope) →
  `Authorization: Bearer $GOOGLE_ADS_TOKEN`
- `$GOOGLE_ADS_DEVELOPER_TOKEN` — the platform's developer token (injected
  server-side) → header `developer-token: $GOOGLE_ADS_DEVELOPER_TOKEN`
- `login-customer-id` — **only for manager (MCC) scoped calls**: the manager id
  the request runs under, or `$GOOGLE_ADS_LOGIN_CUSTOMER_ID` if set (digits
  only, no dashes). Not needed by `customers:listAccessibleCustomers`.

> **API version:** the base is `https://googleads.googleapis.com/<vNN>`. Google
> ships a new `vNN` every ~4 months and retires old ones, so a hardcoded version
> eventually stops working. The example uses `v25` (supported as of 2026-07). If
> **every** call 404s, the version is unavailable — either retired or not yet
> released. Probe `customers:listAccessibleCustomers`: a supported version
> answers 401/200, an unavailable one 404. Step **down** one version at a time
> from the example, and check Google's supported-versions table before assuming
> a newer `vNN` exists.

If `$GOOGLE_ADS_DEVELOPER_TOKEN` is empty, the connector isn't fully provisioned —
say so rather than calling the API (it would 401/DEVELOPER_TOKEN_NOT_APPROVED).

```bash
VER="v25"; BASE="https://googleads.googleapis.com/$VER"
AUTH="Authorization: Bearer $GOOGLE_ADS_TOKEN"; DEV="developer-token: $GOOGLE_ADS_DEVELOPER_TOKEN"
# Customers the OAuth user can access (ids are returned as customers/<id>)
curl -sS -H "$AUTH" -H "$DEV" "$BASE/customers:listAccessibleCustomers" | jq '.resourceNames'
```

## Report with GAQL (searchStream)

```bash
CID="1234567890"   # target customer id, digits only
# Manager (MCC) access → send login-customer-id; direct access → drop the header.
# Array, not a plain string: the header value contains a space and would split.
LOGIN=(); [ -n "$GOOGLE_ADS_LOGIN_CUSTOMER_ID" ] && LOGIN=(-H "login-customer-id: $GOOGLE_ADS_LOGIN_CUSTOMER_ID")
curl -sS -H "$AUTH" -H "$DEV" "${LOGIN[@]}" \
  -H "Content-Type: application/json" -d '{
  "query":"SELECT campaign.name, metrics.cost_micros, metrics.clicks, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC"
}' "$BASE/customers/$CID/googleAds:searchStream" \
  | jq '.[].results[]? | {campaign: .campaign.name, cost_usd: (.metrics.costMicros|tonumber/1e6), clicks: .metrics.clicks, conv: .metrics.conversions}'
```

GAQL resources: `campaign`, `ad_group`, `ad_group_criterion` (keywords),
`customer`. Cost is `metrics.cost_micros` (÷ 1,000,000 = account currency).

## Gotchas

- **A 404 on *every* endpoint points at `VER`, not at credentials** — the
  version is retired or unreleased. A 404 on a *single* call is about that call:
  a missing resource (bad customer id) or a wrong path. Sanity-check the version
  with `customers:listAccessibleCustomers` before debugging auth.
- **Two credentials plus a context header.** `developer-token` is required on
  every call; `login-customer-id` is only needed when acting under a manager
  (MCC) account — `customers:listAccessibleCustomers` works without it. Omitting
  it on a manager-scoped call is the #1 cause of 401/403 here.
- Customer ids are **digits only** in URLs/headers (strip the dashes from
  `123-456-7890`).
- `searchStream` returns an array of chunks each with `.results[]` — flatten with
  `.[].results[]?`.
- Cost is in **micros** of the account currency; divide by 1e6.

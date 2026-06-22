---
name: google-analytics
description: Query Google Analytics 4 (GA4) reports via the Analytics Data API v1 and list properties via the Admin API. Use when the user mentions Google Analytics, GA4, website traffic / sessions / users, top pages or sources, conversions, or a realtime report.
when_to_use: |
  Trigger when the user wants GA4 metrics — sessions, users, top
  pages / channels / countries, conversions, or live realtime users —
  for one of their GA4 properties. Read-only (`analytics.readonly`).
  List properties first to get the numeric property id.
connections: [google/analytics]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Query **Google Analytics 4** via `curl + jq`. The user's OAuth bearer token is in
`$GOOGLE_ANALYTICS_TOKEN` (scope `analytics.readonly`); every call needs
`Authorization: Bearer $GOOGLE_ANALYTICS_TOKEN`. Two APIs: the **Admin API**
(`analyticsadmin.googleapis.com/v1beta`) to discover properties, and the **Data
API** (`analyticsdata.googleapis.com/v1beta`) to run reports.

Failures are `{"error":{"code","message","status"}}` — show verbatim. `401` =
re-install.

```bash
AUTH="Authorization: Bearer $GOOGLE_ANALYTICS_TOKEN"
# List the GA4 properties the user can access (via their account summaries)
curl -sS -H "$AUTH" "https://analyticsadmin.googleapis.com/v1beta/accountSummaries" \
  | jq '.accountSummaries[]?.propertySummaries[]? | {property, displayName}'
```

`property` looks like `properties/123456789` — the number is the `PROPERTY_ID`.

## Run a report

```bash
PID="123456789"
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" -d '{
  "dateRanges":[{"startDate":"28daysAgo","endDate":"today"}],
  "dimensions":[{"name":"pagePath"}],
  "metrics":[{"name":"screenPageViews"},{"name":"activeUsers"}],
  "orderBys":[{"metric":{"metricName":"screenPageViews"},"desc":true}],
  "limit":10
}' "https://analyticsdata.googleapis.com/v1beta/properties/$PID:runReport" \
  | jq '.rows[] | {page: .dimensionValues[0].value, views: .metricValues[0].value, users: .metricValues[1].value}'
```

Swap dimensions/metrics for other reports: `sessionDefaultChannelGroup` +
`sessions` (acquisition), `country` + `activeUsers` (geo), `eventName` +
`eventCount` / `conversions` (events). Dates accept `NdaysAgo`, `today`,
`yesterday`, or `YYYY-MM-DD`.

## Realtime

```bash
curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"dimensions":[{"name":"country"}],"metrics":[{"name":"activeUsers"}]}' \
  "https://analyticsdata.googleapis.com/v1beta/properties/$PID:runRealtimeReport" | jq '.rows'
```

## Gotchas

- This is **GA4 only** (Data API v1). Old Universal Analytics (UA) is shut down —
  don't use the legacy `analytics/v3` endpoints.
- Valid dimension/metric API names matter (`screenPageViews`, not "Pageviews").
  If a name 400s, it's the wrong API id — check the GA4 dimensions & metrics list.
- Reports are capped by `limit` (default 10k rows); page with `offset`.

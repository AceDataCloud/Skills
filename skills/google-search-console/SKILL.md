---
name: google-search-console
description: Query Google Search Console via the Search Console API v1 — search analytics (clicks / impressions / CTR / position), sites, sitemaps and URL inspection. Use when the user mentions Search Console, organic search performance, top queries / pages, indexing status, or sitemaps.
when_to_use: |
  Trigger when the user wants Search Console data — top queries or
  pages by clicks / impressions / CTR / position, performance by date
  or country, the list of verified sites, sitemaps, or URL inspection.
  Read-only (`webmasters.readonly`). List sites first to get the
  property URL.
connections: [google/search-console]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Query **Google Search Console** via `curl + jq`. The user's OAuth bearer token is
in `$GOOGLE_SEARCH_CONSOLE_TOKEN` (scope `webmasters.readonly`); every call needs
`Authorization: Bearer $GOOGLE_SEARCH_CONSOLE_TOKEN`. Base:
`https://searchconsole.googleapis.com`.

Failures are `{"error":{"code","message","status"}}` — show verbatim. `401` =
re-install. `403` = the token's account doesn't own/verify that site.

```bash
AUTH=(-H "Authorization: Bearer $GOOGLE_SEARCH_CONSOLE_TOKEN")
# Verified sites (siteUrl is the property — URL-encode it in later calls)
curl -sS "${AUTH[@]}" "https://searchconsole.googleapis.com/webmasters/v3/sites" \
  | jq '.siteEntry[] | {siteUrl, permissionLevel}'
```

## Search analytics

```bash
# Top queries by clicks for the last 28 days. siteUrl must be URL-encoded
# (https%3A%2F%2Fexample.com%2F  or  sc-domain%3Aexample.com).
SITE="https%3A%2F%2Fexample.com%2F"
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" -d '{
  "startDate":"2026-05-24","endDate":"2026-06-21",
  "dimensions":["query"],"rowLimit":10
}' "https://searchconsole.googleapis.com/webmasters/v3/sites/$SITE/searchAnalytics/query" \
  | jq '.rows[] | {query: .keys[0], clicks, impressions, ctr, position}'
```

Swap `dimensions` for `["page"]`, `["country"]`, `["date"]`, or combine
`["query","page"]`. Add `"dimensionFilterGroups"` to filter by page/country.

## Sitemaps & URL inspection

```bash
# Submitted sitemaps
curl -sS "${AUTH[@]}" "https://searchconsole.googleapis.com/webmasters/v3/sites/$SITE/sitemaps" \
  | jq '.sitemap[] | {path, lastDownloaded, errors, warnings}'

# Is a URL indexed?
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"inspectionUrl":"https://example.com/page","siteUrl":"https://example.com/"}' \
  "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect" \
  | jq '.inspectionResult.indexStatusResult | {verdict, coverageState, lastCrawlTime}'
```

## Gotchas

- **Two property shapes:** URL-prefix (`https://example.com/`) vs Domain
  (`sc-domain:example.com`). Use exactly the `siteUrl` from the sites list,
  URL-encoded.
- Data lags ~2–3 days; the most recent dates may be partial/empty — set `endDate`
  a couple days back for stable numbers.
- `ctr` is 0–1, `position` is average rank (lower = better).

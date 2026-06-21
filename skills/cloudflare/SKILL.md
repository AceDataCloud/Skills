---
name: cloudflare
description: Manage Cloudflare zones, DNS records, cache purge and Workers via the API v4. Use when the user mentions Cloudflare, a DNS record on a Cloudflare-hosted domain, purging / clearing the CDN cache, a zone's settings, WAF / firewall rules, or listing Workers.
when_to_use: |
  Trigger when the user wants to list Cloudflare zones, read or change
  DNS records, purge the cache, inspect Workers, or review firewall
  rules. The connector stores a scoped Cloudflare API token; confirm
  before any write (DNS create/update/delete, cache purge) and prefer
  the smallest-blast-radius action.
connections: [cloudflare]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **Cloudflare API v4** with `curl + jq`. The user's **scoped** token is
in `$CLOUDFLARE_API_TOKEN` (optionally `$CLOUDFLARE_ACCOUNT_ID` /
`$CLOUDFLARE_ZONE_ID`); every call needs `Authorization: Bearer
$CLOUDFLARE_API_TOKEN`. Base URL: `https://api.cloudflare.com/client/v4`.

Every response has `{"success": bool, "errors": [...], "result": ...}`. On
`success:false` show `.errors` verbatim. `403`/`9109` means the token lacks the
permission for that resource → the user must re-mint the token with the right
scope (zone DNS edit, cache purge, etc.).

```bash
AUTH=(-H "Authorization: Bearer $CLOUDFLARE_API_TOKEN")
API="https://api.cloudflare.com/client/v4"
# Zones the token can see
curl -sS "${AUTH[@]}" "$API/zones" | jq '.result[] | {id, name, status, plan: .plan.name}'
```

## DNS records

```bash
ZONE="${CLOUDFLARE_ZONE_ID:?set or pick from the zones list}"
# List (filter with ?type=A&name=foo.example.com)
curl -sS "${AUTH[@]}" "$API/zones/$ZONE/dns_records?per_page=100" \
  | jq '.result[] | {id, type, name, content, proxied, ttl}'

# Create (confirm first)
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"www","content":"example.com","proxied":true}' \
  "$API/zones/$ZONE/dns_records" | jq '.success, .result.id'

# Update PATCH /dns_records/{id} ; delete DELETE /dns_records/{id}
```

## Purge cache (confirm first)

```bash
# Targeted purge by URL (preferred); use {"purge_everything":true} only if asked
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d '{"files":["https://example.com/path"]}' \
  "$API/zones/$ZONE/purge_cache" | jq '.success'
```

## Workers & firewall

```bash
ACCT="${CLOUDFLARE_ACCOUNT_ID:?needed for account-scoped resources}"
curl -sS "${AUTH[@]}" "$API/accounts/$ACCT/workers/scripts" | jq '.result[] | {id, modified_on}'
# Firewall / WAF custom rules live under /zones/$ZONE/firewall/rules and rulesets.
```

## Gotchas

- Insist on a **scoped API token**, never the legacy Global API Key (the connect
  form's help says so) — a Global Key can do anything on the account.
- `proxied:true` = orange-cloud (CDN/WAF on); `false` = DNS-only. Changing it can
  break TLS/origin expectations — confirm intent.
- Account-scoped calls (Workers, some analytics) need `$CLOUDFLARE_ACCOUNT_ID`;
  zone-scoped calls need a zone id (pick from `/zones` if env unset).

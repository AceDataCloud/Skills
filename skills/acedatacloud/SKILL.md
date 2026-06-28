---
name: acedatacloud
description: |
  Manage your AceDataCloud account through the management API
  (platform.acedata.cloud). Use when the user wants to check their balance /
  remaining credits, look up API call (usage) records and spend, list or create
  or delete API keys (credentials), list subscribed services, list/create/pay
  recharge orders, manage platform tokens, view referral/affiliate earnings, or
  (admins) publish an announcement. Also covers the PUBLIC catalog & docs (no
  token needed): service detail & pricing, API list & OpenAPI specs, datasets,
  integrations, full-text documentation search, and the model catalog with
  per-model credit pricing. This is the self-service "console" API — distinct
  from the data-generation APIs (image/video/music/search).
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [acedatacloud]
compatibility: Requires ACEDATACLOUD_PLATFORM_TOKEN (a platform or user token). Auto-injected when the AceDataCloud connector is installed; otherwise set it in .env. Optionally pair with mcp-acedatacloud for tool-use.
---

# AceDataCloud Platform Management

Programmatically manage your AceDataCloud account: balances, usage records, API
keys, services, orders, platform tokens, models, announcements and referral
earnings — plus browse the public catalog & docs (service pricing, API specs,
datasets, integrations, documentation search, model catalog) without a token.

This is the **management / console** API at `https://platform.acedata.cloud/api/v1`
— the same surface the web console uses. It is **different** from the
data-generation API at `api.acedata.cloud` (image / video / music / search generation).

## Setup — use a PLATFORM token, not a service token

The management API is authenticated with a **platform token** (or a logged-in
user token), **not** the per-service API token used for `api.acedata.cloud`.

1. Create one at [platform.acedata.cloud/console/platform-tokens](https://platform.acedata.cloud/console/platform-tokens)
   (or `POST /api/v1/platform-tokens/`). It starts with `platform-` and never expires.
2. Provide it one of two ways:
   - **Connector (recommended in studio / chat):** install the **AceDataCloud**
     connector at [auth.acedata.cloud/user/connections](https://auth.acedata.cloud/user/connections)
     and paste the token once — the runtime injects `ACEDATACLOUD_PLATFORM_TOKEN`
     into the sandbox automatically (this skill declares `connections: [acedatacloud]`).
   - **Local `.env`:**

```bash
ACEDATACLOUD_PLATFORM_TOKEN=platform-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

```bash
curl -H "authorization: Bearer $ACEDATACLOUD_PLATFORM_TOKEN" \
  https://platform.acedata.cloud/api/v1/applications/
```

> A normal token only ever sees **its own** account data. A superuser token sees
> every user's data and is required for admin operations (announcements).

## CLI (preferred)

The skill ships [`scripts/acedatacloud.py`](scripts/acedatacloud.py) — a self-contained
CLI (stdlib only) for the most common operations.

```bash
ADC=$SKILL_DIR/scripts/acedatacloud.py

# Read
python3 $ADC balance                         # remaining credits per subscription
python3 $ADC services --search suno          # list/search subscribed services
python3 $ADC usage --days 7                   # recent API call records
python3 $ADC usage-summary --days 30          # spend aggregated by day + API
python3 $ADC keys                             # list API keys (credentials)
python3 $ADC orders --state Finished          # recharge orders
python3 $ADC tokens                           # platform tokens
python3 $ADC models                           # available chat models
python3 $ADC distributions                    # referral status + commission history

# Catalog & docs (PUBLIC — work without a token)
python3 $ADC get-service --service suno       # one service's detail
python3 $ADC pricing --service suno           # unit, free_amount and cost
python3 $ADC apis --service suno              # API endpoints for a service
python3 $ADC spec --path /suno/audios         # one API's OpenAPI definition + cost
python3 $ADC datasets                         # downloadable datasets
python3 $ADC integrations                     # third-party integrations
python3 $ADC docs-search --query "suno lyrics" --lang en   # full-text doc search
python3 $ADC docs-list                        # browse documentation pages
python3 $ADC doc --id <document-uuid>         # one doc's full content
python3 $ADC model-catalog --modality chat    # rich model catalog + credit pricing
python3 $ADC model --model claude             # look up a model by id/name

# Safe write (require --yes to actually execute)
python3 $ADC create-key  --application <app-id> --name "ci" --yes
python3 $ADC delete-key  --id <credential-id> --yes
python3 $ADC create-order --application <app-id> --package <package-id> --yes
python3 $ADC pay-order   --id <order-id> --pay-way Stripe --yes
python3 $ADC create-token --yes
python3 $ADC delete-token --id <token-id> --yes

# Admin (superuser token only)
python3 $ADC send-announcement --title "..." --content "..." --yes
```

Every command accepts `--json` for machine-readable output and `--token` to
override the env token. Without `--yes`, write commands print a dry-run preview
and exit without calling the API.

## Pagination

List endpoints return `{ "count": <total>, "items": [ ... ] }` and accept
`?limit=` and `?offset=`. (Note: some older docs say `results`; the live field
is **`items`**.)

## Endpoints reference

### Balance / subscriptions — `GET /applications/`

An *Application* is your subscription to one Service; its `remaining_amount` is
your balance (in **Credits**) for that service.

```bash
curl -H "authorization: Bearer $ACEDATACLOUD_PLATFORM_TOKEN" \
  "https://platform.acedata.cloud/api/v1/applications/?limit=1"
```

```json
{
  "count": 3,
  "items": [
    {
      "id": "e9f625f2-cbd5-4254-8264-cfadbd180428",
      "service_id": "f2b646d8-3cfd-46ef-969a-1ea9eebde329",
      "remaining_amount": 100.9,
      "used_amount": 1.1,
      "paid": false,
      "scope": "Global",
      "allow_consume_global": true,
      "expired_at": null,
      "type": "Usage"
    }
  ]
}
```

Filters: `service_id`, `scope` (`Individual`/`Global`), `user_id` (superuser only).

### Usage records — `GET /usage/apis/`

Per-request call records (status code, latency, credits deducted).

Filters: `api_id`, `application_id`, `status_code`, `created_at_from`,
`created_at_to`, `user_id` (superuser only).

```json
{
  "count": 128,
  "items": [
    {
      "id": "c124684b-7188-4c3e-ad53-3fba5150b944",
      "api": { "title": "Suno Audios Generation API" },
      "status_code": 200,
      "original_amount": 0.55,
      "deducted_amount": 0.55,
      "trace_id": "…",
      "elapsed": 12.3,
      "created_at": "2026-06-28T09:15:44Z"
    }
  ]
}
```

- **Spend aggregate** — `GET /usage/apis/aggregate/?created_at_from=&created_at_to=`
  → `{ "items": [{ "date", "api_id", "amount" }], "total": <credits>, "apis": { "<id>": { "title" } } }`
- **Status-code filter values** — `GET /usage/apis/status-codes/` → `{ "items": [200, 400, 502] }`
- **CSV export** — `GET /usage/apis/export/?created_at_from=&created_at_to=` (downloads `usages.csv`)

### Services — `GET /services/`

```json
{ "count": 215, "items": [ { "id": "…", "alias": "suno", "title": "Suno 音乐生成",
  "unit": "Credit", "free_amount": 0.0, "applied_count": 121733,
  "packages": [ { "id": "…", "type": "Usage", "price": 13.0, "amount": 100.0 } ] } ] }
```

### API keys / credentials — `GET /credentials/`

```json
{ "count": 2, "items": [ { "id": "dae4899f-…", "name": "ci", "type": "Token",
  "token": "<secret>", "limited_amount": null, "used_amount": 1.1,
  "host": null, "created_at": "2026-06-28T09:15:44Z" } ] }
```

- **Create** — `POST /credentials/` `{ "application_id": "<app>", "name": "ci", "limited_amount": 100, "expired_at": "2026-12-31T00:00:00Z" }` → returns the credential incl. the new `token`. Save it; it is shown in full only at creation.
- **Delete** — `DELETE /credentials/{id}` → `204 No Content`
- Filters: `application_id`, `host`, `granted` (`true`/`false`), `user_id` (superuser).
- To "rotate" a key, delete it and create a new one.

### Orders (recharge) — `GET /orders/`

```json
{ "count": 12, "items": [ { "id": "17c10c9d-…", "application_id": "…",
  "package_id": "…", "description": "100 Credits", "price": 13.0,
  "state": "Finished", "pay_way": "Stripe", "pay_url": "<url>",
  "created_at": "2026-06-28T09:17:25Z" } ] }
```

- `state` ∈ `Pending` `Paid` `Finished` `Expired` `Failed` `Refunded`
- `pay_way` ∈ `WechatPay` `AliPay` `Stripe` `X402` `PayPal` `Reward`
- **Create** — `POST /orders/` `{ "application_id": "<app>", "package_id": "<package>" }`
- **Pay** — `POST /orders/{id}/pay/` `{ "pay_way": "Stripe" }` → returns the order with a `pay_url` to open
- **Refresh status** — `POST /orders/{id}/refresh/` (re-checks the PSP and updates `state`)
- Filters: `state`, `pay_way`, `created_at_from`, `created_at_to`, `user_id` (superuser).

### Platform tokens — `GET /platform-tokens/`

```json
{ "count": 2, "items": [ { "id": "efdccba4-…", "token": "<secret>",
  "expiration": null, "used_at": null, "created_at": "2026-06-28T06:29:02Z" } ] }
```

- **Create** — `POST /platform-tokens/` → returns the new token (starts with `platform-`)
- **Delete** — `DELETE /platform-tokens/{id}/` → `204 No Content`

### Models — `GET /models/`

OpenAI-style (no pagination): `{ "object": "list", "data": [ { "id": "gpt-4.1",
"label": "GPT-4.1", "owned_by": "openai", "type": "chat", "capabilities": ["vision"] } ] }`

### Catalog & docs (PUBLIC — no token required)

These work without auth (send the token if you have one; not required):

- **Service detail / pricing** — `GET /services/?id=<uuid>` → `items[0]` (full: `cost`, `unit`,
  `free_amount`, `title`). The `services/?alias=` filter is **ignored** server-side, so resolve an
  alias by paging `services/` and matching `alias` client-side. The `services/{id}/` detail route is broken (500).
- **APIs** — `GET /apis/?path=<path>` → exactly one item with its OpenAPI `definition` + `cost`.
  `apis/?service_id=` is **ignored** server-side; filter by `service_id` client-side. `apis/{id}/` is broken (500).
- **Datasets / integrations** — `GET /datasets/`, `GET /integrations/`.
- **Doc search** — `GET /search/?query=<text>&lang=<code>` → `{ results: [ { id, alias, title, type, snippet, url } ] }`.
  The param is **`query`** (not `keyword`).
- **Doc content** — `GET /documents/?id=<uuid>` → `items[0].content`. `documents/{id}/` (id or slug) is broken (404).
- **Model catalog** — `GET /models/catalog/` → `{ rates, modalities, count, items:[{ id, name, provider,
  modality, unit, capabilities, pricing:{ input_credits, output_credits, official_* } }] }`. Filter client-side.

### Announcements — `GET /announcements/`

Public read: `{ "count": 20, "items": [ { "id", "title", "content",
"translation_key", "published", "publish_at", "rank", "tags", "is_read" } ] }`

**Admin only (superuser token):**

- **Publish** — `POST /announcements/admin/` `{ "title": "...", "content": "...", "rank": 5, "tags": ["product"], "published": true }`
  (`content` is Markdown; a zh-cn Translation row is created and other locales are auto-translated by a CronJob)
- **Edit / delete** — `PUT` / `DELETE /announcements/admin/{id}`
- **AI polish** — `POST /announcements/admin/polish/` `{ "title", "content" }`
- **AI translate** — `POST /announcements/admin/translate/` `{ "translation_key" }`

## Write-operation safety

Creating/deleting keys, creating/paying orders, deleting platform tokens, and
publishing announcements are **irreversible or money-related**. Always:

1. Confirm the exact target (`application_id`, `order_id`, `credential_id`) with
   the user before executing.
2. With the CLI, writes are dry-run unless `--yes` is passed.
3. Never print a full `token` value into shared logs — it grants account access.

## Gotchas

- Use the **platform token** (`ACEDATACLOUD_PLATFORM_TOKEN`), not the
  `api.acedata.cloud` service token — the latter returns 401 here.
- `remaining_amount` / `used_amount` / `amount` are in **Credits**, not USD.
  Convert with a service's package: `USD = Credits × (package.price / package.amount)`.
- Newly created credential/platform tokens are returned in full **only once** —
  store them immediately.
- Credential "rotate" is delete + recreate; there is no in-place rotate endpoint.
- Announcement endpoints under `/admin/` require a **superuser** token; a normal
  token gets `403`.

> **MCP:** `pip install mcp-acedatacloud` | Hosted: `https://mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md). The MCP exposes these as tools (`acedatacloud_get_balance`, `acedatacloud_list_usage`, `acedatacloud_get_pricing`, `acedatacloud_search_docs`, `acedatacloud_get_api_spec`, `acedatacloud_create_credential`, …) with the same write-confirmation guard.

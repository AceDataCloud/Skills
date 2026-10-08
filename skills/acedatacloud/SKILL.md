---
name: acedatacloud
description: |
  Manage your AceDataCloud account through the management API
  (platform.acedata.cloud). Use when the user wants to check their balance /
  remaining credits, look up API call (usage) records and spend, list or create
  or delete API keys (credentials), list subscribed services, list/create/pay
  recharge orders, manage platform tokens, view referral/affiliate earnings,
  manage article/video blog drafts, review threads and peer-reviewed publication via MCP / REST, or (admins) publish
  an announcement. Also covers the PUBLIC catalog & docs (no
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
earnings, and manage article/video drafts, review threads and peer-reviewed blog publication through MCP / REST — plus browse
the public catalog & docs (service pricing, API specs, datasets, integrations,
documentation search, model catalog) without a token.

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
     connector at [studio.acedata.cloud/console/connectors](https://studio.acedata.cloud/console/connectors)
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
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script (re-run this at the top of every fresh-shell Bash block).
ADC="$SKILL_DIR/scripts/acedatacloud.py"; [ -f "$ADC" ] || ADC=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/acedatacloud.py' 2>/dev/null | head -1)
[ -f "$ADC" ] || { echo "acedatacloud script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

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
python3 $ADC pricing --service suno           # unit, free_amount and cost (dataset reference quotes when present)
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

### Dataset reference pricing

1. Resolve the requested dataset's public service with `get-service --service <alias-or-uuid>` and read its current metadata. Contact-only datasets are catalog entries, not automatically downloadable purchases; a missing price does not mean free data.
2. Run `pricing --service <alias-or-uuid> --json`. For a Dataset, the CLI includes `pricing_mode` and `reference_quote` when present. The source fields are `metadata.pricing_mode` and `metadata.reference_quote` on the Service, not the Dataset's `price` or an API's `cost`.
3. If `pricing_mode="contact_only"` and the quote has `status="reference"`, present `min_amount`–`max_amount` with the supplied `currency` and quote `unit`. `CNY` amounts are yuan, not Credits or USD; `full_package` means the full package and `tb` means per TB. Equal bounds indicate a single reference amount. Do not apply the Credits-to-USD conversion or invent a quote when none is returned.
4. Treat a reference quote as indicative only: it does not create a purchase Package, guarantee delivery, or grant download or usage rights. Confirm the required version, scope, format, license and final price with support before proceeding; do not call `create-order` or `pay-order` based on a reference quote.

### Announcements — `GET /announcements/`

Public read: `{ "count": 20, "items": [ { "id", "title", "content",
"translation_key", "published", "publish_at", "rank", "tags", "is_read" } ] }`

**Admin only (superuser token):**

- **Publish** — `POST /announcements/admin/` `{ "title": "...", "content": "...", "rank": 5, "tags": ["product"], "published": true }`
  (`content` is Markdown; a zh-cn Translation row is created and other locales are auto-translated by a CronJob)
- **Edit / delete** — `PUT` / `DELETE /announcements/admin/{id}`
- **AI polish** — `POST /announcements/admin/polish/` `{ "title", "content" }`
- **AI translate** — `POST /announcements/admin/translate/` `{ "translation_key" }`

### Blog drafts, review submission and publication (MCP / REST)

Use `mcp-acedatacloud` with a platform token or the Studio OAuth connection. The bundled CLI does not implement blog commands; use the MCP tools and inspect their current input schemas rather than inventing CLI flags. Blog permissions can be delegated to non-admin accounts; check the available tools and scopes before writing.

| Permissions | Operations |
|-------------|------------|
| `blog:read` | List drafts and read full editing-source content |
| `blog:write` | Create, edit and delete unpublished drafts; submit or withdraw a pending review |
| `blog:read` + `blog:publish` | Approve or reject a submitted version, or withdraw approval before publication |
| `blog:write` + `blog:publish` | Publish or schedule an approved draft, unpublish, or delete a published post |

1. Confirm the intended article and source language (`zh-cn` or `en`). Use the current editorial categories: `product-updates`, `tech-sharing`, `product-recommendations`, or `industry-insights` (default `tech-sharing`). Read the current category list if a custom category is needed; do not guess a slug.
2. Save an unpublished draft with `acedatacloud_create_blog_draft`, or edit it with `acedatacloud_update_blog_post`. Read the full source with `acedatacloud_get_blog_draft`, including title, summary, body, category, cover, `content_type` and `video_url`, and retain its current `review_version` and `review_status`. Default `content_type="article"` requires a nonblank body and clears `video_url`. For `content_type="video"`, upload the intended video first and use its actual HTTPS `video_url`; the body may be blank, but title and summary remain required. Never fabricate a media URL. A cover requires HTTPS `cover_url` and nonblank `cover_alt`. If the discovered MCP schema lacks video fields, use `POST /api/v1/blogs/admin/` to create an unpublished draft or `PATCH /api/v1/blogs/admin/{id}/` to edit one after confirmation; do not invent MCP arguments or CLI flags.
3. Submit a `draft` or `rejected` article for review before seeking approval. With `blog:write`, send `POST /api/v1/blogs/admin/{id}/submit/` on the management host with `{"expected_version": CURRENT_REVIEW_VERSION}`; verify `review_status="pending"`. Legacy drafts without a creator must first be saved by an editor. Pending articles cannot be edited: withdraw the review request with `DELETE` to the same `/submit/` route and the current `expected_version`, verify `draft`, then edit and resubmit. Withdrawal of a pending review is distinct from withdrawal of approval.
4. A different authorized account must read the full pending draft (and watch the actual video for a video post) and approve that exact version with `acedatacloud_approve_blog_post`. The creator cannot approve their own draft. For REST approval, `POST /api/v1/blogs/admin/{id}/approval/` requires `expected_version` equal to the `review_version` just read. The reviewer may instead send `POST /api/v1/blogs/admin/{id}/reject/` with that `expected_version` and a nonblank `comment` (at most 2,000 characters), or omit `comment` if an unresolved root review thread already exists on the current version; verify `review_status="rejected"`. Read `review_comment`, revise and resubmit, checking the review threads below before another review. A 409 on submission, withdrawal, approval or rejection means the draft changed: refresh and reread the full draft before retrying. Do not impersonate a reviewer or switch credentials to bypass this separation.
5. Only after `review_status="approved"`, use `acedatacloud_publish_blog_post` from an authorized account: the publisher must not be the reviewer (the creator may publish after peer approval). For scheduling, provide a timezone-aware `publish_at`; omit it to publish now. Verify the returned state and time before reporting the post as publicly live.
6. Changes to reviewed public content (including title, body, category, tags, slug, cover, `content_type` or `video_url`) invalidate approval and advance `review_version`. Unpublish before editing a published post with `acedatacloud_unpublish_blog_post`, then submit and obtain fresh peer approval before republishing. Use `acedatacloud_withdraw_blog_approval` to revoke approval while unpublished; an approved article returns to `draft`.

#### Review threads (authenticated REST)

Review comments are private editorial feedback, not public blog comments. Use the management host and platform Bearer token. Listing requires `blog:read`; adding, replying and resolving require `blog:read` plus either `blog:write` or `blog:publish`.

1. Read the saved draft and `GET /api/v1/blogs/admin/{id}/comments/`. The response is a root-thread array with nested `replies`, anchors, `review_version` and resolution fields. Compare each thread's version to the current draft; historical feedback does not prove a selection still matches today's text.
2. After preview and confirmation, add a root comment with `POST /api/v1/blogs/admin/{id}/comments/`: send the current `expected_version`, a nonblank `body` of at most 2,000 characters, and `field="overall"` with no offsets or quote. For a text selection, use `field="title"`, `"summary"` or `"content"`, with `start_offset`, `end_offset` and the exact saved `quote`. Offsets count **UTF-16 code units**, not Python characters or UTF-8 bytes; start is inclusive, end exclusive, and the selection spans at most 2,000 code units. Never anchor to unsaved text. On 409, refresh the draft and recompute the selection; on a quote mismatch, reread the saved source rather than guessing offsets.
3. Reply to a root thread with `POST /api/v1/blogs/admin/{id}/comments/{comment_id}/replies/` and `{"body":"REVIEW_REPLY"}` (1–2,000 nonblank characters). Replies keep the root's review version; replying to a resolved thread reopens it. Use the root ID, not a reply ID.
4. Resolve or reopen a root thread with `PATCH /api/v1/blogs/admin/{id}/comments/{comment_id}/` and `{"resolved":true}` or `{"resolved":false}`. Replies and resolution do not require `expected_version`; reread the thread and confirm its ID and intended action before sending. Resolving feedback does not approve or publish the draft; retain the peer-review workflow above.

All blog writes require a preview and explicit user confirmation: without `confirm=true`, MCP tools only return a dry-run preview. The REST review routes above execute immediately and have no dry-run flag: preview the method, article ID and body locally and obtain confirmation before sending them with the platform Bearer token. Prefer a matching MCP tool if its discovered schema supports the operation; do not invent submission/rejection tool names or CLI flags. Confirm the article, version and publication time before executing; a successful preview is not evidence of a saved, submitted, approved or published post. If the required operation or permission is unavailable, stop and request the appropriate authorization.

## Write-operation safety

Creating/deleting keys, creating/paying orders, deleting platform tokens, and
publishing announcements or blogs are **irreversible, money-related or publicly visible**. Always:

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

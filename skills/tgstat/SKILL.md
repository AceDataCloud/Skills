---
name: tgstat
description: Search Telegram channels/chats and pull audience + engagement stats (subscribers, reach, ER/ERR) from TGStat via its Stat API. Use when the user wants to find Telegram channels to advertise in (esp. Russian-language / RU market), research competitor channels, or check a channel's reach/engagement before buying an ad placement.
when_to_use: |
  Trigger when the user wants to discover Telegram channels by keyword /
  category / country / language, inspect a specific channel's subscriber
  count, average post reach and engagement (ER / ERR) to judge ad value,
  or check their TGStat API quota. This is a marketing-research /
  ad-channel-selection tool — it does NOT post to Telegram (use the
  `telegram` connector for reading/sending messages).
connections: [tgstat]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Call the **TGStat Stat API** with `curl + jq`. The user's token is in
`$TGSTAT_TOKEN` and is passed as the `token` query parameter on every request.
Base URL: `https://api.tgstat.ru`.

Responses are JSON shaped `{"status":"ok","response": ...}`. Errors come back as
`{"status":"error","error":"<message>"}` — show the `error` verbatim. An invalid
token or an inactive/expired API plan will surface here; tell the user to check
their token / plan in the TGStat 个人中心 and re-connect the connector.

**Always confirm the token + remaining quota first** (`usage/stat` is free and
does not count against tariff quota):

```bash
curl -sS "https://api.tgstat.ru/usage/stat?token=$TGSTAT_TOKEN" \
  | jq '.status, (.response[]? | {serviceKey, title, spentChannels, spentRequests, expiredAt})'
```

## Find channels to advertise in (the main workflow)

`GET /channels/search` — at least one of `q` (keyword, min 3 chars) or
`category` is required.

Params: `q`, `category`, `country`, `language` (default `russian`),
`peer_type` (`channel` | `chat` | `all`, default `channel`),
`search_by_description` (`0`/`1`), `limit` (max 100).

```bash
# Russian-language AI/ChatGPT channels, biggest first.
curl -sS "https://api.tgstat.ru/channels/search" \
  --data-urlencode "token=$TGSTAT_TOKEN" \
  --data-urlencode "q=нейросети" \
  --data-urlencode "language=russian" \
  --data-urlencode "peer_type=channel" \
  --data-urlencode "limit=50" -G \
  | jq '.response.items | sort_by(-.participants_count)
        | .[] | {username, title, subs: .participants_count, ci_index, link}'
```

- Use `--data-urlencode ... -G` so Cyrillic / spaces in `q` are encoded correctly.
- `ci_index` (индекс цитирования) is TGStat's citation/authority score — higher =
  more reposted/mentioned elsewhere, a useful quality signal beyond raw subs.
- Try several keywords (`ChatGPT`, `нейросети`, `AI`, `разработка`, `API`) and
  merge results; TGStat matches title/username (add `search_by_description=1` to
  also match the channel description).

## Judge a channel's ad value

`GET /channels/stat?channelId=<@username | t.me/username | tgstat id>` returns
the numbers that actually matter for ad pricing:

```bash
curl -sS "https://api.tgstat.ru/channels/stat?token=$TGSTAT_TOKEN&channelId=@durov" \
  | jq '.response | {
      subs: .participants_count,
      avg_post_reach,          # средний охват публикации
      adv_reach_24h: .adv_post_reach_24h,   # рекламный охват за 24ч — key for CPM
      er_percent, err_percent, err24_percent,
      daily_reach, ci_index, posts_count
    }'
```

- For **ad CPM estimation** use `adv_post_reach_24h` (average *advertising* reach
  of a post over 24h), not raw subscriber count — subs are vanity, reach is what
  the ad actually gets seen by.
- Low `err_percent` / `err24_percent` relative to subs = inflated/dead audience →
  skip it.
- For a **chat** (not channel) the response instead has `dau`/`wau`/`mau` and
  `messages_count_*` fields.

`GET /channels/get?channelId=...` returns descriptive info (title, about,
`category`, `country`, `language`, `participants_count`, `ci_index`) when you
just need to identify/verify a channel rather than full stats.

## Reference data

`GET /database/categories?token=$TGSTAT_TOKEN` lists valid `category` values you
can pass to `channels/search`. There are also `/database/countries` and
`/database/languages`. (See the docs for the full parameter/response shape.)

## Gotchas

- **Plan gating:** `channels/search` needs a **Stat API tariff S or higher**;
  `channels/stat` / `channels/get` work on all Stat tariffs. If a call returns an
  access error, the user's plan doesn't cover that method.
- **Quota:** each unique channel and each request counts against the monthly
  tariff (visible via `usage/stat`). Don't loop over hundreds of channels
  blindly — search, shortlist, then `stat` only the shortlist.
- **`q` min length is 3 chars** → `{"error":"param q is too short"}`.
- **Cyrillic:** always send `q` via `--data-urlencode` (or pre-URL-encode) so the
  keyword isn't mangled.
- TGStat is a Russian service; the API and billing are RU-side — availability and
  payment are the account owner's responsibility.

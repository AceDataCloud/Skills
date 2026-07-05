---
name: didi-ride
description: 通过滴滴出行 MCP 打车、查价、查询订单、取消订单、规划路线（驾车/公交/步行/骑行）和搜索地点。Use when the user mentions 滴滴, 打车, 叫车, 回家/上班要打车, 查一下从 A 到 B 多少钱/怎么走, 查询订单, 司机在哪/多久到, 预约叫车, 路线规划, DiDi, ride-hailing, or booking a taxi.
when_to_use: |
  Trigger for anything involving the user's DiDi (滴滴出行) account:
  book a ride ("打车去…", "回家", "上班"), get a fare/route estimate,
  query an existing order (driver location, ETA, trip progress), cancel
  an order, plan a driving/transit/walking/cycling route, or search
  places / reverse-geocode. Creating and cancelling orders act on real
  money and a real driver, so those writes are gated behind explicit
  confirmation.
connections: [didi]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# DiDi Ride (滴滴出行)

Drive the user's **DiDi (滴滴出行)** account through the DiDi MCP server:
book rides, estimate fares, track orders, cancel, and plan routes.

The `didi` BYOC connector injects one env var into the sandbox:

- `DIDI_MCP_KEY` — the user's DiDi MCP key. **Secret — never echo, print, or log it.**

If `DIDI_MCP_KEY` is missing, tell the user to connect the DiDi connector at
[auth.acedata.cloud/user/connections](https://auth.acedata.cloud/user/connections)
(they get the key by scanning the QR in the 滴滴出行 App or via
<https://mcp.didichuxing.com/claw>).

## CLI

The skill ships a stdlib-only helper that speaks the MCP Streamable-HTTP
protocol to DiDi. **Run this resolver at the top of every Bash block below** —
each Bash call is a fresh shell, and `$SKILL_DIR` points at the LAST skill loaded
this turn, so anchor on our own script:

```bash
DIDI="$SKILL_DIR/scripts/didi.py"; [ -f "$DIDI" ] || DIDI=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/didi.py' 2>/dev/null | head -1)
[ -f "$DIDI" ] || { echo "didi-ride script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
```

Two commands:

```bash
python3 $DIDI list                        # list tools + their JSON input schemas
python3 $DIDI call <tool> '<json-args>'   # call any tool
```

**Always check `references/api_references.md` for the exact tool + parameter
names before calling.** When unsure, run `python3 $DIDI list` — it returns the
authoritative input schema for every tool straight from DiDi. Do **not** guess
parameter names (common mistakes: `keyword` → `keywords`, `region` → `city`,
four coord fields → six `from_name/from_lat/from_lng/to_name/to_lat/to_lng`).

All argument **values must be strings** (including coordinates and
`product_category`), e.g. `{"product_category":"1"}` not `{"product_category":1}`.

## Write gating (real money / real driver)

`taxi_create_order` and `taxi_cancel_order` are **gated**: without a trailing
`--confirm` the helper only DRY-RUNS and changes nothing. Run once without
`--confirm` to preview, then re-run with `--confirm` as the **last** argument
after the user approves:

```bash
python3 $DIDI call taxi_create_order '{"estimate_trace_id":"...","product_category":"1"}' --confirm
```

- Even when the user says "打车" / "取消订单", confirm the concrete details
  (起终点、车型 for booking; the order for cancelling) before adding `--confirm`.
- Cancel intent ≠ cancel confirmation — always ask "确认取消吗？" first.

## Booking flow (最小可执行)

1. **Resolve addresses** — `maps_textsearch` (never invent coordinates; don't
   reuse coordinates from earlier turns — the user may have moved).
   - If the user references an address alias (家 / 公司 / etc.) that you don't
     have, ask them; this skill has no stored preferences.
2. **Confirm start/end** — if `maps_textsearch` returns ≥2 candidates, list at
   least the top 3 and let the user pick; a single exact match needs no
   confirmation.
3. **Estimate** — `taxi_estimate`; record the returned `traceId` /
   `estimate_trace_id`. It expires (`-32021`) — re-estimate if stale.
4. **Pick car type** — user's current message wins ("叫快车"→`product_category`
   `1`, "专车"→`8`); otherwise ask. Only use categories present in the
   `taxi_estimate` response; never silently substitute a different service level
   (快车 `1` ≠ 特惠快车 `201`).
5. **Create order** — `taxi_create_order` with the latest `estimate_trace_id`
   (dry-run → confirm → `--confirm`).
6. **Report** — order id, start/end, car type, estimated fare. Tell the user
   they can send 「查询订单」 to check status.

## Query an order

Order id comes from (in priority): the user's message → the most recent order
created this conversation → else ask.

```bash
python3 $DIDI call taxi_query_order '{"order_id":"ORDER_ID"}'
```

Status codes (`code`):

| code | 含义 | 输出 |
|------|------|------|
| 0 | 匹配中 | ⏳ 正在为您匹配司机 |
| 1 | 司机已接单 | 展示司机姓名、车型、车牌、电话、距离与预计到达时间 |
| 2 | 司机已到达 | 🔔 司机已到达上车点 |
| 4 | 行程进行中 | 🚗 行程已开始 |
| 5 | 订单完成 | ✅ 行程结束（展示费用，如有） |
| 6 | 系统取消 | ❌ 订单已被系统取消 |
| 7 | 已取消 | ❌ 订单已取消 |
| 3 / 8-12 | 其他终态 | 显示对应状态描述 |

## Routes & places (no order needed)

```bash
python3 $DIDI call maps_direction_driving  '{"from_name":"...","from_lat":"...","from_lng":"...","to_name":"...","to_lat":"...","to_lng":"..."}'
python3 $DIDI call maps_direction_transit  '{...}'   # 公交
python3 $DIDI call maps_direction_walking  '{...}'   # 步行
python3 $DIDI call maps_direction_bicycling '{...}'  # 骑行
python3 $DIDI call maps_place_around '{"keywords":"咖啡","lat":"...","lng":"..."}'
python3 $DIDI call maps_regeocode '{"lat":"...","lng":"..."}'
```

## Gotchas

- **Never print the key or the raw endpoint URL** — the helper handles the
  transport and keeps the key internal.
- `taxi_create_order` takes only `estimate_trace_id`, `product_category`, and
  optional `caller_car_phone`. Don't pass the estimate's coordinate/name fields.
- No stored preferences: this skill doesn't remember home/work/car type — ask
  the user, or wire richer memory in a higher layer.
- Auth failure surfaces as `-32002` (or HTTP 401/403): the key is missing/expired
  → have the user reconnect the connector.

> **Setup:** See [authentication](../_shared/authentication.md). This skill uses
> the `didi` connector's injected `DIDI_MCP_KEY`, not `ACEDATACLOUD_API_TOKEN`.

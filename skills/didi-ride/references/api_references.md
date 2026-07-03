# DiDi MCP — Tool Reference

Authoritative schemas come from `python3 $DIDI list` (the DiDi server returns
each tool's `inputSchema`). This file summarizes the tools and the parameter
names that are easy to get wrong. **All values are strings.**

## Places & geocoding

### `maps_textsearch` — search a place by text
| param | required | notes |
|-------|----------|-------|
| `keywords` | yes | search text, e.g. `北京西站` (NOT `keyword`) |
| `city` | no | city name to scope the search, e.g. `北京` (NOT `region`) |

Returns candidate places with names + coordinates. Use these coordinates for
`taxi_estimate` and the `maps_direction_*` tools.

### `maps_regeocode` — coordinates → address
| param | required |
|-------|----------|
| `lat` | yes |
| `lng` | yes |

## Routes

`maps_direction_driving` / `maps_direction_transit` / `maps_direction_walking`
/ `maps_direction_bicycling` — all take the same six fields:

| param | required |
|-------|----------|
| `from_name` | yes |
| `from_lat` | yes |
| `from_lng` | yes |
| `to_name` | yes |
| `to_lat` | yes |
| `to_lng` | yes |

### `maps_place_around` — nearby POI search
| param | required | notes |
|-------|----------|-------|
| `keywords` | yes | POI keyword, e.g. `咖啡` |
| `lat` | yes | center latitude |
| `lng` | yes | center longitude |

## Ride hailing

### `taxi_estimate` — price/ETA estimate (do this before ordering)
Six coordinate/name fields (same as routes):
`from_name`, `from_lat`, `from_lng`, `to_name`, `to_lat`, `to_lng`.

Returns a list of available car types, each with a `productCategory` and price,
plus a `traceId` / `estimate_trace_id` required by `taxi_create_order`. The
trace id expires — a stale one returns `-32021`; re-estimate to refresh.

Common `product_category` values:

| code | 车型 |
|------|------|
| `1` | 快车 |
| `8` | 专车 |
| `201` | 特惠快车 |

> Treat these as hints — always match against the `productCategory` values the
> live `taxi_estimate` response actually returns. `1` (快车) and `201`
> (特惠快车) are different service levels; never swap one for the other.

### `taxi_create_order` — book the ride  ⚠️ WRITE (needs `--confirm`)
| param | required | notes |
|-------|----------|-------|
| `estimate_trace_id` | yes | from the latest `taxi_estimate` |
| `product_category` | yes | chosen car type code (string) |
| `caller_car_phone` | no | omit unless the user gives a number |

Only these three fields. Do **not** pass coordinate/name fields.

### `taxi_query_order` — status + driver location
| param | required |
|-------|----------|
| `order_id` | yes |

Status `code`: `0` 匹配中 · `1` 司机已接单 · `2` 司机已到达 · `4` 行程中 ·
`5` 完成 · `6` 系统取消 · `7` 已取消 · `3`/`8`-`12` 其他终态.

### `taxi_cancel_order` — cancel  ⚠️ WRITE (needs `--confirm`)
| param | required |
|-------|----------|
| `order_id` | yes |

Always ask "确认取消吗？" before adding `--confirm`.

## Errors

| code | meaning | action |
|------|---------|--------|
| `-32002` / HTTP 401 / 403 | auth failed | key missing/expired → reconnect connector |
| `-32021` | estimate trace expired | re-run `taxi_estimate` |
| HTTP 400 | bad params | re-check parameter names against `didi.py list` |

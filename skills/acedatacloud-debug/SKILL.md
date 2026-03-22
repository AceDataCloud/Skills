---
name: acedatacloud-debug
description: Debug AceDataCloud production issues using CLS logs. Use when investigating API errors, 5xx alerts, tracing request flows, or diagnosing billing discrepancies. Leverages Tencent Cloud CLS structured logging with trace IDs.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires access to PlatformBackend/.env with TENCENT_CLOUD_SECRET_ID and TENCENT_CLOUD_SECRET_KEY.
allowed-tools: Bash(python3 *)
---

# AceDataCloud Debug — Production Issue Investigation

Debug production API issues using Tencent Cloud CLS (Cloud Log Service) structured logs.

## Prerequisites

- Access to `PlatformBackend/.env` with `TENCENT_CLOUD_SECRET_ID` and `TENCENT_CLOUD_SECRET_KEY`
- The `cls_search.py` script at `.claude/scripts/cls_search.py`

## Log Topics

| Topic | ID | Content |
|-------|----|---------|
| **trace** | `751a7350-dc5d-41c3-a6ca-c178bae05807` | PlatformGateway container logs — auth/record phases, upstream responses, errors |
| **api-usages** | `fbb6d4ce-4c55-418a-87e0-f6e15815b3a9` | Structured billing records — trace_id, api_name, status_code, deducted_amount |

## Workflow 1: Debug by Trace ID

When a user provides a specific trace ID from an API error response.

```bash
python3 .claude/scripts/cls_search.py --trace-id <TRACE_ID> --time 7d --limit 50 2>/dev/null
```

This searches **both** topics and returns:
- **Trace logs:** Chronological request flow through PlatformGateway (auth → upstream → record)
- **API usage record:** Structured billing with api_name, status_code, deducted_amount

## Workflow 2: Investigate Service Alerts

When a service is alerting ("XXX 报警了") — find what's failing.

### Step 1: Query 5xx Errors with Chain Mode

```bash
python3 .claude/scripts/cls_search.py --service <SERVICE_NAME> --5xx --chain --time 1h --limit 10 2>/dev/null
```

Chain mode automatically:
1. Finds 5xx error records in api-usages
2. Extracts trace IDs
3. Queries trace logs for each
4. Shows error-relevant lines

### Step 2: Analyze Patterns

Look for:
- **Repeated error messages** → upstream provider issue
- **Specific model failures** → model offline or rate-limited
- **Timeout patterns** → upstream slow response
- **Account/balance errors** → upstream provider balance depleted

### Important Rules

- **"报警" (alert) = 5xx errors only** — always use `--5xx`. Ignore 4xx (403 = auth issues, 499 = client disconnect — these are normal)
- **Always chain-query** — api-usages only shows status_code; the root cause is in trace logs
- **Key error patterns to grep:** `error`, `message`, `failed`, `account`, `offline`, `timeout`, `errorResult`

## Workflow 3: Check Recent Usage

```bash
python3 .claude/scripts/cls_search.py --service <SERVICE_NAME> --time 1h --limit 20 2>/dev/null
```

## Script Flags

| Flag | Description |
|------|-------------|
| `--trace-id <ID>` | Search by specific trace ID |
| `--service <NAME>` | Filter by service name/alias |
| `--5xx` | Only show 5xx errors |
| `--chain` | Auto-follow trace IDs from usage records |
| `--time <PERIOD>` | Time range: `1h`, `6h`, `1d`, `7d` |
| `--limit <N>` | Max results to return |

## Service Name Mapping

Use `PlatformBackend/cost/service_api_mapping.json` to find service aliases and API paths.

## Gotchas

- CLS region is `ap-hongkong` — queries may take a few seconds
- Chain mode is the most useful for alert investigation — always use it
- 499 status codes are client disconnects, NOT server errors — ignore them
- 403 errors in trace logs often mean content moderation or depleted user balance
- The trace topic contains raw container logs (loguru format), api-usages has structured records

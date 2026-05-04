---
name: tencentcloud-cls
description: |
  Search and analyze Tencent Cloud CLS (Cloud Log Service) logs. Use
  whenever the user asks to: search logs, debug API errors, trace
  requests by trace ID, find 5xx errors, run CQL/SQL analytics over
  log topics, extract structured fields. Backed by the official
  tencentcloud-sdk-python CLS client.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [tencentcloud]
---

# Tencent Cloud CLS (Log Service) — Search & Analysis

Search and run CQL / SQL analytics over Tencent Cloud CLS log topics.

> **Setup:** See [tencentcloud authentication](../_shared/tencentcloud.md). The SDK reads `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY` / `TENCENTCLOUD_REGION` from the environment.
>
> **Companion skill:** Use `tencentcloud-cls-alarm` for alarm policy / notice group / shield management. This skill is only about searching log content.

## CLI (preferred)

The skill ships [`scripts/cls.py`](scripts/cls.py) — a self-contained CLI for the most common operations.

```bash
CLS=$SKILL_DIR/scripts/cls.py

python3 $CLS topics                                              # list topics
python3 $CLS search --topic <topic-id> --query 'level:ERROR' --time 1h
python3 $CLS search --topic <topic-id> --trace-id <uuid>
python3 $CLS search --topic <topic-id> --time 1d \
    --query '* | SELECT api_name, count(*) AS cnt GROUP BY api_name ORDER BY cnt DESC LIMIT 20' \
    --format json
```

`--time` accepts `30m / 1h / 6h / 1d / 7d`. `--query` is CQL by default; pass `--lucene` to switch dialect. Append `| SELECT ... GROUP BY ...` to a query for SQL analytics.

For anything beyond what the CLI exposes (custom field projections, raw paginated walks, `Context`-based tailing) drop down to the SDK calls below.

## When to Use

- Find recent errors / 5xx responses for a service
- Look up a single request by trace ID across multiple topics
- Run CQL filters (`status_code:>=500 AND service:"openai"`)
- Run SQL analytics (`SELECT api_name, COUNT(*) GROUP BY api_name`)
- Chain trace logs to reconstruct a request lifecycle
- Extract specific fields for billing / audit reports

## Dependencies

```bash
pip install tencentcloud-sdk-python
```

## Quick start

```python
import os
import json
from tencentcloud.common import credential
from tencentcloud.cls.v20201016 import cls_client, models

cred = credential.EnvironmentVariableCredential().get_credential()
client = cls_client.ClsClient(cred, os.environ["TENCENTCLOUD_REGION"])
```

## Workflows

### Discover topics

```python
req = models.DescribeTopicsRequest()
resp = client.DescribeTopics(req)
for t in resp.Topics:
    print(t.TopicId, t.TopicName, t.LogsetId)
```

> Tip: ask the user for the topic ID up front. Topic IDs look like `751a7350-dc5d-41c3-a6ca-c178bae05807` and aren't guessable from a service name.

### Search logs (CQL)

```python
import time

req = models.SearchLogRequest()
req.TopicId = "<topic-id>"
req.From = int((time.time() - 3600) * 1000)   # 1 hour ago, ms epoch
req.To = int(time.time() * 1000)
req.Query = 'status_code:>=500 AND service:"openai"'
req.Limit = 100
req.Sort = "desc"
req.SyntaxRule = 1                             # 1 = CQL, 0 = Lucene

resp = client.SearchLog(req)
for line in resp.Results:
    fields = {f.Key: f.Value for f in line.LogJson and []}  # see below
    print(line.Time, line.PkgLogId, fields.get("status_code"), fields.get("api_name"))
```

> CLS hands you `Results` with `LogJson` as a JSON string per record. Decode with `json.loads(line.LogJson)` to get a flat dict of all the indexed fields the topic stores.

### Look up a trace ID across multiple topics

```python
TRACE_ID = "34341776-0835-422a-956d-ac8d5b404db1"
TOPICS = {
    "trace": "<trace-topic-id>",
    "api-usages": "<api-usages-topic-id>",
}

for label, topic_id in TOPICS.items():
    req = models.SearchLogRequest()
    req.TopicId = topic_id
    req.From = int((time.time() - 86400) * 1000)
    req.To = int(time.time() * 1000)
    req.Query = f'trace_id:"{TRACE_ID}"'
    req.Limit = 100
    req.SyntaxRule = 1
    resp = client.SearchLog(req)
    print(f"--- {label}: {len(resp.Results)} records ---")
    for line in resp.Results:
        print(line.Time, line.LogJson)
```

### SQL analytics

CLS supports a SQL-on-logs subset for aggregation. Append `| <SQL>` to a CQL filter:

```python
req.Query = '* | SELECT api_name, count(*) AS cnt GROUP BY api_name ORDER BY cnt DESC LIMIT 20'
req.SyntaxRule = 1
resp = client.SearchLog(req)
# When the query has a `|`, results land in resp.Analysis (rows of column→value)
for row in resp.AnalysisResults or []:
    print(row)
```

### Tail recent logs

```python
# Poll every 5s for new lines after the last cursor
last_cursor = None
while True:
    req = models.SearchLogRequest()
    req.TopicId = topic_id
    req.From = int((time.time() - 30) * 1000)
    req.To = int(time.time() * 1000)
    req.Query = 'level:ERROR'
    req.Limit = 100
    req.Sort = "asc"
    req.SyntaxRule = 1
    if last_cursor:
        req.Context = last_cursor
    resp = client.SearchLog(req)
    for line in resp.Results:
        print(line.Time, line.LogJson)
    last_cursor = resp.Context
    time.sleep(5)
```

## CQL cheatsheet

| Pattern | Meaning |
|---|---|
| `status_code:500` | exact match |
| `status_code:>=500` | range |
| `status_code:[500 TO 599]` | range with bounds |
| `service:"openai"` | quoted phrase (use for values containing spaces) |
| `NOT level:DEBUG` | negation |
| `service:openai AND status_code:>=400` | conjunction |
| `(api:foo OR api:bar)` | grouping |
| `* | SELECT ... GROUP BY ...` | switch into SQL analytics |

## Pagination

CLS returns up to 1000 records per call. For larger result sets, iterate with `Context`:

```python
all_records = []
context = None
while True:
    req = models.SearchLogRequest()
    req.TopicId = topic_id
    req.From = ...
    req.To = ...
    req.Query = '...'
    req.Limit = 1000
    req.SyntaxRule = 1
    if context:
        req.Context = context
    resp = client.SearchLog(req)
    all_records.extend(resp.Results)
    context = resp.Context
    if not context or len(resp.Results) < 1000:
        break
```

## Error patterns

| Symptom | Likely cause |
|---|---|
| `InvalidParameter.QueryError` | Quote phrases that contain `:` or spaces; check `SyntaxRule` matches the query |
| `LimitExceeded` | Concurrent `SearchLog` calls exceed the 30-QPS quota — back off & retry |
| `OperationDenied.AccountIsolated` | CLS service is suspended for billing — check the console |
| Empty `Results` but logs visible in console | Time range is wrong (`From` / `To` are ms epoch, not seconds), or topic has different field names than the query expects |

## Console links

- CLS console: <https://console.cloud.tencent.com/cls/topic>
- CQL syntax: <https://www.tencentcloud.com/document/product/614/47044>
- SQL analytics syntax: <https://www.tencentcloud.com/document/product/614/58978>

---
name: tencentcloud-edgeone
description: |
  Manage Tencent Cloud EdgeOne (CDN + edge security). Use when the user
  asks to: list zones, purge CDN cache (URL / prefix / hostname / all),
  prefetch URLs to warm edges, check purge / prefetch task status,
  manage acceleration domains, list / create / delete EdgeOne DNS
  records, inspect WAF / security configuration. Backed by the official
  tencentcloud-sdk-python TEO client.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [tencentcloud]
---

# Tencent Cloud EdgeOne (CDN + Security)

Manage EdgeOne zones — purge cache, prefetch URLs, manage DNS records on the zone, check WAF settings.

> **Setup:** See [tencentcloud authentication](../_shared/tencentcloud.md). The SDK reads `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY` from env. EdgeOne is global — `Region=""` is fine.

## CLI (preferred)

The skill ships [`scripts/edgeone.py`](scripts/edgeone.py) — wraps zone discovery, purge / prefetch, task tracking, EdgeOne DNS records, and WAF inspection.

```bash
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script (re-run this at the top of every fresh-shell Bash block).
EO="$SKILL_DIR/scripts/edgeone.py"; [ -f "$EO" ] || EO=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/edgeone.py' 2>/dev/null | head -1)
[ -f "$EO" ] || { echo "tencentcloud-edgeone script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

python3 $EO zones                                                  # list zones
python3 $EO zone zone-xxxxxxxx                                     # one zone's details
python3 $EO domains zone-xxxxxxxx                                  # acceleration domains
python3 $EO purge zone-xxxxxxxx --urls https://hub.example.com/index.html
python3 $EO purge zone-xxxxxxxx --prefixes https://hub.example.com/assets/
python3 $EO purge zone-xxxxxxxx --hosts hub.example.com
python3 $EO purge zone-xxxxxxxx --all                              # nuclear
python3 $EO prefetch zone-xxxxxxxx --urls https://hub.example.com/ https://hub.example.com/chat
python3 $EO purge-tasks zone-xxxxxxxx --status processing
python3 $EO prefetch-tasks zone-xxxxxxxx
python3 $EO dns zone-xxxxxxxx                                      # EdgeOne DNS records
python3 $EO dns-create zone-xxxxxxxx --name sub --type CNAME --content origin.example.com
python3 $EO dns-delete zone-xxxxxxxx <record-id>
python3 $EO security zone-xxxxxxxx                                 # WAF / security cfg
python3 $EO waf zone-xxxxxxxx
```

Purge / prefetch propagation is global but typically takes 30s–2min. Use `purge-tasks --status processing` to wait.

## When to Use

- List EdgeOne zones / acceleration domains
- Purge cache after a deploy (by URL, prefix, hostname, or whole zone)
- Prefetch URLs to warm edge nodes
- Track purge / prefetch task status
- Manage EdgeOne DNS records (zones managed by EdgeOne use the TEO API, not DNSPod)
- Inspect WAF / security config

## Dependencies

```bash
pip install tencentcloud-sdk-python
```

## Quick start

```python
import os
from tencentcloud.common import credential
from tencentcloud.teo.v20220901 import teo_client, models

cred = credential.EnvironmentVariableCredential().get_credential()
client = teo_client.TeoClient(cred, "")
```

## Workflows

### List zones

```python
req = models.DescribeZonesRequest()
req.Limit = 100
resp = client.DescribeZones(req)
for z in resp.Zones:
    print(z.ZoneId, z.ZoneName, z.Status, z.Type)
```

> Zone IDs look like `zone-xxxxxxxx`. The `ZoneName` is the apex domain (e.g. `acedata.cloud`).

### List acceleration domains in a zone

```python
req = models.DescribeAccelerationDomainsRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Limit = 100
resp = client.DescribeAccelerationDomains(req)
for d in resp.AccelerationDomains:
    print(d.DomainName, d.DomainStatus, d.OriginDetail.OriginType)
```

### Purge cache — by URL

```python
req = models.CreatePurgeTaskRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Type = "purge_url"
req.Targets = [
    "https://hub.example.com/index.html",
    "https://hub.example.com/assets/main.css",
]
resp = client.CreatePurgeTask(req)
print("Task:", resp.JobId)
```

### Purge by hostname (entire host)

```python
req = models.CreatePurgeTaskRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Type = "purge_host"
req.Targets = ["hub.example.com"]
client.CreatePurgeTask(req)
```

### Purge by prefix (all URLs under a path)

```python
req = models.CreatePurgeTaskRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Type = "purge_prefix"
req.Targets = ["https://hub.example.com/assets/"]
client.CreatePurgeTask(req)
```

### Purge ALL cache for a zone (nuclear option)

```python
# Confirm with the user — this re-fetches every cached object on next request,
# spiking origin load.
req = models.CreatePurgeTaskRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Type = "purge_all"
client.CreatePurgeTask(req)
```

### Prefetch (pre-warm edges)

```python
req = models.CreatePrefetchTaskRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Targets = [
    "https://hub.example.com/",
    "https://hub.example.com/chat",
]
resp = client.CreatePrefetchTask(req)
print("Task:", resp.JobId)
```

### Track task status

```python
req = models.DescribePurgeTasksRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Limit = 50
# Optional: req.Filters = [{"Name": "job-id", "Values": ["<job-id>"]}]
resp = client.DescribePurgeTasks(req)
for t in resp.Tasks:
    print(t.JobId, t.Type, t.Status, t.CreateTime)

# Same shape for DescribePrefetchTasks
```

### List EdgeOne DNS records on a zone

```python
req = models.DescribeDnsRecordsRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Limit = 100
resp = client.DescribeDnsRecords(req)
for r in resp.DnsRecords:
    print(r.RecordId, r.Name, r.Type, r.Content)
```

### Create an EdgeOne DNS record

```python
req = models.CreateDnsRecordRequest()
req.ZoneId = "zone-xxxxxxxx"
req.Name = "sub.example.com"
req.Type = "CNAME"
req.Content = "origin.example.com"
req.TTL = 600
client.CreateDnsRecord(req)
```

### Delete an EdgeOne DNS record

```python
req = models.DeleteDnsRecordsRequest()
req.ZoneId = "zone-xxxxxxxx"
req.RecordIds = ["<record-id>"]
client.DeleteDnsRecords(req)
```

## Purge type cheatsheet

| Type | When to use | Caveat |
|---|---|---|
| `purge_url` | Specific page / asset changed | Most surgical; up to 1000 URLs per call |
| `purge_prefix` | A directory of assets changed (`/assets/...`) | Treats target as a prefix match |
| `purge_host` | Full site deployment | Affects everything on the hostname |
| `purge_all` | Emergency / major migration | All cache for the zone — origin spike inevitable |

## Typical post-deploy sequence

```python
# 1. Purge the hostname so users get the new bundle
client.CreatePurgeTask(models.CreatePurgeTaskRequest(
    ZoneId="zone-xxxxxxxx",
    Type="purge_host",
    Targets=["hub.example.com"],
))

# 2. Prefetch the most-trafficked routes so edge cache is warm
client.CreatePrefetchTask(models.CreatePrefetchTaskRequest(
    ZoneId="zone-xxxxxxxx",
    Targets=[
        "https://hub.example.com/",
        "https://hub.example.com/chat",
        "https://hub.example.com/login",
    ],
))

# 3. Watch for completion (typically 30s – 2min)
import time
while True:
    resp = client.DescribePurgeTasks(models.DescribePurgeTasksRequest(
        ZoneId="zone-xxxxxxxx",
        Filters=[{"Name": "status", "Values": ["processing"]}],
    ))
    if not resp.Tasks:
        print("All purge tasks done.")
        break
    print(f"{len(resp.Tasks)} tasks still processing...")
    time.sleep(15)
```

## Important reminders

- **`purge_all` causes origin load spike.** Use only when surgical purges aren't enough.
- **Prefetch isn't free** — it counts against your CDN traffic quota at edge-warm time. Only prefetch URLs you're confident users will hit.
- **Purge / prefetch propagation is global** but takes 30s–2min. Plan deploy windows accordingly.
- EdgeOne DNS and DNSPod DNS are *separate*. Domains onboarded to EdgeOne with NS-mode resolve through the TEO API; CNAME-mode domains still resolve through whatever DNS you've configured (DNSPod or third-party). Use the right skill for the right zone type.

## Console links

- EdgeOne console: <https://console.cloud.tencent.com/edgeone>
- API reference: <https://www.tencentcloud.com/document/product/1145/53929>

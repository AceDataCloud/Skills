---
name: tencentcloud-dns
description: |
  Manage DNS records on DNSPod (Tencent Cloud's DNS service). Use when
  the user asks to add / update / delete A / AAAA / CNAME / MX / TXT /
  NS / SRV / CAA records, list records for a domain, search records,
  add ACME challenge / SPF / DKIM / domain-verification TXT records.
  Backed by the official tencentcloud-sdk-python DNSPod client.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [tencentcloud]
---

# DNSPod (Tencent Cloud DNS)

Manage DNS records via the DNSPod API.

> **Setup:** See [tencentcloud authentication](../_shared/tencentcloud.md). DNSPod uses the **same** Tencent Cloud SecretId / SecretKey as the rest of the platform — there's no separate `DP_Id` / `DP_Key` for the v3 API. The SDK client below auto-reads `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY` from env.
>
> The legacy v2 DNSPod API used a different key format; this skill targets the v3 SDK exclusively.

## When to Use

- Add a new subdomain (A / AAAA / CNAME)
- Update an existing record (change IP, change CNAME target)
- Add email-related records (MX, SPF / DKIM / DMARC TXT)
- Add domain-verification TXT records (Google / Search Console / SSL ACME challenges)
- List or search records on a domain
- Delete obsolete records

## Dependencies

```bash
pip install tencentcloud-sdk-python
```

## Quick start

```python
import os
from tencentcloud.common import credential
from tencentcloud.dnspod.v20210323 import dnspod_client, models

cred = credential.EnvironmentVariableCredential().get_credential()
# DNSPod is global — region is ignored, but the SDK still requires one.
client = dnspod_client.DnspodClient(cred, "")
```

## Workflows

### List domains in the account

```python
req = models.DescribeDomainListRequest()
req.Limit = 100
resp = client.DescribeDomainList(req)
for d in resp.DomainList:
    print(d.DomainId, d.Name, d.Status, d.RecordCount)
```

### List records for a domain

```python
req = models.DescribeRecordListRequest()
req.Domain = "example.com"
req.Limit = 100                  # max 3000
# Optional: req.RecordType = "A"
# Optional: req.Subdomain = "api"
resp = client.DescribeRecordList(req)
for r in resp.RecordList:
    print(r.RecordId, r.Name, r.Type, r.Value, "TTL=", r.TTL, "Line=", r.Line)
```

### Search by keyword (filter client-side)

```python
req = models.DescribeRecordListRequest()
req.Domain = "example.com"
req.Limit = 3000
resp = client.DescribeRecordList(req)
matches = [r for r in resp.RecordList if "api" in r.Name or "api" in r.Value]
for r in matches:
    print(r.RecordId, r.Name, r.Type, r.Value)
```

### Create records

```python
def create_record(domain, sub_domain, record_type, value, ttl=600, mx=None):
    req = models.CreateRecordRequest()
    req.Domain = domain
    req.SubDomain = sub_domain   # use "@" for the apex
    req.RecordType = record_type
    req.RecordLine = "默认"      # "Default" line — works in all environments
    req.Value = value
    req.TTL = ttl
    if mx is not None:
        req.MX = mx
    resp = client.CreateRecord(req)
    return resp.RecordId

# A record
rid = create_record("example.com", "www", "A", "1.2.3.4")
# CNAME (note: Value MUST end with a dot for absolute target)
rid = create_record("example.com", "api2", "CNAME", "api.example.com.")
# MX (priority via mx=)
rid = create_record("example.com", "@", "MX", "mail.example.com.", mx=10)
# TXT (SPF)
rid = create_record("example.com", "@", "TXT", '"v=spf1 include:_spf.google.com ~all"')
# ACME challenge for cert issuance
rid = create_record("example.com", "_acme-challenge", "TXT", '"<validation-token>"')
```

### Update an existing record

```python
req = models.ModifyRecordRequest()
req.Domain = "example.com"
req.RecordId = 123456789
req.SubDomain = "www"
req.RecordType = "A"
req.RecordLine = "默认"
req.Value = "5.6.7.8"
req.TTL = 600
client.ModifyRecord(req)
```

### Delete a record

```python
# Confirm with the user before running.
req = models.DeleteRecordRequest()
req.Domain = "example.com"
req.RecordId = 123456789
client.DeleteRecord(req)
```

## Record types

| Type | Use For | Example Value |
|---|---|---|
| `A` | IPv4 address | `1.2.3.4` |
| `AAAA` | IPv6 address | `2001:db8::1` |
| `CNAME` | Alias to another hostname | `target.example.com.` |
| `MX` | Mail server | `mail.example.com.` (set `MX=` priority) |
| `TXT` | SPF / DKIM / DMARC / domain verification / ACME | `"v=spf1 ..."` (quoted) |
| `NS` | Delegate subzone | `ns1.example.com.` |
| `SRV` | Service discovery | `0 5 443 api.example.com.` |
| `CAA` | Cert Authority Authorization | `0 issue "letsencrypt.org"` |

## CNAME apex restriction

DNSPod (like every other DNS service) **does not support `CNAME` on the apex `@`** (the bare domain) when other record types exist. Use `A` for the apex; `CNAME` for subdomains. If the upstream is itself a hostname (e.g. an EdgeOne / CDN endpoint), use the `Alias` record type via the EdgeOne console — DNSPod itself doesn't have an `ALIAS` type.

## RecordLine ("线路")

DNSPod can serve different values to different ISPs / regions via `RecordLine`. For 99% of cases pick `"默认"` (Default) — it serves to every resolver. Other common lines: `"电信"`, `"联通"`, `"移动"`, `"境外"`, `"国内"`. Use the console to set up split-horizon DNS; the API just lets you write the records.

## Verifying changes

```bash
dig @119.29.29.29 www.example.com +short    # 119.29.29.29 = DNSPod's recursor
dig www.example.com +trace                  # follow the delegation chain
```

DNSPod propagation is usually under a minute on its own resolver and bounded by the TTL elsewhere. Use `TTL=60` while iterating; raise to `600` once stable.

## Important reminders

- **CNAME values need a trailing dot** to be absolute (`api.example.com.`). Without it, DNSPod won't reject — but resolvers will hate you.
- **Confirm deletes** with the user — there's no undo. The `RecordId` is required, so search first to be sure.
- **Don't rotate `NS` records lightly** — losing nameserver delegation takes the entire domain offline until you fix it.
- **TXT values for SPF/DMARC need to stay under 255 chars per chunk.** For longer policies, split into multiple quoted strings within one TXT value.
- DNSPod has separate quota for free / paid plans on `RecordCount` and `RecordsPerMinute`. Check the console if `LimitExceeded` errors appear.

## Console links

- DNSPod console: <https://console.cloud.tencent.com/cns>
- API reference: <https://www.tencentcloud.com/document/product/1097/40694>

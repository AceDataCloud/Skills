---
name: tencentcloud-cos
description: |
  Manage Tencent Cloud COS (Cloud Object Storage) buckets and objects.
  Use whenever the user asks about COS / 对象存储 / Tencent Cloud bucket
  operations: list buckets, list objects, upload, download, delete,
  pre-signed URLs, calculate bucket size (du), batch delete with prefix,
  copy objects between keys. Backed by the official cos-python-sdk-v5.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [tencentcloud]
---

# Tencent Cloud COS (Object Storage)

Manage Tencent Cloud COS buckets and objects via the official `cos-python-sdk-v5` client.

> **Setup:** See [tencentcloud authentication](../_shared/tencentcloud.md) for SecretId / SecretKey / region setup. The SDK reads `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY` / `TENCENTCLOUD_REGION` from the environment.

## CLI (preferred)

The skill ships [`scripts/cos.py`](scripts/cos.py) — a self-contained CLI that wraps every COS operation below. **Prefer this over hand-rolled SDK calls** when the user's request maps cleanly onto one of its subcommands; it's what the maintained code paths exercise.

```bash
# $SKILL_DIR can point at another skill loaded this turn — anchor on our own
# script (re-run this at the top of every fresh-shell Bash block).
COS="$SKILL_DIR/scripts/cos.py"; [ -f "$COS" ] || COS=$(find /tmp -maxdepth 8 -path '*/skills/*/scripts/cos.py' 2>/dev/null | head -1)
[ -f "$COS" ] || { echo "tencentcloud-cos script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }

python3 $COS buckets                                  # list all buckets
python3 $COS ls mydata-1250000000 --prefix images/    # list objects
python3 $COS upload mydata-1250000000 ./report.pdf --key docs/report-2026.pdf
python3 $COS download mydata-1250000000 docs/report-2026.pdf --output ./out.pdf
python3 $COS url mydata-1250000000 docs/report-2026.pdf --expires 3600
python3 $COS du mydata-1250000000 --prefix logs/
python3 $COS cp mydata-1250000000 old/path.txt new/path.txt
python3 $COS batch-delete mydata-1250000000 --prefix temp/old/ --dry-run
python3 $COS batch-delete mydata-1250000000 --prefix temp/old/   # actually delete
python3 $COS info mydata-1250000000 docs/report-2026.pdf
```

Run `python3 $COS --help` (or `python3 $COS <cmd> --help`) for full flags. Pass `--region <region>` to override per-call.

## When to Use

- List COS buckets across the account
- List objects in a bucket (with prefix / delimiter filtering)
- Upload / download files
- Delete a single object or batch-delete by prefix
- Generate pre-signed download URLs (private bucket sharing)
- Calculate bucket / prefix storage usage
- Copy objects within a bucket

## Dependencies

```bash
pip install cos-python-sdk-v5
```

## Bucket naming

Tencent Cloud bucket names always end in `-<APPID>`, e.g. `mydata-1250000000`. The APPID is the numeric account identifier. The SDK requires the full `name-APPID` form everywhere a bucket is named.

## Quick start

```python
import os
from qcloud_cos import CosConfig, CosS3Client

config = CosConfig(
    Region=os.environ["TENCENTCLOUD_REGION"],
    SecretId=os.environ["TENCENTCLOUD_SECRET_ID"],
    SecretKey=os.environ["TENCENTCLOUD_SECRET_KEY"],
    Scheme="https",
)
client = CosS3Client(config)
```

## Workflows

### List all buckets

```python
resp = client.list_buckets()
for b in resp["Buckets"]["Bucket"]:
    print(b["Name"], b["Location"], b["CreationDate"])
```

### List objects in a bucket

```python
# Single page (max 1000 objects)
resp = client.list_objects(Bucket="mydata-1250000000", Prefix="images/", Delimiter="/")
for obj in resp.get("Contents", []):
    print(obj["Key"], int(obj["Size"]), obj["LastModified"])

# Paginate through everything
marker = ""
while True:
    resp = client.list_objects(Bucket="mydata-1250000000", Prefix="logs/", Marker=marker, MaxKeys=1000)
    for obj in resp.get("Contents", []):
        print(obj["Key"])
    if resp.get("IsTruncated") != "true":
        break
    marker = resp["NextMarker"]
```

### Upload a file

```python
# Streaming upload — handles multipart / resumes / 5GB+ files transparently
client.upload_file(
    Bucket="mydata-1250000000",
    Key="uploads/2026/report.pdf",
    LocalFilePath="./report.pdf",
)
```

### Download a file

```python
client.download_file(
    Bucket="mydata-1250000000",
    Key="uploads/2026/report.pdf",
    DestFilePath="./report.pdf",
)
```

### Generate a pre-signed download URL

```python
# Default expiry 1 hour; pass Expired=86400 for 24h, etc.
url = client.get_presigned_url(
    Method="GET",
    Bucket="mydata-1250000000",
    Key="uploads/2026/report.pdf",
    Expired=3600,
)
print(url)
```

### Delete a single object

```python
client.delete_object(Bucket="mydata-1250000000", Key="uploads/old-file.txt")
```

### Batch delete by prefix (with dry-run safety)

```python
# 1) Always preview first
to_delete = []
marker = ""
while True:
    resp = client.list_objects(Bucket="mydata-1250000000", Prefix="temp/old/", Marker=marker, MaxKeys=1000)
    for obj in resp.get("Contents", []):
        to_delete.append({"Key": obj["Key"]})
    if resp.get("IsTruncated") != "true":
        break
    marker = resp["NextMarker"]

print(f"Would delete {len(to_delete)} objects")
for o in to_delete[:10]:
    print("  -", o["Key"])

# 2) Confirm with the user before running this:
# resp = client.delete_objects(Bucket="mydata-1250000000", Delete={"Object": to_delete, "Quiet": "false"})
# print("Deleted:", len(resp.get("Deleted", [])))
```

### Calculate bucket / prefix size (du)

```python
total_bytes = 0
total_count = 0
marker = ""
while True:
    resp = client.list_objects(Bucket="mydata-1250000000", Prefix="logs/", Marker=marker, MaxKeys=1000)
    for obj in resp.get("Contents", []):
        total_bytes += int(obj["Size"])
        total_count += 1
    if resp.get("IsTruncated") != "true":
        break
    marker = resp["NextMarker"]

print(f"{total_count} objects, {total_bytes / 1024 / 1024:.1f} MiB")
```

### Copy objects within a bucket

```python
client.copy_object(
    Bucket="mydata-1250000000",
    Key="new/path.txt",
    CopySource={
        "Bucket": "mydata-1250000000",
        "Key": "old/path.txt",
        "Region": os.environ["TENCENTCLOUD_REGION"],
    },
)
```

## Safety reminders

- **Confirm batch deletes with the user** before running. The `delete_objects` call is irreversible — there's no recycle bin in COS by default.
- **Pre-signed URLs are bearer tokens** — anyone with the URL gets the object until it expires. Default to short expiries (1 hour) unless the user explicitly asks for longer.
- **Cross-region operations** require the source / destination Region in `CopySource`. Mismatched region triggers `NoSuchBucket`.
- **`download_file` overwrites the destination** without asking. Pick `DestFilePath` carefully when scripting in a loop.

## Error patterns

| Symptom | Likely cause |
|---|---|
| `NoSuchBucket` | Wrong region, wrong APPID suffix on the bucket name |
| `AccessDenied` | Sub-account missing `QcloudCOSReadOnlyAccess` / `QcloudCOSDataReadOnly` etc. |
| `SignatureDoesNotMatch` | SecretKey was pasted with leading / trailing whitespace, or the system clock is off by more than 5 minutes |
| `RequestTimeTooSkewed` | Same — clock skew |

## Console links

- COS console: <https://console.cloud.tencent.com/cos/bucket>
- API reference: <https://www.tencentcloud.com/document/product/436/41330>

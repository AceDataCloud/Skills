#!/usr/bin/env python3
"""
Tencent Cloud COS (Cloud Object Storage) Management Tool

Manage COS buckets: list, upload, download, delete objects, manage buckets.

Usage:
  python3 $SKILL_DIR/scripts/cos.py buckets [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py ls <bucket> [--prefix PREFIX] [--region REGION] [--limit N]
  python3 $SKILL_DIR/scripts/cos.py upload <bucket> <local_path> [--key KEY] [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py download <bucket> <key> [--output PATH] [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py delete <bucket> <key> [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py info <bucket> <key> [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py url <bucket> <key> [--region REGION] [--expires SECONDS]
  python3 $SKILL_DIR/scripts/cos.py du <bucket> [--prefix PREFIX] [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py cp <bucket> <src_key> <dst_key> [--region REGION]
  python3 $SKILL_DIR/scripts/cos.py batch-delete <bucket> --prefix PREFIX [--region REGION] [--dry-run]

Environment:
  Reads TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY from
  sandbox env vars (TENCENTCLOUD_SECRET_ID / SECRET_KEY)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_REGION = os.environ.get("TENCENTCLOUD_REGION", "ap-hongkong")




def get_client(region):
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        print(
            "ERROR: cos-python-sdk-v5 not installed.\n"
            "Run: pip3 install cos-python-sdk-v5",
            file=sys.stderr,
        )
        sys.exit(1)

    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        print(
            "ERROR: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key,
        Scheme="https",
    )
    return CosS3Client(config)


def human_size(num_bytes):
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def cmd_buckets(args):
    """List all buckets."""
    client = get_client(args.region)
    resp = client.list_buckets()
    buckets = resp.get("Buckets", {}).get("Bucket", [])

    if not buckets:
        print("No buckets found.")
        return

    print(f"Found {len(buckets)} bucket(s):\n")
    for b in buckets:
        name = b.get("Name", "N/A")
        location = b.get("Location", "N/A")
        created = b.get("CreationDate", "N/A")
        print(f"  {name:50s} {location:20s} Created: {created}")


def cmd_ls(args):
    """List objects in a bucket."""
    client = get_client(args.region)

    params = {
        "Bucket": args.bucket,
        "MaxKeys": args.limit,
    }
    if args.prefix:
        params["Prefix"] = args.prefix
    if args.delimiter:
        params["Delimiter"] = args.delimiter

    resp = client.list_objects(**params)

    # Common prefixes (directories)
    prefixes = resp.get("CommonPrefixes", [])
    if prefixes:
        for p in prefixes:
            prefix = p.get("Prefix", "")
            print(f"  DIR  {prefix}")

    # Objects
    contents = resp.get("Contents", [])
    if not contents and not prefixes:
        print("No objects found.")
        return

    total_size = 0
    for obj in contents:
        key = obj.get("Key", "")
        size = int(obj.get("Size", 0))
        modified = obj.get("LastModified", "N/A")
        total_size += size
        print(f"  {human_size(size):>10s}  {modified:25s}  {key}")

    truncated = resp.get("IsTruncated", "false")
    print(f"\n  {len(contents)} object(s), total: {human_size(total_size)}"
          f"{' (truncated, use --limit to see more)' if truncated == 'true' else ''}")


def cmd_upload(args):
    """Upload a file to COS."""
    client = get_client(args.region)
    local_path = Path(args.local_path)

    if not local_path.exists():
        print(f"ERROR: File not found: {local_path}", file=sys.stderr)
        sys.exit(1)

    key = args.key or local_path.name

    print(f"Uploading {local_path} → {args.bucket}/{key} ...")
    resp = client.upload_file(
        Bucket=args.bucket,
        Key=key,
        LocalFilePath=str(local_path),
    )

    etag = resp.get("ETag", "N/A")
    url = f"https://{args.bucket}.cos.{args.region}.myqcloud.com/{key}"
    print(f"  ETag: {etag}")
    print(f"  URL:  {url}")


def cmd_download(args):
    """Download an object from COS."""
    client = get_client(args.region)

    output = args.output or Path(args.key).name
    print(f"Downloading {args.bucket}/{args.key} → {output} ...")

    resp = client.download_file(
        Bucket=args.bucket,
        Key=args.key,
        DestFilePath=output,
    )
    print(f"  Downloaded to: {output}")


def cmd_delete(args):
    """Delete an object from COS."""
    client = get_client(args.region)

    print(f"Deleting {args.bucket}/{args.key} ...")
    client.delete_object(
        Bucket=args.bucket,
        Key=args.key,
    )
    print("  Deleted.")


def cmd_info(args):
    """Get object metadata (head object)."""
    client = get_client(args.region)

    resp = client.head_object(
        Bucket=args.bucket,
        Key=args.key,
    )

    print(f"Object info for {args.bucket}/{args.key}:\n")
    for k, v in resp.items():
        if k.startswith("x-cos-") or k in ("Content-Length", "Content-Type", "ETag", "Last-Modified"):
            print(f"  {k}: {v}")


def cmd_url(args):
    """Generate a pre-signed URL."""
    client = get_client(args.region)

    url = client.get_presigned_url(
        Method="GET",
        Bucket=args.bucket,
        Key=args.key,
        Expired=args.expires,
    )
    print(url)


def cmd_du(args):
    """Calculate total size of objects with a given prefix."""
    client = get_client(args.region)

    total_size = 0
    total_count = 0
    marker = ""

    while True:
        params = {
            "Bucket": args.bucket,
            "MaxKeys": 1000,
            "Marker": marker,
        }
        if args.prefix:
            params["Prefix"] = args.prefix

        resp = client.list_objects(**params)
        contents = resp.get("Contents", [])

        for obj in contents:
            total_size += int(obj.get("Size", 0))
            total_count += 1

        if resp.get("IsTruncated") == "true":
            marker = resp.get("NextMarker", "")
            if not marker and contents:
                marker = contents[-1].get("Key", "")
        else:
            break

    prefix_str = args.prefix or "(all)"
    print(f"Bucket: {args.bucket}")
    print(f"Prefix: {prefix_str}")
    print(f"Objects: {total_count}")
    print(f"Total size: {human_size(total_size)}")


def cmd_cp(args):
    """Copy an object within the same bucket."""
    client = get_client(args.region)

    source = {
        "Bucket": args.bucket,
        "Key": args.src_key,
        "Region": args.region,
    }

    print(f"Copying {args.src_key} → {args.dst_key} in {args.bucket} ...")
    client.copy_object(
        Bucket=args.bucket,
        Key=args.dst_key,
        CopySource=source,
    )
    print("  Copied.")


def cmd_batch_delete(args):
    """Delete all objects with a given prefix (with confirmation)."""
    client = get_client(args.region)

    # Collect all keys
    keys = []
    marker = ""
    while True:
        resp = client.list_objects(
            Bucket=args.bucket,
            Prefix=args.prefix,
            MaxKeys=1000,
            Marker=marker,
        )
        contents = resp.get("Contents", [])
        keys.extend([obj["Key"] for obj in contents])

        if resp.get("IsTruncated") == "true":
            marker = resp.get("NextMarker", "")
            if not marker and contents:
                marker = contents[-1].get("Key", "")
        else:
            break

    if not keys:
        print("No objects found with the given prefix.")
        return

    total_size = sum(int(obj.get("Size", 0)) for obj in contents)
    print(f"Found {len(keys)} object(s) with prefix '{args.prefix}'")

    if args.dry_run:
        print("DRY RUN — would delete:")
        for k in keys[:20]:
            print(f"  {k}")
        if len(keys) > 20:
            print(f"  ... and {len(keys) - 20} more")
        return

    # Ask for confirmation
    confirm = input(f"Delete {len(keys)} objects? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    # Delete in batches of 1000
    for i in range(0, len(keys), 1000):
        batch = keys[i:i + 1000]
        delete_objects = {"Object": [{"Key": k} for k in batch]}
        client.delete_objects(Bucket=args.bucket, Delete=delete_objects)
        print(f"  Deleted batch {i // 1000 + 1} ({len(batch)} objects)")

    print(f"  Total deleted: {len(keys)} objects")


def main():
    parser = argparse.ArgumentParser(
        description="Tencent Cloud COS Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--region", "-r", default=DEFAULT_REGION,
                        help=f"Region (default: {DEFAULT_REGION})")
    sub = parser.add_subparsers(dest="command", required=True)

    # buckets
    sub.add_parser("buckets", help="List all buckets")

    # ls
    p = sub.add_parser("ls", help="List objects in a bucket")
    p.add_argument("bucket", help="Bucket name (e.g. mybucket-1250000000)")
    p.add_argument("--prefix", "-p", help="Key prefix filter")
    p.add_argument("--delimiter", "-d", help="Delimiter for directory-like listing (use '/')")
    p.add_argument("--limit", "-l", type=int, default=100, help="Max objects to list (default: 100)")

    # upload
    p = sub.add_parser("upload", help="Upload a file")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("local_path", help="Local file path")
    p.add_argument("--key", "-k", help="Object key (default: filename)")

    # download
    p = sub.add_parser("download", help="Download an object")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("key", help="Object key")
    p.add_argument("--output", "-o", help="Output file path (default: object filename)")

    # delete
    p = sub.add_parser("delete", help="Delete an object")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("key", help="Object key")

    # info
    p = sub.add_parser("info", help="Get object metadata")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("key", help="Object key")

    # url
    p = sub.add_parser("url", help="Generate a pre-signed URL")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("key", help="Object key")
    p.add_argument("--expires", "-e", type=int, default=3600, help="URL expiry in seconds (default: 3600)")

    # du
    p = sub.add_parser("du", help="Calculate total size of objects")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("--prefix", "-p", help="Key prefix")

    # cp
    p = sub.add_parser("cp", help="Copy an object within the same bucket")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("src_key", help="Source object key")
    p.add_argument("dst_key", help="Destination object key")

    # batch-delete
    p = sub.add_parser("batch-delete", help="Delete all objects with a prefix")
    p.add_argument("bucket", help="Bucket name")
    p.add_argument("--prefix", required=True, help="Key prefix for objects to delete")
    p.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")

    args = parser.parse_args()

    commands = {
        "buckets": cmd_buckets,
        "ls": cmd_ls,
        "upload": cmd_upload,
        "download": cmd_download,
        "delete": cmd_delete,
        "info": cmd_info,
        "url": cmd_url,
        "du": cmd_du,
        "cp": cmd_cp,
        "batch-delete": cmd_batch_delete,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()

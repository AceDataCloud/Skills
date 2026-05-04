#!/usr/bin/env python3
"""
DNSPod (Tencent Cloud DNS) — record management CLI.

Uses the v3 DNSPod API via tencentcloud-sdk-python — same TENCENTCLOUD_*
credentials as every other tencentcloud-* skill.

Quick examples:
  python3 $SKILL_DIR/scripts/dns.py domains
  python3 $SKILL_DIR/scripts/dns.py list example.com
  python3 $SKILL_DIR/scripts/dns.py list example.com --type CNAME
  python3 $SKILL_DIR/scripts/dns.py search example.com --keyword api
  python3 $SKILL_DIR/scripts/dns.py create example.com --sub www --type A --value 1.2.3.4
  python3 $SKILL_DIR/scripts/dns.py update example.com <record_id> --sub www --type A --value 5.6.7.8
  python3 $SKILL_DIR/scripts/dns.py delete example.com <record_id>

Environment:
  TENCENTCLOUD_SECRET_ID   — required
  TENCENTCLOUD_SECRET_KEY  — required
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def get_client():
    try:
        from tencentcloud.common import credential
        from tencentcloud.dnspod.v20210323 import dnspod_client
    except ImportError:
        print(
            "ERROR: tencentcloud-sdk-python not installed.\nRun: pip3 install tencentcloud-sdk-python",
            file=sys.stderr,
        )
        sys.exit(1)
    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        print(
            "ERROR: TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set in env",
            file=sys.stderr,
        )
        sys.exit(1)
    cred = credential.Credential(secret_id, secret_key)
    # DNSPod is global — region is ignored, pass empty string.
    return dnspod_client.DnspodClient(cred, "")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_domains(args):
    from tencentcloud.dnspod.v20210323 import models

    client = get_client()
    req = models.DescribeDomainListRequest()
    req.Limit = 100
    resp = client.DescribeDomainList(req)
    rows = [
        {
            "DomainId": d.DomainId,
            "Name": d.Name,
            "Status": d.Status,
            "RecordCount": d.RecordCount,
        }
        for d in (resp.DomainList or [])
    ]
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print(f"{'Name':30s}  {'Status':10s}  {'#Records':8s}  DomainId")
        for r in rows:
            print(f"{r['Name']:30s}  {r['Status']:10s}  {r['RecordCount']:>8d}  {r['DomainId']}")


def cmd_list(args):
    from tencentcloud.dnspod.v20210323 import models

    client = get_client()
    req = models.DescribeRecordListRequest()
    req.Domain = args.domain
    req.Limit = args.limit
    if args.type:
        req.RecordType = args.type
    if args.sub:
        req.Subdomain = args.sub
    resp = client.DescribeRecordList(req)
    _print_records(resp.RecordList or [], args.format)


def cmd_search(args):
    """List + client-side keyword filter (DNSPod has no server-side text search)."""
    from tencentcloud.dnspod.v20210323 import models

    client = get_client()
    req = models.DescribeRecordListRequest()
    req.Domain = args.domain
    req.Limit = 3000
    resp = client.DescribeRecordList(req)
    keyword = args.keyword.lower()
    matches = [
        r
        for r in (resp.RecordList or [])
        if keyword in (r.Name or "").lower() or keyword in (r.Value or "").lower()
    ]
    _print_records(matches, args.format)


def _print_records(records, fmt):
    rows = [
        {
            "RecordId": r.RecordId,
            "Name": r.Name,
            "Type": r.Type,
            "Value": r.Value,
            "TTL": r.TTL,
            "Line": r.Line,
            "MX": getattr(r, "MX", None),
        }
        for r in records
    ]
    if fmt == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    print(f"{'RecordId':12s}  {'Name':22s}  {'Type':6s}  {'TTL':5s}  Value")
    for r in rows:
        print(f"{str(r['RecordId']):12s}  {r['Name']:22s}  {r['Type']:6s}  {str(r['TTL']):5s}  {r['Value']}")


def cmd_create(args):
    from tencentcloud.dnspod.v20210323 import models

    client = get_client()
    req = models.CreateRecordRequest()
    req.Domain = args.domain
    req.SubDomain = args.sub
    req.RecordType = args.type
    req.RecordLine = args.line
    req.Value = args.value
    req.TTL = args.ttl
    if args.mx is not None:
        req.MX = args.mx
    resp = client.CreateRecord(req)
    print(f"Created RecordId={resp.RecordId}")


def cmd_update(args):
    from tencentcloud.dnspod.v20210323 import models

    client = get_client()
    req = models.ModifyRecordRequest()
    req.Domain = args.domain
    req.RecordId = int(args.record_id)
    req.SubDomain = args.sub
    req.RecordType = args.type
    req.RecordLine = args.line
    req.Value = args.value
    req.TTL = args.ttl
    if args.mx is not None:
        req.MX = args.mx
    client.ModifyRecord(req)
    print(f"Updated RecordId={args.record_id}")


def cmd_delete(args):
    from tencentcloud.dnspod.v20210323 import models

    if not args.yes:
        print(f"DRY RUN: would delete RecordId={args.record_id} on {args.domain}. Pass --yes to actually delete.")
        return
    client = get_client()
    req = models.DeleteRecordRequest()
    req.Domain = args.domain
    req.RecordId = int(args.record_id)
    client.DeleteRecord(req)
    print(f"Deleted RecordId={args.record_id}")


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tencent Cloud DNSPod record management.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("domains", help="List domains")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_domains)

    p = sub.add_parser("list", help="List records on a domain")
    p.add_argument("domain")
    p.add_argument("--type", help="Filter by record type (A, AAAA, CNAME, MX, TXT, …)")
    p.add_argument("--sub", help="Filter by exact subdomain")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("search", help="Search records by keyword (matches Name or Value)")
    p.add_argument("domain")
    p.add_argument("--keyword", required=True)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("create", help="Create a record")
    p.add_argument("domain")
    p.add_argument("--sub", required=True, help="Subdomain (use @ for apex)")
    p.add_argument("--type", required=True, help="A / AAAA / CNAME / MX / TXT / NS / SRV / CAA")
    p.add_argument("--value", required=True)
    p.add_argument("--line", default="默认", help='RecordLine (default "默认")')
    p.add_argument("--ttl", type=int, default=600)
    p.add_argument("--mx", type=int, help="MX priority (only for type=MX)")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("update", help="Modify an existing record")
    p.add_argument("domain")
    p.add_argument("record_id")
    p.add_argument("--sub", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--line", default="默认")
    p.add_argument("--ttl", type=int, default=600)
    p.add_argument("--mx", type=int)
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete", help="Delete a record (requires --yes)")
    p.add_argument("domain")
    p.add_argument("record_id")
    p.add_argument("--yes", action="store_true", help="Confirm destructive operation")
    p.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())

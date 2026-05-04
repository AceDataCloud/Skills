#!/usr/bin/env python3
"""
Tencent Cloud EdgeOne (EO) Management Tool

Manage EdgeOne CDN/security: zones, cache purge, prefetch, DNS records, security rules.

Usage:
  python3 $SKILL_DIR/scripts/edgeone.py zones
  python3 $SKILL_DIR/scripts/edgeone.py zone <zone_id>
  python3 $SKILL_DIR/scripts/edgeone.py domains <zone_id>
  python3 $SKILL_DIR/scripts/edgeone.py purge <zone_id> --urls URL1 [URL2 ...]
  python3 $SKILL_DIR/scripts/edgeone.py purge <zone_id> --prefixes PREFIX1 [PREFIX2 ...]
  python3 $SKILL_DIR/scripts/edgeone.py purge <zone_id> --hosts HOST1 [HOST2 ...]
  python3 $SKILL_DIR/scripts/edgeone.py purge <zone_id> --all
  python3 $SKILL_DIR/scripts/edgeone.py prefetch <zone_id> --urls URL1 [URL2 ...]
  python3 $SKILL_DIR/scripts/edgeone.py purge-tasks <zone_id> [--status STATUS]
  python3 $SKILL_DIR/scripts/edgeone.py prefetch-tasks <zone_id> [--status STATUS]
  python3 $SKILL_DIR/scripts/edgeone.py dns <zone_id> [--name NAME] [--type TYPE]
  python3 $SKILL_DIR/scripts/edgeone.py dns-create <zone_id> --name NAME --type TYPE --content CONTENT [--ttl TTL]
  python3 $SKILL_DIR/scripts/edgeone.py dns-delete <zone_id> <record_id>
  python3 $SKILL_DIR/scripts/edgeone.py security <zone_id>
  python3 $SKILL_DIR/scripts/edgeone.py waf <zone_id>

Environment:
  Reads TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY from
  sandbox env vars (TENCENTCLOUD_SECRET_ID / SECRET_KEY)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path





def get_client():
    try:
        from tencentcloud.common import credential
        from tencentcloud.teo.v20220901 import teo_client
    except ImportError:
        print(
            "ERROR: tencentcloud-sdk-python not installed.\n"
            "Run: pip3 install tencentcloud-sdk-python",
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

    cred = credential.Credential(secret_id, secret_key)
    return teo_client.TeoClient(cred, "")


def pp(data):
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def cmd_zones(args):
    """List all EdgeOne zones."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribeZonesRequest()
    req.Limit = 100
    resp = client.DescribeZones(req)
    data = json.loads(resp.to_json_string())

    zones = data.get("Zones", [])
    if not zones:
        print("No zones found.")
        return

    print(f"Found {data.get('TotalCount', len(zones))} zone(s):\n")
    for z in zones:
        status = z.get("Status", "Unknown")
        plan = z.get("PlanType", "N/A")
        emoji = "●" if status == "active" else "○"
        print(f"  {emoji} {z.get('ZoneId', 'N/A'):25s} {z.get('ZoneName', 'N/A'):30s} "
              f"{status:12s} Plan: {plan}")


def cmd_zone(args):
    """Get zone details."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribeZonesRequest()
    req.Filters = [{"Name": "zone-id", "Values": [args.zone_id]}]
    resp = client.DescribeZones(req)
    data = json.loads(resp.to_json_string())

    zones = data.get("Zones", [])
    if not zones:
        print(f"Zone {args.zone_id} not found.")
        return

    pp(zones[0])


def cmd_domains(args):
    """List acceleration domains for a zone."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribeAccelerationDomainsRequest()
    req.ZoneId = args.zone_id
    req.Limit = 100
    resp = client.DescribeAccelerationDomains(req)
    data = json.loads(resp.to_json_string())

    domains = data.get("AccelerationDomains", [])
    if not domains:
        print("No domains found.")
        return

    print(f"Found {data.get('TotalCount', len(domains))} domain(s):\n")
    for d in domains:
        status = d.get("DomainStatus", "Unknown")
        cname = d.get("Cname", "N/A")
        emoji = "●" if status == "online" else "○"
        print(f"  {emoji} {d.get('DomainName', 'N/A'):40s} {status:12s} CNAME: {cname}")


def cmd_purge(args):
    """Create a cache purge task."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.CreatePurgeTaskRequest()
    req.ZoneId = args.zone_id

    if args.urls:
        req.Type = "purge_url"
        req.Targets = args.urls
        print(f"Purging {len(args.urls)} URL(s)...")
    elif args.prefixes:
        req.Type = "purge_prefix"
        req.Targets = args.prefixes
        print(f"Purging {len(args.prefixes)} prefix(es)...")
    elif args.hosts:
        req.Type = "purge_host"
        req.Targets = args.hosts
        print(f"Purging {len(args.hosts)} host(s)...")
    elif args.all:
        req.Type = "purge_all"
        req.Targets = []
        print("Purging ALL cache...")
    else:
        print("ERROR: Specify --urls, --prefixes, --hosts, or --all", file=sys.stderr)
        sys.exit(1)

    resp = client.CreatePurgeTask(req)
    data = json.loads(resp.to_json_string())
    task_id = data.get("TaskId", "N/A")
    print(f"  Purge task created: {task_id}")


def cmd_prefetch(args):
    """Create a prefetch (pre-warm) task."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.CreatePrefetchTaskRequest()
    req.ZoneId = args.zone_id
    req.Targets = args.urls

    print(f"Prefetching {len(args.urls)} URL(s)...")
    resp = client.CreatePrefetchTask(req)
    data = json.loads(resp.to_json_string())
    task_id = data.get("TaskId", "N/A")
    print(f"  Prefetch task created: {task_id}")


def cmd_purge_tasks(args):
    """List purge tasks."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribePurgeTasksRequest()
    req.ZoneId = args.zone_id
    req.Limit = 20

    if args.status:
        req.Filters = [{"Name": "status", "Values": [args.status]}]

    resp = client.DescribePurgeTasks(req)
    data = json.loads(resp.to_json_string())

    tasks = data.get("Tasks", [])
    if not tasks:
        print("No purge tasks found.")
        return

    print(f"Found {data.get('TotalCount', len(tasks))} task(s):\n")
    for t in tasks:
        status = t.get("Status", "Unknown")
        emoji = "✓" if status == "complete" else "…" if status == "processing" else "✗"
        print(f"  {emoji} {t.get('TaskId', 'N/A'):40s} {t.get('Type', 'N/A'):15s} "
              f"{status:12s} {t.get('CreatedOn', 'N/A')}")
        target = t.get("Target", "")
        if target:
            print(f"    Target: {target}")


def cmd_prefetch_tasks(args):
    """List prefetch tasks."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribePrefetchTasksRequest()
    req.ZoneId = args.zone_id
    req.Limit = 20

    if args.status:
        req.Filters = [{"Name": "status", "Values": [args.status]}]

    resp = client.DescribePrefetchTasks(req)
    data = json.loads(resp.to_json_string())

    tasks = data.get("Tasks", [])
    if not tasks:
        print("No prefetch tasks found.")
        return

    print(f"Found {data.get('TotalCount', len(tasks))} task(s):\n")
    for t in tasks:
        status = t.get("Status", "Unknown")
        emoji = "✓" if status == "complete" else "…" if status == "processing" else "✗"
        print(f"  {emoji} {t.get('TaskId', 'N/A'):40s} {status:12s} {t.get('CreatedOn', 'N/A')}")
        target = t.get("Target", "")
        if target:
            print(f"    Target: {target}")


def cmd_dns(args):
    """List DNS records for a zone."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribeDnsRecordsRequest()
    req.ZoneId = args.zone_id
    req.Limit = 100

    filters = []
    if args.name:
        filters.append({"Name": "name", "Values": [args.name]})
    if args.type:
        filters.append({"Name": "type", "Values": [args.type]})
    if filters:
        req.Filters = filters

    resp = client.DescribeDnsRecords(req)
    data = json.loads(resp.to_json_string())

    records = data.get("DnsRecords", [])
    if not records:
        print("No DNS records found.")
        return

    print(f"Found {data.get('TotalCount', len(records))} record(s):\n")
    for r in records:
        print(f"  {r.get('RecordId', 'N/A'):15s} {r.get('Type', 'N/A'):8s} "
              f"{r.get('Name', 'N/A'):40s} → {r.get('Content', 'N/A'):40s} "
              f"TTL: {r.get('TTL', 'N/A')}")


def cmd_dns_create(args):
    """Create a DNS record."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.CreateDnsRecordRequest()
    req.ZoneId = args.zone_id
    req.Type = args.type
    req.Name = args.name
    req.Content = args.content
    req.TTL = args.ttl

    print(f"Creating {args.type} record: {args.name} → {args.content} ...")
    resp = client.CreateDnsRecord(req)
    data = json.loads(resp.to_json_string())
    record_id = data.get("RecordId", "N/A")
    print(f"  Created record: {record_id}")


def cmd_dns_delete(args):
    """Delete a DNS record."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DeleteDnsRecordsRequest()
    req.ZoneId = args.zone_id
    req.RecordIds = [args.record_id]

    print(f"Deleting DNS record {args.record_id} ...")
    client.DeleteDnsRecords(req)
    print("  Deleted.")


def cmd_security(args):
    """Get zone security configuration."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    req = models.DescribeSecurityIPGroupInfoRequest()
    req.ZoneId = args.zone_id

    resp = client.DescribeSecurityIPGroupInfo(req)
    data = json.loads(resp.to_json_string())
    pp(data)


def cmd_waf(args):
    """Get WAF configuration."""
    from tencentcloud.teo.v20220901 import models

    client = get_client()
    # Retrieve the zone settings which include security features
    req = models.DescribeZoneSettingRequest()
    req.ZoneId = args.zone_id

    resp = client.DescribeZoneSetting(req)
    data = json.loads(resp.to_json_string())

    zone_setting = data.get("ZoneSetting", {})
    # Extract security-related settings
    security_fields = {}
    for key in ("WebSocket", "Cache", "CacheKey", "PostMaxSize", "Quic",
                "ClientIpHeader", "CachePrefresh", "Ipv6", "Https", "Grpc"):
        if key in zone_setting:
            security_fields[key] = zone_setting[key]

    pp(security_fields)


def main():
    parser = argparse.ArgumentParser(
        description="Tencent Cloud EdgeOne Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # zones
    sub.add_parser("zones", help="List all zones")

    # zone
    p = sub.add_parser("zone", help="Get zone details")
    p.add_argument("zone_id")

    # domains
    p = sub.add_parser("domains", help="List acceleration domains")
    p.add_argument("zone_id")

    # purge
    p = sub.add_parser("purge", help="Create cache purge task")
    p.add_argument("zone_id")
    purge_group = p.add_mutually_exclusive_group(required=True)
    purge_group.add_argument("--urls", nargs="+", help="URLs to purge")
    purge_group.add_argument("--prefixes", nargs="+", help="URL prefixes to purge")
    purge_group.add_argument("--hosts", nargs="+", help="Hostnames to purge")
    purge_group.add_argument("--all", action="store_true", help="Purge all cache")

    # prefetch
    p = sub.add_parser("prefetch", help="Create prefetch/pre-warm task")
    p.add_argument("zone_id")
    p.add_argument("--urls", nargs="+", required=True, help="URLs to prefetch")

    # purge-tasks
    p = sub.add_parser("purge-tasks", help="List purge tasks")
    p.add_argument("zone_id")
    p.add_argument("--status", help="Filter by status (processing/complete/failed)")

    # prefetch-tasks
    p = sub.add_parser("prefetch-tasks", help="List prefetch tasks")
    p.add_argument("zone_id")
    p.add_argument("--status", help="Filter by status")

    # dns
    p = sub.add_parser("dns", help="List DNS records")
    p.add_argument("zone_id")
    p.add_argument("--name", help="Filter by record name")
    p.add_argument("--type", help="Filter by type (A/CNAME/TXT/MX)")

    # dns-create
    p = sub.add_parser("dns-create", help="Create DNS record")
    p.add_argument("zone_id")
    p.add_argument("--name", required=True, help="Record name")
    p.add_argument("--type", required=True, help="Record type (A/CNAME/TXT/MX)")
    p.add_argument("--content", required=True, help="Record content/value")
    p.add_argument("--ttl", type=int, default=300, help="TTL in seconds (default: 300)")

    # dns-delete
    p = sub.add_parser("dns-delete", help="Delete DNS record")
    p.add_argument("zone_id")
    p.add_argument("record_id")

    # security
    p = sub.add_parser("security", help="Get security IP group info")
    p.add_argument("zone_id")

    # waf
    p = sub.add_parser("waf", help="Get zone security/WAF settings")
    p.add_argument("zone_id")

    args = parser.parse_args()

    commands = {
        "zones": cmd_zones,
        "zone": cmd_zone,
        "domains": cmd_domains,
        "purge": cmd_purge,
        "prefetch": cmd_prefetch,
        "purge-tasks": cmd_purge_tasks,
        "prefetch-tasks": cmd_prefetch_tasks,
        "dns": cmd_dns,
        "dns-create": cmd_dns_create,
        "dns-delete": cmd_dns_delete,
        "security": cmd_security,
        "waf": cmd_waf,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()

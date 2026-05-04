#!/usr/bin/env python3
"""
Tencent Cloud CLS (Cloud Log Service) — search & analytics CLI.

Search log topics with CQL filters or run SQL analytics over them.

Quick examples:
  python3 $SKILL_DIR/scripts/cls.py topics
  python3 $SKILL_DIR/scripts/cls.py search --topic <topic-id> --query 'level:ERROR' --time 1h
  python3 $SKILL_DIR/scripts/cls.py search --topic <topic-id> --trace-id <uuid>
  python3 $SKILL_DIR/scripts/cls.py search --topic <topic-id> \\
      --query '* | SELECT api_name, count(*) AS cnt GROUP BY api_name ORDER BY cnt DESC LIMIT 20' \\
      --time 1d

Environment:
  TENCENTCLOUD_SECRET_ID   — required
  TENCENTCLOUD_SECRET_KEY  — required
  TENCENTCLOUD_REGION      — optional, default ap-hongkong
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

DEFAULT_REGION = os.environ.get("TENCENTCLOUD_REGION", "ap-hongkong")


def get_client(region: str = DEFAULT_REGION):
    try:
        from tencentcloud.cls.v20201016 import cls_client
        from tencentcloud.common import credential
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
    return cls_client.ClsClient(cred, region)


# ---------------------------------------------------------------------------
# Time parsing — accepts `30m`, `1h`, `6h`, `1d`, `7d`.
# ---------------------------------------------------------------------------

_TIME_RE = re.compile(r"^(\d+)([smhd])$")


def parse_relative(spec: str) -> int:
    """Return milliseconds for a string like `1h` / `30m` / `7d`."""
    m = _TIME_RE.match(spec)
    if not m:
        raise ValueError(f"bad --time: {spec!r}; use e.g. 30m, 1h, 6h, 1d, 7d")
    n, unit = int(m.group(1)), m.group(2)
    return n * {"s": 1000, "m": 60_000, "h": 3_600_000, "d": 86_400_000}[unit]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_topics(args):
    """List all log topics in the region."""
    from tencentcloud.cls.v20201016 import models

    client = get_client(args.region)
    req = models.DescribeTopicsRequest()
    if args.logset_id:
        req.Filters = [{"Key": "logsetId", "Values": [args.logset_id]}]
    resp = client.DescribeTopics(req)
    if args.format == "json":
        print(json.dumps([t._serialize() for t in (resp.Topics or [])], indent=2, ensure_ascii=False))
        return
    print(f"{'TopicId':40s}  {'TopicName':32s}  {'LogsetId'}")
    for t in resp.Topics or []:
        print(f"{t.TopicId:40s}  {(t.TopicName or '')[:32]:32s}  {t.LogsetId}")


def cmd_search(args):
    """Search a topic with a CQL / SQL query."""
    from tencentcloud.cls.v20201016 import models

    client = get_client(args.region)
    req = models.SearchLogRequest()
    req.TopicId = args.topic
    now_ms = int(time.time() * 1000)
    req.From = now_ms - parse_relative(args.time)
    req.To = now_ms

    if args.trace_id:
        query = f'trace_id:"{args.trace_id}"'
    else:
        query = args.query
    req.Query = query
    req.Limit = args.limit
    req.Sort = args.sort
    req.SyntaxRule = 0 if args.lucene else 1

    resp = client.SearchLog(req)

    # Analytics queries (have a `|`) land in AnalysisResults.
    if "|" in query and (resp.AnalysisResults or []):
        rows = []
        for row in resp.AnalysisResults or []:
            rows.append({c.Name: c.Value for c in row.Data})
        if args.format == "json":
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for r in rows:
                print(json.dumps(r, ensure_ascii=False))
        return

    out = []
    for line in resp.Results or []:
        try:
            fields = json.loads(line.LogJson) if line.LogJson else {}
        except Exception:
            fields = {"_raw": line.LogJson}
        out.append({"time_ms": line.Time, "fields": fields})
    if args.format == "json":
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for entry in out:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["time_ms"] / 1000))
            f = entry["fields"]
            short = " ".join(f"{k}={v}" for k, v in list(f.items())[:6])
            print(f"{ts}  {short}")
    if resp.Context:
        print(f"\n# more results: --context {resp.Context}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search Tencent Cloud CLS log topics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"Tencent Cloud region (default: {DEFAULT_REGION})",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_topics = sub.add_parser("topics", help="List log topics")
    p_topics.add_argument("--logset-id", help="Filter to one logset")
    p_topics.add_argument("--format", choices=["text", "json"], default="text")
    p_topics.set_defaults(func=cmd_topics)

    p_search = sub.add_parser("search", help="Search a topic")
    p_search.add_argument("--topic", required=True, help="TopicId (UUID)")
    g = p_search.add_mutually_exclusive_group(required=True)
    g.add_argument("--query", "-q", help="CQL or SQL query (use `|` for SQL analytics)")
    g.add_argument("--trace-id", help="Shortcut for trace_id:\"<id>\"")
    p_search.add_argument("--time", default="1h", help="Time range (30m, 1h, 6h, 1d, 7d). Default 1h.")
    p_search.add_argument("--limit", type=int, default=100, help="Max results (default 100)")
    p_search.add_argument("--sort", choices=["asc", "desc"], default="desc")
    p_search.add_argument("--lucene", action="store_true", help="Treat --query as Lucene (default CQL)")
    p_search.add_argument("--format", choices=["text", "json"], default="text")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())

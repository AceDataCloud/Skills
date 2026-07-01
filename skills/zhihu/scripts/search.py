#!/usr/bin/env python3
"""
zhihu search — search Zhihu and the web via the Zhihu Developer Platform API.
Standard-library only (urllib), no third-party deps.

Auth: Bearer token via ``ZHIHU_DEVELOPER_TOKEN`` env var.
Does NOT require login cookies — independent of blog.py.

Endpoints:
  zhihu_search  — search Zhihu content (questions/answers/articles)
  global_search — search the entire web with optional filters
  hot_list      — current Zhihu trending topics

Quick examples:
  python3 $SKILL_DIR/scripts/search.py search "Python 爬虫"
  python3 $SKILL_DIR/scripts/search.py search "Python 爬虫" --count 5
  python3 $SKILL_DIR/scripts/search.py global "AI Agent" --count 10
  python3 $SKILL_DIR/scripts/search.py global "React" --filter 'host=="github.com"'
  python3 $SKILL_DIR/scripts/search.py global "新闻" --db realtime
  python3 $SKILL_DIR/scripts/search.py hot
  python3 $SKILL_DIR/scripts/search.py hot --limit 10
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://developer.zhihu.com/api/v1/content"


def out(obj) -> None:
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def die(msg: str, code: int = 1) -> None:
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def get_token() -> str:
    token = os.environ.get("ZHIHU_DEVELOPER_TOKEN", "").strip()
    if not token:
        die(
            "ZHIHU_DEVELOPER_TOKEN not set. "
            "Set this env var to your Zhihu Developer Platform access secret."
        )
    return token


def api_get(endpoint: str, params: dict | None = None) -> dict:
    """GET request to the Zhihu Developer Platform API."""
    token = get_token()
    url = f"{BASE_URL}/{endpoint}"
    if params:
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        if params:
            url += "?" + urllib.parse.urlencode(params)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Request-Timestamp": str(int(time.time())),
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        die(f"HTTP {e.code}: {body[:500]}")
    except urllib.error.URLError as e:
        die(f"Network error: {e.reason}")
    return {}


def _fmt_zhihu_item(item: dict) -> dict:
    """Format a zhihu_search result item for display."""
    return {
        "title": item.get("Title", ""),
        "type": item.get("ContentType", ""),
        "content_id": item.get("ContentID", ""),
        "url": item.get("Url", ""),
        "excerpt": item.get("ContentText", "")[:200],
        "vote_up": item.get("VoteUpCount", 0),
        "comments": item.get("CommentCount", 0),
        "author": item.get("AuthorName", ""),
        "authority": item.get("AuthorityLevel", ""),
        "edit_time": item.get("EditTime", 0),
    }


def _fmt_global_item(item: dict) -> dict:
    """Format a global_search result item for display."""
    return {
        "title": item.get("Title", ""),
        "type": item.get("ContentType", ""),
        "content_id": item.get("ContentID", ""),
        "url": item.get("Url", ""),
        "excerpt": item.get("ContentText", "")[:300],
        "vote_up": item.get("VoteUpCount", 0),
        "comments": item.get("CommentCount", 0),
        "author": item.get("AuthorName", ""),
        "authority": item.get("AuthorityLevel", ""),
        "edit_time": item.get("EditTime", 0),
    }


def _fmt_hot_item(item: dict, rank: int) -> dict:
    """Format a hot_list result item for display."""
    return {
        "rank": rank,
        "title": item.get("Title", ""),
        "url": item.get("Url", ""),
        "summary": item.get("Summary", ""),
        "thumbnail": item.get("ThumbnailUrl", ""),
    }


def cmd_search(args):
    """Search Zhihu content (站内搜索)."""
    params = {"Query": args.query, "Count": args.count}
    resp = api_get("zhihu_search", params)

    if resp.get("Code") != 0:
        die(f"API error: Code={resp.get('Code')} Message={resp.get('Message')}")

    data = resp.get("Data", {})
    items = data.get("Items") or []

    result = {
        "query": args.query,
        "count": len(items),
        "results": [_fmt_zhihu_item(it) for it in items],
    }
    if data.get("EmptyReason"):
        result["empty_reason"] = data["EmptyReason"]

    out(result)


def cmd_global(args):
    """Search the entire web (全网搜索)."""
    params: dict = {"Query": args.query, "Count": args.count}
    if args.filter:
        params["Filter"] = args.filter
    if args.db:
        params["SearchDB"] = args.db

    resp = api_get("global_search", params)

    if resp.get("Code") != 0:
        die(f"API error: Code={resp.get('Code')} Message={resp.get('Message')}")

    data = resp.get("Data", {})
    items = data.get("Items") or []

    result = {
        "query": args.query,
        "has_more": data.get("HasMore", False),
        "count": len(items),
        "results": [_fmt_global_item(it) for it in items],
    }
    out(result)


def cmd_hot(args):
    """Get current Zhihu trending topics (热榜)."""
    params = {"Limit": args.limit}
    resp = api_get("hot_list", params)

    if resp.get("Code") != 0:
        die(f"API error: Code={resp.get('Code')} Message={resp.get('Message')}")

    data = resp.get("Data", {})
    items = data.get("Items") or []

    result = {
        "total": data.get("Total", len(items)),
        "items": [_fmt_hot_item(it, i + 1) for i, it in enumerate(items)],
    }
    out(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="zhihu-search",
        description="Search Zhihu and the web via the Zhihu Developer Platform API",
    )
    sub = parser.add_subparsers(dest="command")

    # search (zhihu_search)
    p_search = sub.add_parser("search", help="Search Zhihu content (站内搜索)")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--count", type=int, default=10, help="Results count (max 10)")

    # global (global_search)
    p_global = sub.add_parser("global", help="Search the entire web (全网搜索)")
    p_global.add_argument("query", help="Search query")
    p_global.add_argument("--count", type=int, default=10, help="Results count (max 20)")
    p_global.add_argument(
        "--filter",
        help='Advanced filter expression, e.g. host=="example.com" AND publish_time>=1700000000',
    )
    p_global.add_argument(
        "--db",
        choices=["all", "realtime", "static"],
        help="Index to search: all (default), realtime, static",
    )

    # hot (hot_list)
    p_hot = sub.add_parser("hot", help="Get Zhihu trending topics (热榜)")
    p_hot.add_argument("--limit", type=int, default=30, help="Number of items (max 30)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {"search": cmd_search, "global": cmd_global, "hot": cmd_hot}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read Yandex Webmaster hosts and popular queries."""

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


BASE = "https://api.webmaster.yandex.net/v4"


def api_get(path: str, token: str, params=None) -> dict:
    url = BASE + path
    if params:
        url += "?" + urlencode(params)
    req = Request(
        url, headers={"Authorization": f"OAuth {token}", "Accept": "application/json"}
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").replace(token, "[redacted]")
        raise RuntimeError(f"Yandex Webmaster API {exc.code}: {body[:1000]}") from None
    except URLError as exc:
        raise RuntimeError(f"Yandex Webmaster request failed: {exc.reason}") from None


def user_id(token: str) -> str:
    value = api_get("/user", token).get("user_id")
    if value is None:
        raise RuntimeError("Yandex Webmaster did not return user_id")
    return str(value)


def hosts(token: str) -> dict:
    return api_get(f"/user/{quote(user_id(token), safe='')}/hosts", token)


def popular_queries(token: str, host_id: str, limit: int) -> dict:
    if not host_id or limit < 1 or limit > 100:
        raise ValueError("provide a host_id and limit between 1 and 100")
    return api_get(
        f"/user/{quote(user_id(token), safe='')}/hosts/{quote(host_id, safe='')}/search-queries/popular",
        token,
        {"order_by": "TOTAL_SHOWS", "query_indicator": "TOTAL_SHOWS", "limit": limit},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("hosts")
    q = subs.add_parser("popular-queries")
    q.add_argument("--host-id", required=True)
    q.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    token = os.environ.get("YANDEXWEBMASTER_ACCESS_TOKEN", "")
    if not token:
        parser.error("connect Yandex Webmaster first")
    try:
        result = (
            hosts(token)
            if args.command == "hosts"
            else popular_queries(token, args.host_id, args.limit)
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

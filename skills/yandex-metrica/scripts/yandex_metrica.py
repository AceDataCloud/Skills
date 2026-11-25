#!/usr/bin/env python3
"""Read Yandex Metrica counters and acquisition reports."""

import argparse
import json
import os
import sys
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE = "https://api-metrika.yandex.net"
DIMENSIONS = {
    "country": "ym:s:regionCountry",
    "source": "ym:s:<attribution>TrafficSource",
    "utm-source": "ym:s:<attribution>UTMSource",
}


def api_get(path: str, token: str, params=None) -> dict:
    url = BASE + path + ("?" + urlencode(params) if params else "")
    req = Request(
        url, headers={"Authorization": f"OAuth {token}", "Accept": "application/json"}
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").replace(token, "[redacted]")
        raise RuntimeError(f"Yandex Metrica API {exc.code}: {body[:1000]}") from None
    except URLError as exc:
        raise RuntimeError(f"Yandex Metrica request failed: {exc.reason}") from None


def report(token: str, counter_id: str, dimension: str, start: str, end: str) -> dict:
    if not counter_id.isdecimal() or int(counter_id) <= 0:
        raise ValueError("counter_id must be positive and numeric")
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("start must be on or before end")
    return api_get(
        "/stat/v1/data",
        token,
        {
            "ids": counter_id,
            "date1": start,
            "date2": end,
            "dimensions": DIMENSIONS[dimension],
            "attribution": "lastsign",
            "metrics": "ym:s:visits,ym:s:users",
            "accuracy": "full",
            "limit": 100,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("counters")
    r = subs.add_parser("report")
    r.add_argument("--counter-id", required=True)
    r.add_argument("--dimension", choices=sorted(DIMENSIONS), required=True)
    r.add_argument("--start", required=True)
    r.add_argument("--end", required=True)
    args = parser.parse_args()
    token = os.environ.get("YANDEXMETRICA_ACCESS_TOKEN", "")
    if not token:
        parser.error("connect Yandex Metrica first")
    try:
        result = (
            api_get("/management/v1/counters", token)
            if args.command == "counters"
            else report(token, args.counter_id, args.dimension, args.start, args.end)
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

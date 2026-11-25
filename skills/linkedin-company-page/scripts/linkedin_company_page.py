#!/usr/bin/env python3
"""Dry-run-first LinkedIn company Page publisher."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


API = "https://api.linkedin.com/rest/posts"
VERSION = "202609"


def post_payload(organization_id: str, commentary: str) -> dict:
    if not organization_id.isdecimal() or int(organization_id) <= 0:
        raise ValueError("organization_id must be a positive numeric LinkedIn Page ID")
    text = commentary.strip()
    if not text:
        raise ValueError("post text cannot be empty")
    return {
        "author": f"urn:li:organization:{organization_id}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def request(method: str, url: str, token: str, version: str, payload=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            body = response.read()
            parsed = json.loads(body) if body else {}
            return response.status, response.headers, parsed
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").replace(token, "[redacted]")
        raise RuntimeError(f"LinkedIn API {exc.code}: {body[:1200]}") from None
    except URLError as exc:
        raise RuntimeError(f"LinkedIn request failed: {exc.reason}") from None


def publish(organization_id: str, text_file: Path, confirm: bool) -> dict:
    payload = post_payload(organization_id, text_file.read_text(encoding="utf-8"))
    if not confirm:
        return {
            "dry_run": True,
            "target": payload["author"],
            "post": payload["commentary"],
        }
    token = os.environ.get("LINKEDIN_COMPANY_PAGE_TOKEN", "")
    if not token:
        raise ValueError(
            "LINKEDIN_COMPANY_PAGE_TOKEN is not set; connect LinkedIn company Page"
        )
    version = os.environ.get("LINKEDIN_API_VERSION", VERSION)
    status, headers, _ = request("POST", API, token, version, payload)
    if status != 201:
        raise RuntimeError(f"LinkedIn returned unexpected create status {status}")
    urn = headers.get("x-restli-id") or headers.get("X-RestLi-Id")
    if not urn:
        return {
            "submitted": True,
            "verified": False,
            "reason": "No post URN in create response",
        }
    result = {"submitted": True, "verified": False, "urn": urn}
    try:
        read_status, _, body = request(
            "GET", f"{API}/{quote(urn, safe='')}", token, version
        )
        if read_status == 200 and body.get("author") == payload["author"]:
            result["verified"] = True
            result["url"] = (
                f"https://www.linkedin.com/feed/update/{quote(urn, safe=':')}/"
            )
    except RuntimeError as exc:
        result["readback_error"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["publish"])
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                publish(args.organization_id, args.text_file, args.confirm),
                ensure_ascii=False,
            )
        )
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Upload one video to TikTok inbox using FILE_UPLOAD, or fetch status."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = "https://open.tiktokapis.com/v2"
MAX_CHUNK_SIZE = 64 * 1024 * 1024


def output(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def fail(message: str) -> None:
    output({"ok": False, "error": message})
    raise SystemExit(1)


def token() -> str:
    value = os.environ.get("TIKTOK_TOKEN")
    if not value:
        fail("TIKTOK_TOKEN is not set — reconnect TikTok and retry")
    return value


def api(path: str, body: dict) -> dict:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            fail(f"TikTok returned HTTP {error.code}")
    except urllib.error.URLError as error:
        fail(f"network error reaching TikTok: {error.reason}")
    api_error = payload.get("error") or {}
    if api_error.get("code") not in (None, "ok"):
        fail(f"TikTok API error {api_error.get('code')}: {api_error.get('message') or 'request failed'}")
    return payload.get("data") or {}


def upload_file(path: str) -> dict:
    size = os.path.getsize(path)
    if size <= 0:
        fail("video file is empty")
    if size > MAX_CHUNK_SIZE:
        fail("video exceeds the 64 MB single-upload limit")
    init = api(
        "/post/publish/inbox/video/init/",
        {"source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}},
    )
    upload_url = init.get("upload_url")
    publish_id = init.get("publish_id")
    if not upload_url or not publish_id:
        fail("TikTok init response did not contain upload_url and publish_id")
    with open(path, "rb") as video:
        body = video.read()
    request = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size - 1}/{size}",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except urllib.error.URLError as error:
        fail(f"network error uploading video: {error.reason}")
    if status != 201:
        fail(f"TikTok upload returned HTTP {status}, expected 201")
    return {"publish_id": publish_id, "status": "UPLOADED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    upload = sub.add_parser("upload")
    upload.add_argument("file")
    status = sub.add_parser("status")
    status.add_argument("publish_id")
    args = parser.parse_args()
    if args.command == "upload":
        data = upload_file(args.file)
    else:
        data = api("/post/publish/status/fetch/", {"publish_id": args.publish_id})
    output({"ok": True, "data": data})


if __name__ == "__main__":
    main()

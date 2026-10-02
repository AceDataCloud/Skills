#!/usr/bin/env python3
"""Upload to TikTok inbox or run a confirmed private-account review post."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://open.tiktokapis.com/v2"
MAX_CHUNK_SIZE = 64 * 1024 * 1024
VERIFIED_MEDIA_DOMAIN = "acedata.cloud"


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


def creator_info() -> dict:
    return api("/post/publish/creator_info/query/", {})


def check_media_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or not (host == VERIFIED_MEDIA_DOMAIN or host.endswith(f".{VERIFIED_MEDIA_DOMAIN}"))
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        fail("review post requires a public HTTPS video URL under the verified acedata.cloud domain")
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.geturl() != url or response.status != 200:
                fail("video URL redirects or does not return HTTP 200")
            if response.headers.get_content_type() != "video/mp4":
                fail("review video URL must return video/mp4")
    except urllib.error.HTTPError as error:
        fail(f"video URL returned HTTP {error.code}")
    except urllib.error.URLError as error:
        fail(f"network error checking video URL: {error.reason}")


def upload_url(url: str) -> dict:
    check_media_url(url)
    init = api("/post/publish/inbox/video/init/", {"source_info": {"source": "PULL_FROM_URL", "video_url": url}})
    publish_id = init.get("publish_id")
    if not isinstance(publish_id, str) or not publish_id:
        fail("TikTok inbox init did not return a publish_id; check account status before retrying")
    return {"publish_id": publish_id, "status": "PROCESSING_DOWNLOAD"}


def review_post_url(url: str, duration_sec: float, values: dict) -> dict:
    if not isinstance(duration_sec, (int, float)) or not math.isfinite(duration_sec) or duration_sec <= 0:
        fail("review video duration must be positive")
    if not isinstance(values, dict):
        fail("review post values must be an object from the confirmed Studio card")
    title = values.get("title")
    privacy = values.get("privacy_level")
    if not isinstance(title, str) or len(title.encode("utf-16-le")) // 2 > 2200:
        fail("review post title must be a string of at most 2200 UTF-16 code units")
    if privacy != "SELF_ONLY":
        fail("unaudited review posts require the user-selected SELF_ONLY privacy level")
    required_booleans = (
        "disable_comment",
        "disable_duet",
        "disable_stitch",
        "brand_organic_toggle",
        "brand_content_toggle",
        "is_aigc",
    )
    if any(type(values.get(field)) is not bool for field in required_booleans):
        fail("review post requires explicit interaction, disclosure, and AI-content booleans")
    if values["brand_content_toggle"]:
        fail("branded content cannot use SELF_ONLY privacy")
    info = creator_info()
    options = info.get("privacy_level_options")
    if not isinstance(options, list) or privacy not in options:
        fail("SELF_ONLY is not in the creator's current TikTok privacy options")
    maximum = info.get("max_video_post_duration_sec")
    if type(maximum) not in (int, float) or not math.isfinite(maximum) or duration_sec > maximum:
        fail("review video exceeds the creator's current TikTok duration limit")
    for interaction in ("comment", "duet", "stitch"):
        restriction = info.get(f"{interaction}_disabled")
        if type(restriction) is not bool:
            fail(f"creator info did not include the current {interaction} restriction")
        if restriction and values[f"disable_{interaction}"] is False:
            fail(f"the creator's TikTok account disables {interaction}")
    check_media_url(url)
    post_info = {"title": title, "privacy_level": privacy}
    for field in required_booleans:
        post_info[field] = values[field]
    init = api(
        "/post/publish/video/init/",
        {"post_info": post_info, "source_info": {"source": "PULL_FROM_URL", "video_url": url}},
    )
    publish_id = init.get("publish_id")
    if not isinstance(publish_id, str) or not publish_id:
        fail("TikTok Direct Post init did not return a publish_id; check account status before retrying")
    return {"publish_id": publish_id, "status": "PROCESSING_DOWNLOAD"}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    upload = sub.add_parser("upload")
    upload.add_argument("file")
    inbox_url = sub.add_parser("upload-url")
    inbox_url.add_argument("url")
    status = sub.add_parser("status")
    status.add_argument("publish_id")
    sub.add_parser("creator-info")
    review = sub.add_parser("review-post-url")
    review.add_argument("url")
    review.add_argument("--duration-sec", type=float, required=True)
    review.add_argument("--values-file", required=True)
    review.add_argument("--confirmed", action="store_true", required=True)
    args = parser.parse_args()
    if args.command == "upload":
        data = upload_file(args.file)
    elif args.command == "upload-url":
        data = upload_url(args.url)
    elif args.command == "status":
        data = api("/post/publish/status/fetch/", {"publish_id": args.publish_id})
    elif args.command == "creator-info":
        data = creator_info()
    else:
        if args.values_file == "-":
            values = json.load(sys.stdin)
        else:
            with open(args.values_file, encoding="utf-8") as confirmed_values:
                values = json.load(confirmed_values)
        data = review_post_url(args.url, args.duration_sec, values)
    output({"ok": True, "data": data})


if __name__ == "__main__":
    main()

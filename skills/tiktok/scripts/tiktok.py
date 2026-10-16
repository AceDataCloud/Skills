#!/usr/bin/env python3
"""Upload to TikTok inbox or directly post after creator confirmation."""

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
    put_video_file(upload_url, path, size, publish_id)
    return {"publish_id": publish_id, "status": "UPLOADED"}


def put_video_file(upload_url: str, path: str, size: int, publish_id: str) -> None:
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
        fail(f"network error uploading video for {publish_id}: {error.reason}")
    if status != 201:
        fail(f"TikTok upload for {publish_id} returned HTTP {status}, expected 201")


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
        fail("video URL must be public HTTPS under the verified acedata.cloud domain")
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.geturl() != url or response.status != 200:
                fail("video URL redirects or does not return HTTP 200")
            if response.headers.get_content_type() != "video/mp4":
                fail("video URL must return video/mp4")
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


def direct_post_info(duration_sec: float, values: dict, expected_creator_username: str) -> dict:
    if not isinstance(duration_sec, (int, float)) or not math.isfinite(duration_sec) or duration_sec <= 0:
        fail("video duration must be positive")
    if not isinstance(values, dict):
        fail("post values must be an object from the confirmed Studio card")
    title = values.get("title")
    privacy = values.get("privacy_level")
    if not isinstance(title, str) or len(title.encode("utf-16-le")) // 2 > 2200:
        fail("post title must be a string of at most 2200 UTF-16 code units")
    if not isinstance(privacy, str) or not privacy:
        fail("privacy level must be selected in the Studio card")
    required_booleans = (
        "disable_comment",
        "disable_duet",
        "disable_stitch",
        "brand_organic_toggle",
        "brand_content_toggle",
        "is_aigc",
    )
    if any(type(values.get(field)) is not bool for field in required_booleans):
        fail("direct post requires explicit interaction, disclosure, and AI-content booleans")
    if values["brand_content_toggle"] and privacy == "SELF_ONLY":
        fail("branded content cannot use SELF_ONLY privacy")
    info = creator_info()
    actual_creator_username = info.get("creator_username")
    expected_username = expected_creator_username[1:] if expected_creator_username.startswith("@") else expected_creator_username
    expected_username = expected_username.strip()
    if not expected_username or not isinstance(actual_creator_username, str) or actual_creator_username.casefold() != expected_username.casefold():
        fail("connected TikTok creator does not match the confirmed destination account")
    options = info.get("privacy_level_options")
    if not isinstance(options, list) or privacy not in options:
        fail("selected privacy level is not in the creator's current TikTok privacy options")
    maximum = info.get("max_video_post_duration_sec")
    if type(maximum) not in (int, float) or not math.isfinite(maximum) or duration_sec > maximum:
        fail("video exceeds the creator's current TikTok duration limit")
    for interaction in ("comment", "duet", "stitch"):
        restriction = info.get(f"{interaction}_disabled")
        if type(restriction) is not bool:
            fail(f"creator info did not include the current {interaction} restriction")
        if restriction and values[f"disable_{interaction}"] is False:
            fail(f"the creator's TikTok account disables {interaction}")
    post_info = {"title": title, "privacy_level": privacy}
    for field in required_booleans:
        post_info[field] = values[field]
    return post_info


def direct_post_url(url: str, duration_sec: float, values: dict, expected_creator_username: str) -> dict:
    post_info = direct_post_info(duration_sec, values, expected_creator_username)
    check_media_url(url)
    init = api(
        "/post/publish/video/init/",
        {"post_info": post_info, "source_info": {"source": "PULL_FROM_URL", "video_url": url}},
    )
    publish_id = init.get("publish_id")
    if not isinstance(publish_id, str) or not publish_id:
        fail("TikTok Direct Post init did not return a publish_id; check account status before retrying")
    return {"publish_id": publish_id, "status": "PROCESSING_DOWNLOAD"}


def direct_post_file(path: str, duration_sec: float, values: dict, expected_creator_username: str) -> dict:
    size = os.path.getsize(path)
    if size <= 0 or size > MAX_CHUNK_SIZE:
        fail("video must be a non-empty MP4 no larger than 64 MB")
    post_info = direct_post_info(duration_sec, values, expected_creator_username)
    init = api(
        "/post/publish/video/init/",
        {
            "post_info": post_info,
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1},
        },
    )
    upload_url = init.get("upload_url")
    publish_id = init.get("publish_id")
    if not isinstance(upload_url, str) or not upload_url or not isinstance(publish_id, str) or not publish_id:
        fail("TikTok Direct Post init did not return an upload_url and publish_id; check account status before retrying")
    put_video_file(upload_url, path, size, publish_id)
    return {"publish_id": publish_id, "status": "PROCESSING_UPLOAD"}


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
    for command, source in (("post-url", "url"), ("post-file", "file"), ("review-post-url", "url")):
        direct = sub.add_parser(command, help=argparse.SUPPRESS if command == "review-post-url" else None)
        direct.add_argument(source)
        direct.add_argument("--duration-sec", type=float, required=True)
        direct.add_argument("--expected-creator-username", required=True)
        direct.add_argument("--values-file", required=True)
        direct.add_argument("--confirmed", action="store_true", required=True)
    args = parser.parse_args()
    if args.command == "upload":
        data = upload_file(args.file)
    elif args.command == "upload-url":
        data = upload_url(args.url)
    elif args.command == "status":
        data = api("/post/publish/status/fetch/", {"publish_id": args.publish_id})
    elif args.command == "creator-info":
        data = creator_info()
    elif args.command in ("post-url", "post-file", "review-post-url"):
        if args.values_file == "-":
            values = json.load(sys.stdin)
        else:
            with open(args.values_file, encoding="utf-8") as confirmed_values:
                values = json.load(confirmed_values)
        if args.command == "post-file":
            data = direct_post_file(args.file, args.duration_sec, values, args.expected_creator_username)
        else:
            data = direct_post_url(args.url, args.duration_sec, values, args.expected_creator_username)
    output({"ok": True, "data": data})


if __name__ == "__main__":
    main()

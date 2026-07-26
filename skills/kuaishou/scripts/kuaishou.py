#!/usr/bin/env python3
"""kuaishou — publish video to & read works from the user's 快手 account.

Standard-library only (urllib), no third-party deps. The connector injects the
user's OAuth token as ``KUAISHOU_TOKEN``; ``KUAISHOU_APP_ID`` carries the app id
that every open-platform call also requires.

Publishing is three stateful calls (start_upload → upload → publish), which is
why this is a script and not raw curl. ``publish`` is GATED: without a trailing
``--confirm`` it only dry-runs. ``--confirm`` is honored ONLY as the last
argument, so a caption that merely contains "--confirm" can never self-authorize.

Examples:
  python3 kuaishou.py whoami
  python3 kuaishou.py works --limit 20
  python3 kuaishou.py work <photo-id>
  python3 kuaishou.py counts
  python3 kuaishou.py publish --video-url URL --cover-url URL --caption T --confirm
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import os
import re
import socket
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

API = "https://open.kuaishou.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
MAX_COVER_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 500 * 1024 * 1024
CHUNK = 8 * 1024 * 1024  # Kuaishou recommends fragments <= 10MB.
DIRECT_UPLOAD_MAX = 10 * 1024 * 1024

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


def _creds():
    token = os.environ.get("KUAISHOU_TOKEN", "").strip()
    app_id = os.environ.get("KUAISHOU_APP_ID", "").strip()
    if not token:
        die("KUAISHOU_TOKEN is not set — connect 快手 first")
    if not app_id:
        die("KUAISHOU_APP_ID is not set — the connector must inject the app id")
    return token, app_id


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # A 30x could otherwise reach an internal host _assert_public_url() never saw.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError(f"media redirect blocked ({code}) -> {newurl[:80]}")


_MEDIA_OPENER = urllib.request.build_opener(_NoRedirect)


MEDIA_HOST_ALLOWLIST = ("cdn.acedata.cloud", "acedata.cloud", "kwimgs.com", "yximgs.com")


def _assert_public_url(url: str) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise RuntimeError(f"unsupported media URL: {url[:80]}")
    host = parts.hostname.lower()
    # Allowlist, not just an IP check: a bare IP check is defeated by DNS
    # rebinding (pass on the first resolve, point at 169.254.169.254 on the
    # second). Media we publish comes from our own CDN anyway.
    if not any(host == h or host.endswith("." + h) for h in MEDIA_HOST_ALLOWLIST):
        raise RuntimeError(
            f"media host not allowed: {host} — upload the file to cdn.acedata.cloud first, or pass a local path"
        )
    try:
        addrs = socket.getaddrinfo(host, None)
    except OSError as e:
        raise RuntimeError(f"cannot resolve {host}: {e}")
    for info in addrs:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise RuntimeError(f"blocked non-public media host: {host}")


def _download_to(url: str, limit: int, dest) -> int:
    """Stream to *dest* so a 500MB video never sits in memory."""
    _assert_public_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    total = 0
    with _MEDIA_OPENER.open(req, timeout=300) as r:
        while True:
            buf = r.read(1024 * 1024)
            if not buf:
                break
            total += len(buf)
            if total > limit:
                raise RuntimeError(f"media exceeds {limit} bytes")
            dest.write(buf)
    dest.flush()
    return total


def _download(url: str, limit: int) -> bytes:
    _assert_public_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _MEDIA_OPENER.open(req, timeout=120) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError(f"media exceeds {limit} bytes")
    return data


def _read_media(url: str | None, path: str | None, limit: int, what: str) -> bytes:
    """Small media (covers) only — video streams to disk via ``_download_to``."""
    if url:
        return _download(url, limit)
    if path:
        with open(path, "rb") as fh:
            data = fh.read(limit + 1)
        if len(data) > limit:
            raise RuntimeError(f"{what} exceeds {limit} bytes")
        return data
    raise RuntimeError(f"no {what} provided")


def _redact(text: str) -> str:
    """Strip credentials before anything upstream-echoed reaches stdout."""
    for name in ("access_token", "upload_token", "app_secret", "refresh_token"):
        text = re.sub(rf"({name}[\"'=:\s]+)[^\s\"'&,}}]+", r"\1<redacted>", text)
    for var in ("KUAISHOU_TOKEN", "KUAISHOU_APP_ID"):
        secret = os.environ.get(var, "")
        if len(secret) >= 6:
            text = text.replace(secret, "<redacted>")
    return text


def _check(payload: dict, what: str) -> dict:
    # Kuaishou answers HTTP 200 even on failure; ``result`` is the real status.
    if payload.get("result") != 1:
        raise RuntimeError(_redact(f"{what} failed: {json.dumps(payload, ensure_ascii=False)}"))
    return payload


def _api(path: str, params: dict, method: str = "GET", body: bytes | None = None, ctype: str | None = None) -> dict:
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": UA}
    if ctype:
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(_redact(f"HTTP {e.code} from {path}: {detail}"))


def _multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = "----AceDataKuaishou" + os.urandom(8).hex()
    buf = bytearray()
    for name, value in fields.items():
        if value is None:
            continue
        buf += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
    for name, (filename, blob) in files.items():
        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        buf += (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode()
        buf += blob + b"\r\n"
    buf += f"--{boundary}--\r\n".encode()
    return bytes(buf), f"multipart/form-data; boundary={boundary}"


def _upload_binary(endpoint: str, upload_token: str, path: str, size: int) -> None:
    """Step 2 — direct for small files, fragmented otherwise. Reads from disk
    one chunk at a time so peak memory stays at one fragment."""
    # The gateway is plain http per the docs and the host is issued fresh by
    # start_upload — never hardcode it.
    base = f"http://{endpoint}"
    if size <= DIRECT_UPLOAD_MAX:
        with open(path, "rb") as fh:
            blob = fh.read()
        url = f"{base}/api/upload?{urllib.parse.urlencode({'upload_token': upload_token})}"
        req = urllib.request.Request(url, data=blob, headers={"Content-Type": "video/mp4"}, method="POST")
        with urllib.request.urlopen(req, timeout=600) as r:
            _check(json.loads(r.read().decode("utf-8", "replace")), "upload")
        return

    count = 0
    with open(path, "rb") as fh:
        while True:
            part = fh.read(CHUNK)
            if not part:
                break
            q = urllib.parse.urlencode({"upload_token": upload_token, "fragment_id": count})  # starts at 0
            req = urllib.request.Request(
                f"{base}/api/upload/fragment?{q}", data=part, headers={"Content-Type": "video/mp4"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=600) as r:
                _check(json.loads(r.read().decode("utf-8", "replace")), f"fragment {count}")
            count += 1
    q = urllib.parse.urlencode({"upload_token": upload_token, "fragment_count": count})
    req = urllib.request.Request(f"{base}/api/upload/complete?{q}", data=b"", method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        _check(json.loads(r.read().decode("utf-8", "replace")), "complete")


def cmd_whoami() -> None:
    token, app_id = _creds()
    data = _check(_api("/openapi/user_info", {"app_id": app_id, "access_token": token}), "user_info")
    out(data.get("user_info") or {})


def cmd_works(limit: int, cursor: str | None) -> None:
    token, app_id = _creds()
    params = {"app_id": app_id, "access_token": token, "count": max(1, min(limit, 200))}
    if cursor:
        params["cursor"] = cursor
    data = _check(_api("/openapi/photo/list", params), "photo/list")
    out({"video_list": data.get("video_list") or []})


def cmd_work(photo_id: str) -> None:
    token, app_id = _creds()
    data = _check(
        _api("/openapi/photo/info", {"app_id": app_id, "access_token": token, "photo_id": photo_id}), "photo/info"
    )
    out(data.get("video_info") or {})


def cmd_counts() -> None:
    token, app_id = _creds()
    data = _check(_api("/openapi/photo/count", {"app_id": app_id, "access_token": token}), "photo/count")
    data.pop("result", None)
    out(data)


def cmd_publish(args) -> None:
    token, app_id = _creds()
    if not args.caption:
        die("--caption is required (快手 requires a title)")
    if not (args.cover_url or args.cover_file):
        die("--cover-url or --cover-file is required (快手 requires a cover image)")
    if not (args.video_url or args.video_file):
        die("--video-url or --video-file is required")

    if not CONFIRM:
        out(
            {
                "dry_run": True,
                "caption": args.caption,
                "video": args.video_url or args.video_file,
                "cover": args.cover_url or args.cover_file,
                "note": (
                    "Nothing was published. Confirm the content is the user's own original work — "
                    "快手 bans accounts that publish non-original video. Re-run with --confirm as the LAST argument."
                ),
            }
        )
        return

    tmp = None
    try:
        cover = _read_media(args.cover_url, args.cover_file, MAX_COVER_BYTES, "cover")
        if args.video_url:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            size = _download_to(args.video_url, MAX_VIDEO_BYTES, tmp)
            tmp.close()
            video_path = tmp.name
        else:
            video_path = args.video_file
            size = os.path.getsize(video_path)
            if size > MAX_VIDEO_BYTES:
                raise RuntimeError(f"video exceeds {MAX_VIDEO_BYTES} bytes")

        started = _check(
            _api("/openapi/photo/start_upload", {"app_id": app_id, "access_token": token}, method="POST"),
            "start_upload",
        )
        upload_token = started["upload_token"]
        _upload_binary(started["endpoint"], upload_token, video_path, size)

        fields = {"caption": args.caption}
        if args.stereo_type:
            fields["stereo_type"] = args.stereo_type
        if args.product_id:
            fields["merchant_product_id"] = args.product_id
        body, ctype = _multipart(fields, {"cover": ("cover.jpg", cover)})
        published = _check(
            _api(
                "/openapi/photo/publish",
                {"app_id": app_id, "access_token": token, "upload_token": upload_token},
                method="POST",
                body=body,
                ctype=ctype,
            ),
            "photo/publish",
        )
    except (RuntimeError, OSError) as e:
        die(_redact(str(e)))
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    info = published.get("video_info") or {}
    photo_id = info.get("photo_id")
    out(
        {
            "published": True,
            "photo_id": photo_id,
            "caption": info.get("caption"),
            "url": f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else None,
            "pending": info.get("pending"),
        }
    )


def main() -> None:
    p = argparse.ArgumentParser(prog="kuaishou", description="快手 open-platform client")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami")
    sub.add_parser("counts")

    w = sub.add_parser("works")
    w.add_argument("--limit", type=int, default=20)
    w.add_argument("--cursor")

    one = sub.add_parser("work")
    one.add_argument("photo_id")

    pub = sub.add_parser("publish")
    pub.add_argument("--caption", required=False)
    pub.add_argument("--video-url")
    pub.add_argument("--video-file")
    pub.add_argument("--cover-url")
    pub.add_argument("--cover-file")
    pub.add_argument("--stereo-type", choices=["NOT_SPHERICAL_VIDEO", "SPHERICAL_VIDEO_360", "SPHERICAL_VIDEO_180"])
    pub.add_argument("--product-id")

    args = p.parse_args(ARGV)
    if args.cmd == "whoami":
        cmd_whoami()
    elif args.cmd == "counts":
        cmd_counts()
    elif args.cmd == "works":
        cmd_works(args.limit, args.cursor)
    elif args.cmd == "work":
        cmd_work(args.photo_id)
    elif args.cmd == "publish":
        cmd_publish(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Xiaohongshu automation through the user's AceDataCloud connector cookies."""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import ipaddress
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

COOKIE_ENV = "XIAOHONGSHU_COOKIES"
ALLOWED_COOKIE_DOMAINS = {"xiaohongshu.com", ".xiaohongshu.com"}
SAME_SITE_MAP = {
    "strict": "Strict",
    "lax": "Lax",
    "no_restriction": "None",
    "none": "None",
}
CHROMIUM_PATHS = (
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
VENDOR_DIR = Path(__file__).with_name("vendor")
WRITE_COMMANDS = {
    "publish",
    "publish-video",
    "publish-long",
    "comment",
    "reply",
    "like",
    "unlike",
    "favorite",
    "unfavorite",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv"}
MAX_REMOTE_IMAGE_BYTES = 25 * 1024 * 1024
MAX_STAGED_MEDIA_BYTES = 256 * 1024 * 1024
VISIBILITY_CHOICES = ("公开可见", "仅自己可见", "仅互关好友可见")
SEARCH_SORT_CHOICES = ("综合", "最新", "最多点赞", "最多评论", "最多收藏")
SEARCH_TYPE_CHOICES = ("不限", "视频", "图文")
SEARCH_TIME_CHOICES = ("不限", "一天内", "一周内", "半年内")
SEARCH_SCOPE_CHOICES = ("不限", "已看过", "未看过", "已关注")
SEARCH_LOCATION_CHOICES = ("不限", "同城", "附近")

_RAW_ARGS = sys.argv[1:]
CONFIRM = bool(_RAW_ARGS) and _RAW_ARGS[-1] == "--confirm"
ARGV = _RAW_ARGS[:-1] if CONFIRM else list(_RAW_ARGS)


class ConnectorCookieError(RuntimeError):
    """The connector cookie jar is absent or cannot be used safely."""


def _is_xiaohongshu_domain(domain: str) -> bool:
    normalized = domain.strip().lower().rstrip(".")
    return normalized in ALLOWED_COOKIE_DOMAINS or normalized.endswith(
        ".xiaohongshu.com"
    )


def load_connector_cookie_jar(raw: str | None = None) -> list[dict]:
    """Load the Chrome-extension cookie jar injected by the connector."""
    serialized = raw if raw is not None else os.environ.get(COOKIE_ENV)
    if not serialized:
        raise ConnectorCookieError(
            "Xiaohongshu is not connected. Connect it at "
            "https://auth.acedata.cloud/user/connections."
        )
    try:
        cookie_jar = json.loads(serialized)
    except json.JSONDecodeError as error:
        raise ConnectorCookieError(f"{COOKIE_ENV} is not valid JSON") from error
    if not isinstance(cookie_jar, list) or not cookie_jar:
        raise ConnectorCookieError(f"{COOKIE_ENV} must be a non-empty cookie list")
    if not all(isinstance(cookie, dict) for cookie in cookie_jar):
        raise ConnectorCookieError(f"{COOKIE_ENV} contains a non-object cookie")
    return cookie_jar


def convert_connector_cookies(
    cookie_jar: list[dict], now: float | None = None
) -> list[dict]:
    """Convert Chrome-extension cookies to CDP ``CookieParam`` records."""
    current_time = time.time() if now is None else now
    converted: list[dict] = []

    for cookie in cookie_jar:
        name = cookie.get("name")
        value = cookie.get("value")
        domain = cookie.get("domain") or ".xiaohongshu.com"
        if not isinstance(name, str) or not name:
            raise ConnectorCookieError("cookie name must be a non-empty string")
        if not isinstance(value, str):
            raise ConnectorCookieError(f"cookie {name!r} has a non-string value")
        if not isinstance(domain, str) or not _is_xiaohongshu_domain(domain):
            raise ConnectorCookieError(f"cookie {name!r} has an invalid domain")

        expiration = cookie.get("expirationDate")
        if expiration is not None:
            if not isinstance(expiration, (int, float)):
                raise ConnectorCookieError(
                    f"cookie {name!r} has an invalid expirationDate"
                )
            if expiration <= current_time:
                continue

        converted_cookie = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": cookie.get("path") if isinstance(cookie.get("path"), str) else "/",
            "httpOnly": bool(cookie.get("httpOnly")),
            "secure": bool(cookie.get("secure")),
        }
        if expiration is not None:
            converted_cookie["expires"] = expiration
        same_site = cookie.get("sameSite")
        if isinstance(same_site, str) and same_site.lower() in SAME_SITE_MAP:
            converted_cookie["sameSite"] = SAME_SITE_MAP[same_site.lower()]
        converted.append(converted_cookie)

    if not converted:
        raise ConnectorCookieError("all Xiaohongshu connector cookies are expired")
    return converted


def output(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def fail(message: str, code: int = 1) -> None:
    output({"success": False, "error": message})
    raise SystemExit(code)


def _sanitize_error(message: str) -> str:
    sanitized = re.sub(
        r"(?i)(xsec_token[=/:'\"\s]+)[^&\s'\"]+", r"\1[REDACTED]", message
    )
    try:
        for cookie in load_connector_cookie_jar():
            value = cookie.get("value")
            if isinstance(value, str) and len(value) >= 6:
                sanitized = sanitized.replace(value, "[REDACTED]")
    except ConnectorCookieError:
        pass
    return sanitized


def _redact_xsec_tokens(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower().replace("_", "") == "xsectoken"
            else _redact_xsec_tokens(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_xsec_tokens(item) for item in value]
    return value


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _stage_media_payload(
    payload: dict[str, Any], directory: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    staged = copy.deepcopy(payload)
    canonical = copy.deepcopy(payload)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    total_staged_bytes = 0

    def stage(reference: str, index: int) -> tuple[str, dict[str, Any]]:
        nonlocal total_staged_bytes
        if reference.startswith("https://"):
            source = Path(_download_public_image(reference, directory))
        else:
            source = Path(reference)
        suffix = source.suffix.lower()
        target = directory / f"media-{index}{suffix}"
        size = source.stat().st_size
        total_staged_bytes += size
        if total_staged_bytes > MAX_STAGED_MEDIA_BYTES:
            if reference.startswith("https://"):
                source.unlink(missing_ok=True)
            raise ValueError("staged media exceeds 256 MB in total")
        if source != target:
            if reference.startswith("https://"):
                source.replace(target)
            else:
                shutil.copyfile(source, target)
            target.chmod(0o600)
        digest, hashed_size = _hash_file(target)
        if hashed_size != size:
            raise RuntimeError("media changed while it was being staged")
        return str(target), {"source": reference, "sha256": digest, "size": size}

    media_index = 0
    if isinstance(payload.get("images"), list):
        staged_images = []
        canonical_images = []
        for reference in payload["images"]:
            staged_path, media = stage(reference, media_index)
            media_index += 1
            staged_images.append(staged_path)
            canonical_images.append(media)
        staged["images"] = staged_images
        canonical["images"] = canonical_images
    if isinstance(payload.get("video"), str):
        staged_path, media = stage(payload["video"], media_index)
        staged["video"] = staged_path
        canonical["video"] = media
    return staged, canonical


def _preview_digest(command: str, canonical_payload: dict[str, Any]) -> str:
    serialized = json.dumps(
        {"command": command, "payload": canonical_payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_executable(env_name: str, candidates: tuple[str, ...]) -> str:
    configured = os.environ.get(env_name)
    if configured:
        path = shutil.which(configured) or configured
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
        raise RuntimeError(f"{env_name} points to a missing or non-executable file")
    for candidate in candidates:
        path = shutil.which(candidate) or candidate
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise RuntimeError(
        "the Xiaohongshu automation runtime is not installed in this sandbox; "
        "deploy the current platform-service-sandbox image"
    )


def _chromium_child_env(workdir: Path) -> dict[str, str]:
    """Build a minimal child environment that never contains connector secrets."""
    return {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "NO_COLOR": "1",
        "HOME": str(workdir),
        "TMPDIR": str(workdir),
        "XDG_CACHE_HOME": str(workdir / "cache"),
        "XDG_CONFIG_HOME": str(workdir / "config"),
        "NO_PROXY": "127.0.0.1,localhost",
    }


def _chromium_arguments(
    chromium: str,
    profile_dir: Path,
    stealth_args: list[str],
    proxy: str | None,
) -> list[str]:
    arguments = [
        chromium,
        "--remote-debugging-pipe",
        f"--user-data-dir={profile_dir}",
        "--headless=new",
        "--incognito",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        *stealth_args,
    ]
    if proxy:
        parsed_proxy = urlsplit(proxy)
        if parsed_proxy.username or parsed_proxy.password:
            raise RuntimeError("authenticated XIAOHONGSHU_PROXY URLs are not supported")
        arguments.append(f"--proxy-server={proxy}")
    return list(dict.fromkeys(arguments))


def _public_https_addresses(value: str) -> tuple[str, ...]:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return ()
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(
        (".localhost", ".local", ".internal")
    ):
        return ()
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname, parsed.port or 443, type=socket.SOCK_STREAM
            )
        }
    except socket.gaierror:
        return ()
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            return ()
    return tuple(sorted(addresses))


def _is_public_https_url(value: str) -> bool:
    return bool(_public_https_addresses(value))


def _validate_media_reference(value: str, *, image: bool) -> str:
    if value.startswith(("http://", "https://")):
        if not image:
            raise ValueError(
                "video publishing only supports a local absolute file path"
            )
        if not _is_public_https_url(value):
            raise ValueError(f"image URL must be public HTTPS: {value}")
        suffix = Path(urlsplit(value).path).suffix.lower()
        if suffix and suffix not in IMAGE_SUFFIXES:
            raise ValueError(f"unsupported image URL extension: {suffix}")
        return value

    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"media path must be absolute: {value}")
    if not path.is_file():
        raise ValueError(f"media file does not exist: {value}")
    allowed = IMAGE_SUFFIXES if image else VIDEO_SUFFIXES
    if path.suffix.lower() not in allowed:
        raise ValueError(
            f"unsupported {'image' if image else 'video'} extension: {path.suffix}"
        )
    return str(path)


def _download_public_image(url: str, directory: Path) -> str:
    current = url
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/146 Safari/537.36"
    }
    for _ in range(6):
        parsed = urlsplit(current)
        addresses = _public_https_addresses(current)
        if not addresses or not parsed.hostname:
            raise ValueError(f"image redirect is not public HTTPS: {current}")
        response, pool = _open_pinned_https_response(current, addresses[0], headers)
        try:
            result = _consume_image_response(response, current, directory)
            if result[0] == "redirect":
                current = urljoin(current, result[1])
                continue
            return result[1]
        finally:
            response.release_conn()
            pool.close()
    raise ValueError("image URL has too many redirects")


def _open_pinned_https_response(
    url: str, address: str, headers: dict[str, str]
) -> tuple[urllib3.response.BaseHTTPResponse, urllib3.HTTPSConnectionPool]:
    parsed = urlsplit(url)
    assert parsed.hostname
    pool = urllib3.HTTPSConnectionPool(
        address,
        parsed.port or 443,
        assert_hostname=parsed.hostname,
        server_hostname=parsed.hostname,
        cert_reqs="CERT_REQUIRED",
        maxsize=1,
        block=True,
    )
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    try:
        response = pool.request(
            "GET",
            path,
            headers={**headers, "Host": parsed.netloc},
            redirect=False,
            preload_content=False,
            retries=False,
            timeout=urllib3.Timeout(connect=10, read=30),
        )
    except Exception:
        pool.close()
        raise
    return response, pool


def _consume_image_response(
    response: urllib3.response.BaseHTTPResponse, current: str, directory: Path
) -> tuple[str, str]:
    connection = response.connection
    peer_socket = getattr(connection, "sock", None)
    if peer_socket is None:
        raise RuntimeError("image download peer address is unavailable")
    peer_ip = ipaddress.ip_address(peer_socket.getpeername()[0])
    if not peer_ip.is_global:
        raise ValueError("image download connected to a non-public address")

    if response.status in {301, 302, 303, 307, 308}:
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError("image redirect is missing Location")
        return "redirect", location
    if response.status != 200:
        raise RuntimeError(f"image download returned HTTP {response.status}")

    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
    if not content_type.startswith("image/"):
        raise ValueError(f"remote media is not an image: {content_type or 'unknown'}")
    declared_size = response.headers.get("Content-Length")
    if declared_size and int(declared_size) > MAX_REMOTE_IMAGE_BYTES:
        raise ValueError("remote image exceeds 25 MB")

    suffix = Path(urlsplit(current).path).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        suffix = {"image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}.get(
            content_type, ".jpg"
        )
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = (
        directory
        / f"remote-{hashlib.sha256(current.encode()).hexdigest()[:16]}{suffix}"
    )
    total = 0
    try:
        with target.open("wb") as file_handle:
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_REMOTE_IMAGE_BYTES:
                    raise ValueError("remote image exceeds 25 MB")
                file_handle.write(chunk)
        target.chmod(0o600)
        return "image", str(target)
    except Exception:
        target.unlink(missing_ok=True)
        raise


def _prepare_images(images: list[str], directory: Path) -> list[str]:
    return [
        _download_public_image(image, directory)
        if image.startswith("https://")
        else image
        for image in images
    ]


def _title_units(title: str) -> int:
    return sum(1 if ord(character) < 128 else 2 for character in title)


def _validate_publish_text(title: str, content: str) -> None:
    if not title.strip():
        raise ValueError("title cannot be empty")
    if _title_units(title) > 40:
        raise ValueError("title exceeds Xiaohongshu's 20-character display limit")
    if not content.strip():
        raise ValueError("content cannot be empty")
    if len(content) > 1000:
        raise ValueError("content exceeds Xiaohongshu's 1000-character limit")


def _validate_long_article_text(title: str, content: str, description: str) -> None:
    if not title.strip():
        raise ValueError("title cannot be empty")
    if _title_units(title) > 40:
        raise ValueError("title exceeds Xiaohongshu's 20-character display limit")
    if not content.strip():
        raise ValueError("long article content cannot be empty")
    if len(content) > 20000:
        raise ValueError("long article content exceeds 20000 characters")
    if len(description) > 1000:
        raise ValueError("long article description exceeds 1000 characters")


def _validate_schedule(value: str | None) -> None:
    if not value:
        return
    normalized = value.replace("Z", "+00:00")
    try:
        scheduled = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError("schedule-at must be ISO 8601") from error
    if scheduled.tzinfo is None:
        raise ValueError("schedule-at must include a timezone offset")
    now = datetime.now(timezone.utc)
    if scheduled < now + timedelta(hours=1) or scheduled > now + timedelta(days=14):
        raise ValueError("schedule-at must be between 1 hour and 14 days from now")


def _unattended_write_allowed() -> tuple[bool, str]:
    if os.environ.get("AICHAT_UNATTENDED_MODE") != "true":
        return True, "interactive"
    return False, "Xiaohongshu writes require interactive confirmation"


def _read_text_argument(value: str | None, file_path: str | None, label: str) -> str:
    if value is not None and file_path is not None:
        raise ValueError(f"use either --{label} or --{label}-file, not both")
    if file_path:
        path = Path(file_path).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise ValueError(f"--{label}-file must be an existing absolute path")
        return path.read_text(encoding="utf-8").strip()
    return (value or "").strip()


def _payload_for_command(args: argparse.Namespace) -> dict[str, Any] | None:
    command = args.command
    if command == "publish":
        title = _read_text_argument(args.title, args.title_file, "title")
        content = _read_text_argument(args.content, args.content_file, "content")
        _validate_publish_text(title, content)
        images = [_validate_media_reference(value, image=True) for value in args.images]
        if not 1 <= len(images) <= 18:
            raise ValueError("publish requires 1 to 18 images")
        _validate_schedule(args.schedule_at)
        return {
            "title": title,
            "content": content,
            "images": images,
            "tags": args.tags,
            "schedule_at": args.schedule_at or "",
            "is_original": args.original,
            "visibility": args.visibility,
            "products": args.products,
        }
    if command == "publish-video":
        title = _read_text_argument(args.title, args.title_file, "title")
        content = _read_text_argument(args.content, args.content_file, "content")
        _validate_publish_text(title, content)
        video = _validate_media_reference(args.video, image=False)
        _validate_schedule(args.schedule_at)
        return {
            "title": title,
            "content": content,
            "video": video,
            "tags": args.tags,
            "schedule_at": args.schedule_at or "",
            "visibility": args.visibility,
            "products": args.products,
        }
    if command == "publish-long":
        if args.images:
            raise ValueError(
                "long-article inline images are unavailable until Xiaohongshu exposes a verifiable web upload flow"
            )
        title = _read_text_argument(args.title, args.title_file, "title")
        content = _read_text_argument(args.content, args.content_file, "content")
        description = _read_text_argument(
            args.description, args.description_file, "description"
        )
        if not description:
            description = content[:800]
        _validate_long_article_text(title, content, description)
        images = [_validate_media_reference(value, image=True) for value in args.images]
        _validate_schedule(args.schedule_at)
        return {
            "title": title,
            "content": content,
            "description": description,
            "images": images,
            "template": args.template or "",
            "schedule_at": args.schedule_at or "",
            "is_original": args.original,
            "visibility": args.visibility,
            "products": args.products,
        }
    if command == "search":
        filters = {
            key: value
            for key, value, default in (
                ("sort_by", args.sort_by, "综合"),
                ("note_type", args.note_type, "不限"),
                ("publish_time", args.publish_time, "不限"),
                ("search_scope", args.search_scope, "不限"),
                ("location", args.location, "不限"),
            )
            if value != default
        }
        return {"keyword": args.keyword, **({"filters": filters} if filters else {})}
    if command == "detail":
        return {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "xsec_source": args.xsec_source,
            "load_all_comments": args.load_all_comments,
            "click_more_replies": args.click_more_replies,
            "limit": args.limit,
            "reply_limit": args.reply_limit,
            "scroll_speed": args.scroll_speed,
        }
    if command == "profile":
        return {"user_id": args.user_id, "xsec_token": args.xsec_token}
    if command == "comment":
        return {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "xsec_source": args.xsec_source,
            "content": args.content,
        }
    if command == "reply":
        if not args.comment_id:
            raise ValueError(
                "reply requires an exact --comment-id; --user-id is not unique"
            )
        return {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "xsec_source": args.xsec_source,
            "comment_id": args.comment_id or "",
            "user_id": args.user_id or "",
            "content": args.content,
        }
    if command in {"like", "unlike"}:
        return {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "xsec_source": args.xsec_source,
            "unlike": command == "unlike",
        }
    if command in {"favorite", "unfavorite"}:
        return {
            "feed_id": args.feed_id,
            "xsec_token": args.xsec_token,
            "xsec_source": args.xsec_source,
            "unfavorite": command == "unfavorite",
        }
    return None


class DirectXiaohongshuRuntime:
    """Run one isolated Chromium session with connector cookies in memory."""

    def __init__(self, cookies: list[dict]):
        self.cookies = cookies
        self.process: subprocess.Popen[bytes] | None = None
        self.browser: Any = None
        self.page: Any = None
        self.log_handle: Any = None
        self.temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self.workdir: Path | None = None
        self.cdp_transport: Any = None
        self.previous_signal_handlers: dict[int, Any] = {}

    def __enter__(self) -> "DirectXiaohongshuRuntime":
        if not VENDOR_DIR.is_dir():
            raise RuntimeError("the vendored Xiaohongshu browser engine is missing")
        if str(VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(VENDOR_DIR))

        from xhs.cdp import Browser, PipeTransport
        from xhs.stealth import STEALTH_ARGS

        chromium = _resolve_executable("XIAOHONGSHU_CHROMIUM_BIN", CHROMIUM_PATHS)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="acedata-xhs-")
        self.workdir = Path(self.temp_dir.name)
        self.workdir.chmod(0o700)
        profile_dir = self.workdir / "profile"
        profile_dir.mkdir(mode=0o700)
        log_path = self.workdir / "runtime.log"
        log_path.touch(mode=0o600)
        self.log_handle = log_path.open("wb")

        proxy = os.environ.get("XIAOHONGSHU_PROXY")
        arguments = _chromium_arguments(chromium, profile_dir, STEALTH_ARGS, proxy)
        child_env = _chromium_child_env(self.workdir)
        browser_read, parent_write = os.pipe()
        parent_read, browser_write = os.pipe()

        def map_pipe_fds() -> None:
            os.dup2(browser_read, 3)
            os.dup2(browser_write, 4)
            os.set_inheritable(3, True)
            os.set_inheritable(4, True)
            for fd in {browser_read, browser_write} - {3, 4}:
                os.close(fd)
            if sys.platform.startswith("linux"):
                import ctypes

                ctypes.CDLL(None).prctl(1, signal.SIGKILL)

        try:
            self.process = subprocess.Popen(
                arguments,
                cwd=self.workdir,
                env=child_env,
                stdin=subprocess.DEVNULL,
                stdout=self.log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                pass_fds=tuple(sorted({browser_read, browser_write, 3, 4})),
                preexec_fn=map_pipe_fds,
            )
            self._install_signal_handlers()
            os.close(browser_read)
            os.close(browser_write)
            self.cdp_transport = PipeTransport(parent_write, parent_read)
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Chromium exited during startup")
                try:
                    self.browser = Browser(self.cdp_transport)
                    self.browser.connect()
                    break
                except Exception:
                    self.browser = None
                    time.sleep(0.25)
            else:
                raise RuntimeError("Chromium did not expose a CDP endpoint")

            self.page = self.browser.get_or_create_page()
            self.page.set_cookies(self.cookies)
            return self
        except Exception:
            for fd in (browser_read, browser_write, parent_write, parent_read):
                with contextlib.suppress(OSError):
                    os.close(fd)
            self._stop()
            raise

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._stop()

    def _install_signal_handlers(self) -> None:
        if (
            __import__("threading").current_thread()
            is not __import__("threading").main_thread()
        ):
            return
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            self.previous_signal_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, self._handle_signal)

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        self._stop()
        raise SystemExit(128 + signum)

    def _stop(self) -> None:
        if self.browser:
            with contextlib.suppress(Exception):
                self.browser.close()
            self.browser = None
            self.cdp_transport = None
        elif self.cdp_transport:
            with contextlib.suppress(Exception):
                self.cdp_transport.close()
            self.cdp_transport = None
        if self.process:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(self.process.pid, signal.SIGTERM)
            if self.process.poll() is None:
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(self.process.pid, signal.SIGKILL)
                    self.process.wait(timeout=5)
        self.process = None
        if self.log_handle:
            self.log_handle.close()
            self.log_handle = None
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None
        for signum, handler in self.previous_signal_handlers.items():
            signal.signal(signum, handler)
        self.previous_signal_handlers.clear()

    def run(self, command: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        if self.page is None or self.workdir is None:
            raise RuntimeError("Chromium runtime is not ready")
        return _run_page_command(self.page, command, payload or {}, self.workdir)


def _run_page_command(
    page: Any, command: str, payload: dict[str, Any], workdir: Path
) -> dict[str, Any]:
    from xhs.comment import post_comment, reply_comment
    from xhs.feed_detail import get_feed_detail
    from xhs.feeds import list_feeds
    from xhs.like_favorite import favorite_feed, like_feed, unfavorite_feed, unlike_feed
    from xhs.publish import (
        _set_original,
        _set_schedule_publish,
        _set_visibility,
        bind_products,
        click_publish_button,
        fill_publish_form,
    )
    from xhs.publish_long_article import (
        click_next_and_fill_description,
        publish_long_article,
        select_template,
    )
    from xhs.publish_video import click_publish_video_button, fill_publish_video_form
    from xhs.search import search_feeds
    from xhs.types import (
        CommentLoadConfig,
        FilterOption,
        PublishImageContent,
        PublishVideoContent,
    )
    from xhs.user_profile import get_user_profile

    if command in {"status", "whoami"}:
        page.navigate("https://www.xiaohongshu.com/explore")
        page.wait_for_load()
        page.wait_dom_stable()
        user = _read_current_user(page)
        if command == "status":
            return {"success": True, "is_logged_in": user["is_logged_in"]}
        return {"success": True, **user}
    if command == "feeds":
        feeds = list_feeds(page)
        rows = [feed.to_dict() for feed in feeds]
        for row in rows:
            row["xsecSource"] = "pc_feed"
        return {"success": True, "count": len(rows), "feeds": rows}
    if command == "search":
        filters = (
            FilterOption(**payload.get("filters", {}))
            if payload.get("filters")
            else None
        )
        feeds = search_feeds(page, payload["keyword"], filters)
        rows = [feed.to_dict() for feed in feeds]
        for row in rows:
            row["xsecSource"] = "pc_feed"
        return {"success": True, "count": len(rows), "feeds": rows}
    if command == "detail":
        config = CommentLoadConfig(
            click_more_replies=payload["click_more_replies"],
            max_replies_threshold=payload["reply_limit"],
            max_comment_items=payload["limit"],
            scroll_speed=payload["scroll_speed"],
        )
        detail = get_feed_detail(
            page,
            payload["feed_id"],
            payload["xsec_token"],
            payload["xsec_source"],
            load_all_comments=payload["load_all_comments"],
            config=config,
        )
        return {"success": True, **detail.to_dict()}
    if command == "profile":
        profile = get_user_profile(page, payload["user_id"], payload["xsec_token"])
        result = profile.to_dict()
        for row in result.get("feeds", []):
            row["xsecSource"] = "pc_note"
        return {"success": True, **result}

    if command == "publish":
        images = _prepare_images(payload["images"], workdir / "media")
        if len(images) != len(payload["images"]):
            raise RuntimeError("one or more images could not be prepared")
        content = PublishImageContent(
            title=payload["title"],
            content=payload["content"],
            tags=payload["tags"],
            image_paths=images,
            schedule_time=payload["schedule_at"] or None,
            is_original=payload["is_original"],
            visibility=payload["visibility"],
        )
        fill_publish_form(page, content)
        bind_products(page, payload["products"])
        click_publish_button(page)
        return {"success": True, "status": "published", "title": payload["title"]}

    if command == "publish-video":
        from xhs.publish_video import VIDEO_OPERATION_TIMEOUT_SECONDS

        content = PublishVideoContent(
            title=payload["title"],
            content=payload["content"],
            tags=payload["tags"],
            video_path=payload["video"],
            schedule_time=payload["schedule_at"] or None,
            visibility=payload["visibility"],
        )
        deadline = time.monotonic() + VIDEO_OPERATION_TIMEOUT_SECONDS
        fill_publish_video_form(page, content, deadline=deadline)
        bind_products(page, payload["products"])
        click_publish_video_button(page, deadline=deadline)
        return {"success": True, "status": "published", "title": payload["title"]}

    if command == "publish-long":
        images = _prepare_images(payload["images"], workdir / "media")
        if len(images) != len(payload["images"]):
            raise RuntimeError("one or more long-article images could not be prepared")
        templates = publish_long_article(
            page, payload["title"], payload["content"], images
        )
        template = payload["template"] or (templates[0] if templates else "")
        if not template or not select_template(page, template):
            raise RuntimeError(
                f"requested template is unavailable; available templates: {templates}"
            )
        click_next_and_fill_description(page, payload["description"])
        if payload["schedule_at"]:
            _set_schedule_publish(page, payload["schedule_at"])
        _set_visibility(page, payload["visibility"])
        if payload["is_original"]:
            _set_original(page)
        bind_products(page, payload["products"])
        click_publish_button(page)
        return {
            "success": True,
            "status": "published",
            "title": payload["title"],
            "template": template,
        }

    if command == "comment":
        post_comment(
            page,
            payload["feed_id"],
            payload["xsec_token"],
            payload["content"],
            payload["xsec_source"],
        )
        return {"success": True, "status": "commented"}
    if command == "reply":
        reply_comment(
            page,
            payload["feed_id"],
            payload["xsec_token"],
            payload["content"],
            comment_id=payload["comment_id"],
            user_id=payload["user_id"],
            xsec_source=payload["xsec_source"],
        )
        return {"success": True, "status": "replied"}
    if command == "like":
        return {
            "success": True,
            **like_feed(
                page, payload["feed_id"], payload["xsec_token"], payload["xsec_source"]
            ).to_dict(),
        }
    if command == "unlike":
        return {
            "success": True,
            **unlike_feed(
                page, payload["feed_id"], payload["xsec_token"], payload["xsec_source"]
            ).to_dict(),
        }
    if command == "favorite":
        return {
            "success": True,
            **favorite_feed(
                page, payload["feed_id"], payload["xsec_token"], payload["xsec_source"]
            ).to_dict(),
        }
    if command == "unfavorite":
        return {
            "success": True,
            **unfavorite_feed(
                page, payload["feed_id"], payload["xsec_token"], payload["xsec_source"]
            ).to_dict(),
        }
    raise ValueError(f"unsupported command: {command}")


def _read_current_user(page: Any) -> dict[str, Any]:
    result = page.evaluate(
        """
        (() => {
            const root = window.__INITIAL_STATE__?.user || {};
            const unwrap = value => value?.value ?? value?._value
                ?? value?._rawValue ?? value;
            const info = unwrap(root.userInfo) || {};
            return {
                is_logged_in: Boolean(unwrap(root.loggedIn)),
                user_id: info.userId || '',
                red_id: info.redId || '',
                nickname: info.nickname || '',
            };
        })()
        """
    )
    if not isinstance(result, dict):
        return {"is_logged_in": False, "user_id": "", "red_id": "", "nickname": ""}
    return result


def dry_run(
    args: argparse.Namespace,
    payload: dict[str, Any],
    digest: str,
) -> None:
    output(
        {
            "success": True,
            "dry_run": True,
            "command": args.command,
            "request": _redact_xsec_tokens(payload),
            "preview_digest": digest,
            "note": "No account change was made. Show this preview and ask the user to confirm before rerunning with --confirm.",
        }
    )


def execute(args: argparse.Namespace) -> dict:
    payload = _payload_for_command(args)
    with tempfile.TemporaryDirectory(prefix="acedata-xhs-approved-") as media_dir:
        if args.command in WRITE_COMMANDS:
            assert payload is not None
            staged_payload, canonical_payload = _stage_media_payload(
                payload, Path(media_dir)
            )
            digest = _preview_digest(args.command, canonical_payload)
            if not CONFIRM:
                dry_run(args, payload, digest)
                return {}
            if args.preview_digest != digest:
                raise RuntimeError("write payload or media changed after preview")
            allowed, reason = _unattended_write_allowed()
            if not allowed:
                raise RuntimeError(f"unattended write refused: {reason}")
            payload = staged_payload

        cookies = convert_connector_cookies(load_connector_cookie_jar())
        with DirectXiaohongshuRuntime(cookies) as runtime:
            return runtime.run(args.command, payload)


def _add_feed_reference(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--feed-id", required=True)
    parser.add_argument("--xsec-token", required=True)
    parser.add_argument(
        "--xsec-source", choices=("pc_feed", "pc_note"), default="pc_feed"
    )


def _add_write_preview(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--preview-digest", default="")


def _add_publish_text(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title")
    parser.add_argument("--title-file")
    parser.add_argument("--content")
    parser.add_argument("--content-file")
    parser.add_argument("--tags", action="append", default=[])
    parser.add_argument("--schedule-at")
    parser.add_argument("--visibility", choices=VISIBILITY_CHOICES, default="公开可见")
    parser.add_argument("--products", action="append", default=[])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="check connector login status")
    subparsers.add_parser("whoami", help="get the connected account and its notes")
    subparsers.add_parser("feeds", help="list homepage recommendations")

    search = subparsers.add_parser("search", help="search Xiaohongshu notes")
    search.add_argument("--keyword", required=True)
    search.add_argument("--sort-by", choices=SEARCH_SORT_CHOICES, default="综合")
    search.add_argument("--note-type", choices=SEARCH_TYPE_CHOICES, default="不限")
    search.add_argument("--publish-time", choices=SEARCH_TIME_CHOICES, default="不限")
    search.add_argument("--search-scope", choices=SEARCH_SCOPE_CHOICES, default="不限")
    search.add_argument("--location", choices=SEARCH_LOCATION_CHOICES, default="不限")

    detail = subparsers.add_parser("detail", help="get a note and its comments")
    _add_feed_reference(detail)
    detail.add_argument("--load-all-comments", action="store_true")
    detail.add_argument(
        "--click-more-replies", action=argparse.BooleanOptionalAction, default=True
    )
    detail.add_argument("--limit", type=int, default=20)
    detail.add_argument("--reply-limit", type=int, default=10)
    detail.add_argument(
        "--scroll-speed", choices=("slow", "normal", "fast"), default="normal"
    )

    profile = subparsers.add_parser("profile", help="get a user profile and notes")
    profile.add_argument("--user-id", required=True)
    profile.add_argument("--xsec-token", required=True)

    publish = subparsers.add_parser("publish", help="publish an image note (GATED)")
    _add_write_preview(publish)
    _add_publish_text(publish)
    publish.add_argument("--images", action="append", required=True)
    publish.add_argument("--original", action="store_true")

    publish_video = subparsers.add_parser(
        "publish-video", help="publish a video note (GATED)"
    )
    _add_write_preview(publish_video)
    _add_publish_text(publish_video)
    publish_video.add_argument("--video", required=True)

    publish_long = subparsers.add_parser(
        "publish-long", help="publish a formatted long article (GATED)"
    )
    _add_write_preview(publish_long)
    _add_publish_text(publish_long)
    publish_long.add_argument("--description")
    publish_long.add_argument("--description-file")
    publish_long.add_argument("--images", action="append", default=[])
    publish_long.add_argument("--template")
    publish_long.add_argument("--original", action="store_true")

    comment = subparsers.add_parser("comment", help="comment on a note (GATED)")
    _add_write_preview(comment)
    _add_feed_reference(comment)
    comment.add_argument("--content", required=True)

    reply = subparsers.add_parser("reply", help="reply to a note comment (GATED)")
    _add_write_preview(reply)
    _add_feed_reference(reply)
    reply.add_argument("--content", required=True)
    reply.add_argument("--comment-id")
    reply.add_argument("--user-id")

    for command in ("like", "unlike", "favorite", "unfavorite"):
        action = subparsers.add_parser(command, help=f"{command} a note (GATED)")
        _add_write_preview(action)
        _add_feed_reference(action)
    return parser


def main() -> None:
    try:
        result = execute(build_parser().parse_args(ARGV))
        if result:
            output(result)
    except Exception as error:
        fail(_sanitize_error(str(error)), code=2)


if __name__ == "__main__":
    main()

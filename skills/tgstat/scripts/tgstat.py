#!/usr/bin/env python3
"""Public TGStat research CLI with a connected Telegram username."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple, Union

DEFAULT_PUBLIC_BASE = "https://tgstat.com"
# Public tgstat.com sits behind Cloudflare, so pages are fetched through the
# platform WebExtrator render service (headless Chromium) instead of directly.
RENDER_ENDPOINT = os.environ.get("TGSTAT_RENDER_ENDPOINT", "https://api.acedata.cloud/webextrator/render")
RENDER_TOKEN_ENV = "TGSTAT_RENDER_TOKEN"
RENDER_DELAY_SECONDS = 2
RENDER_BLOCK_RESOURCES = ["image", "font", "media", "stylesheet"]
PUBLIC_USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,}")
TGSTAT_HOST_RE = re.compile(r"^(?:[a-z]{2,3}\.)?tgstat\.com$", re.IGNORECASE)
TGSTAT_INPUT_HOST_RE = re.compile(r"^(?:(?:[a-z]{2,3}\.)?tgstat\.com|tgstat\.ru)$", re.IGNORECASE)
# The /stat suffix is optional: the summary metrics live on the main entity page.
ENTITY_PATH_RE = re.compile(r"/(channel|chat)/(@[A-Za-z0-9_]{3,}|id\d+)(?:/stat)?/?", re.IGNORECASE)


class TGStatError(RuntimeError):
    pass


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _metric_key(label: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return key or "value"


def _metric_number(value: str) -> Optional[Union[int, float]]:
    compact = _compact(value).replace(" ", "").replace(",", "")
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)([kmb])?", compact, re.IGNORECASE)
    if not match:
        return None
    number = float(match.group(1))
    multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}.get(
        (match.group(2) or "").lower(), 1
    )
    result = number * multiplier
    return int(result) if result.is_integer() else result


def _entity_from_url(url: str) -> Optional[Tuple[str, str]]:
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    match = ENTITY_PATH_RE.fullmatch(path)
    if not match:
        return None
    return match.group(1).lower(), match.group(2)


def _safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _safe_error_body(body: str) -> str:
    return _compact(body)[:200]


def _validate_request_url(url: str, initial_host: Optional[str] = None) -> None:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https":
        raise TGStatError("TGStat requests and redirects must use HTTPS")
    allowed_from = initial_host or host
    if TGSTAT_HOST_RE.fullmatch(allowed_from):
        if not TGSTAT_HOST_RE.fullmatch(host):
            raise TGStatError(f"TGStat redirected to an unexpected host: {host}")
    else:
        raise TGStatError(f"unsupported TGStat request host: {allowed_from}")


class RankingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: List[dict] = []
        self.current: Optional[dict] = None
        self.card_div_depth = 0
        self.capture: Optional[dict] = None
        self.pending_metric: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = set(attr.get("class", "").split())
        if tag == "div" and "peer-item-row" in classes and self.current is None:
            self.current = {"metrics": {}, "metrics_display": {}}
            self.card_div_depth = 1
            return
        if self.current is None:
            return
        if tag == "div":
            self.card_div_depth += 1
        if self.capture is not None:
            self.capture["depth"] += 1
            return

        if tag == "a" and attr.get("href"):
            entity = _entity_from_url(attr["href"])
            hostname = urllib.parse.urlparse(attr["href"]).hostname or ""
            if entity and TGSTAT_HOST_RE.fullmatch(hostname):
                peer_type, identifier = entity
                self.current.setdefault("type", peer_type)
                self.current.setdefault("identifier", identifier)
                self.current.setdefault("tgstat_url", attr["href"])

        kind = ""
        if tag == "div" and "ribbon" in classes:
            kind = "rank"
        elif tag == "div" and {"text-truncate", "font-16", "text-dark"}.issubset(classes):
            if self.current.get("tgstat_url") and not self.current.get("title"):
                kind = "title"
        elif tag == "span" and {"border", "rounded", "bg-light"}.issubset(classes):
            if self.current.get("tgstat_url") and not self.current.get("category"):
                kind = "category"
        elif tag == "h4":
            kind = "metric_value"
        elif tag == "div" and {"text-muted", "text-truncate"}.issubset(classes):
            if self.pending_metric is not None:
                kind = "metric_label"
        if kind:
            self.capture = {"tag": tag, "kind": kind, "depth": 1, "parts": []}

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        if self.capture is not None:
            self.capture["depth"] -= 1
            if self.capture["depth"] == 0:
                self._finish_capture()
        if tag == "div":
            self.card_div_depth -= 1
            if self.card_div_depth == 0:
                self._finish_card()

    def handle_data(self, data: str) -> None:
        if self.capture is not None:
            self.capture["parts"].append(data)

    def _finish_capture(self) -> None:
        assert self.current is not None and self.capture is not None
        kind = self.capture["kind"]
        value = _compact("".join(self.capture["parts"]))
        self.capture = None
        if not value:
            return
        if kind == "rank":
            match = re.search(r"\d+", value)
            if match:
                self.current["rank"] = int(match.group())
        elif kind in {"title", "category"}:
            self.current[kind] = value
        elif kind == "metric_value":
            self.pending_metric = value
        elif kind == "metric_label" and self.pending_metric is not None:
            key = _metric_key(value)
            display = self.pending_metric
            self.current["metrics_display"][key] = display
            number = _metric_number(display)
            self.current["metrics"][key] = number if number is not None else display
            self.pending_metric = None

    def _finish_card(self) -> None:
        assert self.current is not None
        item = self.current
        identifier = item.get("identifier", "")
        if identifier.startswith("@"):
            item["username"] = identifier
            item["telegram_url"] = f"https://t.me/{identifier[1:]}"
        else:
            item["username"] = None
            item["telegram_url"] = None
        if item.get("tgstat_url") and item.get("title"):
            self.items.append(item)
        self.current = None
        self.card_div_depth = 0
        self.capture = None
        self.pending_metric = None


class DetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: Dict[str, str] = {}
        self.capture: Optional[dict] = None
        self.pending_metric: Optional[str] = None
        self.metrics: Dict[str, Union[int, float, str]] = {}
        self.metrics_display: Dict[str, str] = {}
        self.text_parts: List[str] = []
        self._tag_index = 0
        self._pending_at = -100

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        self._tag_index += 1
        if tag == "meta":
            key = (attr.get("property") or attr.get("name") or "").lower()
            if key in {"og:title", "og:description", "description"} and attr.get("content"):
                self.meta[key] = _compact(attr["content"])
        if self.capture is not None:
            self.capture["depth"] += 1
            return
        classes = set(attr.get("class", "").split())
        kind = ""
        if tag == "title":
            kind = "title"
        elif tag in {"h2", "h3", "h4"} and "text-dark" in classes:
            kind = "metric_value"
        elif tag == "div" and {"text-uppercase", "font-12"}.issubset(classes):
            # Only pair a label that sits right after its value inside the same
            # stat card, so a stray numeric heading can't grab a distant label.
            if self.pending_metric is not None and self._tag_index - self._pending_at <= 6:
                kind = "metric_label"
        if kind:
            self.capture = {"kind": kind, "depth": 1, "parts": []}

    def handle_endtag(self, tag: str) -> None:
        if self.capture is None:
            return
        self.capture["depth"] -= 1
        if self.capture["depth"] != 0:
            return
        kind = self.capture["kind"]
        value = _compact("".join(self.capture["parts"]))
        self.capture = None
        if kind == "title" and value:
            self.meta.setdefault("title", value)
        elif kind == "metric_value" and _metric_number(value) is not None:
            self.pending_metric = value
            self._pending_at = self._tag_index
        elif kind == "metric_label" and value and self.pending_metric is not None:
            number = _metric_number(self.pending_metric)
            if number is not None:
                key = _metric_key(value)
                self.metrics_display[key] = self.pending_metric
                self.metrics[key] = number
            self.pending_metric = None

    def handle_data(self, data: str) -> None:
        text = _compact(data)
        if text:
            self.text_parts.append(text)
        if self.capture is not None:
            self.capture["parts"].append(data)


def parse_rankings_html(html: str) -> List[dict]:
    parser = RankingParser()
    parser.feed(html)
    return parser.items


def parse_detail_html(html: str, url: str) -> dict:
    parser = DetailParser()
    parser.feed(html)
    text = " ".join(parser.text_parts)
    entity = _entity_from_url(url)
    title = parser.meta.get("og:title") or parser.meta.get("title")
    # A real entity page echoes the requested @username / id in its title or
    # emits an og:title; tgstat error / search / interstitial pages do neither
    # (the bare "TGStat" brand in <title> is not proof the entity exists).
    identifier_token = str(entity[1]).casefold() if entity else ""
    recognized = bool(
        entity and title and (identifier_token in title.casefold() or bool(parser.meta.get("og:title")))
    )
    lowered_title = (title or "").casefold()
    if "not found" in lowered_title or "404" in lowered_title:
        status = "not_found"
    elif "authentication required" in text.lower():
        status = "restricted"
    elif recognized:
        status = "ok"
    else:
        status = "unrecognized"
    result = {
        "status": status,
        "type": entity[0] if entity else None,
        "identifier": entity[1] if entity else None,
        "title": title,
        "description": parser.meta.get("og:description") or parser.meta.get("description"),
        "metrics": parser.metrics,
        "metrics_display": parser.metrics_display,
        "tgstat_url": url,
    }
    identifier = result["identifier"]
    result["telegram_url"] = f"https://t.me/{identifier[1:]}" if isinstance(identifier, str) and identifier.startswith("@") else None
    return result


def _json_out(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _render_token() -> str:
    token = os.environ.get(RENDER_TOKEN_ENV, "").strip()
    if not token:
        raise TGStatError("TGStat rendering is not configured: the platform render token is missing")
    return token


# Render statuses worth retrying: Cloudflare/anti-bot interstitials surface as
# 422 antibot_blocked, and the render service can transiently 429/5xx.
_RETRYABLE_RENDER_STATUS = frozenset({422, 425, 429, 500, 502, 503, 504})
_RENDER_ATTEMPTS = 3


def _request_with_url(url: str, timeout: int) -> Tuple[str, str]:
    # Public tgstat.com is behind Cloudflare; render it through the platform
    # WebExtrator service (headless Chromium) rather than fetching directly.
    # Anti-bot blocks are intermittent, so retry with a longer settle and a
    # cache bypass before giving up.
    _validate_request_url(url)
    render_timeout = max(20, min(timeout, 45))
    token = _render_token()
    last_reason = ""
    for attempt in range(_RENDER_ATTEMPTS):
        payload = json.dumps(
            {
                "url": url,
                "wait_until": "domcontentloaded",
                "delay": RENDER_DELAY_SECONDS + 2 * attempt,
                "timeout": render_timeout,
                "block_resources": RENDER_BLOCK_RESOURCES,
                "bypass_cache": attempt > 0,
            }
        ).encode()
        request = urllib.request.Request(
            RENDER_ENDPOINT,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=render_timeout + 75) as response:
                envelope = json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            if exc.code in _RETRYABLE_RENDER_STATUS or "antibot" in body.lower():
                last_reason = f"render blocked (HTTP {exc.code}): {_safe_error_body(body)}"
                _render_backoff(attempt)
                continue
            raise TGStatError(f"render service HTTP {exc.code}: {_safe_error_body(body)}") from exc
        except urllib.error.URLError as exc:
            last_reason = f"render service unreachable: {_safe_error_body(str(exc.reason))}"
            _render_backoff(attempt)
            continue
        except json.JSONDecodeError as exc:
            raise TGStatError(f"render service returned invalid JSON: {_safe_error_body(str(exc))}") from exc
        render = envelope.get("data") if isinstance(envelope, dict) else None
        if isinstance(render, dict):
            html = render.get("html") or ""
            final_url = render.get("finalUrl") or render.get("url") or url
            if html.strip() and "challenge-platform" not in html and "Just a moment" not in html:
                final_host = urllib.parse.urlparse(final_url).hostname or ""
                if not (TGSTAT_HOST_RE.fullmatch(final_host) or TGSTAT_INPUT_HOST_RE.fullmatch(final_host)):
                    raise TGStatError(f"render redirected to an unexpected host: {final_host}")
                return html, final_url
            last_reason = f"empty or interstitial render (upstream status {render.get('status')})"
        else:
            last_reason = "render service returned no page data"
        _render_backoff(attempt)
    raise TGStatError(f"could not render {_safe_url(url)}: {last_reason}")


def _render_backoff(attempt: int) -> None:
    # Skip the wait after the final attempt; give Cloudflare a moment otherwise.
    if attempt < _RENDER_ATTEMPTS - 1:
        time.sleep(min(2 + 2 * attempt, 6))


def _request(url: str, timeout: int) -> str:
    return _request_with_url(url, timeout)[0]


def _public_base(value: str) -> str:
    parsed = urllib.parse.urlparse(value if "://" in value else f"https://{value}")
    if parsed.scheme != "https" or not parsed.hostname or not TGSTAT_HOST_RE.fullmatch(parsed.hostname):
        raise TGStatError("public host must be tgstat.com or a regional *.tgstat.com host")
    return f"https://{parsed.hostname}"


def _normalize_target(target: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    target = target.strip()
    if target.startswith("http://") or target.startswith("https://"):
        parsed = urllib.parse.urlparse(target)
        if parsed.scheme != "https":
            raise TGStatError("target URL must use HTTPS")
        if parsed.hostname and TGSTAT_INPUT_HOST_RE.fullmatch(parsed.hostname):
            entity = _entity_from_url(target)
            if not entity:
                raise TGStatError("TGStat target must be a channel or chat statistics URL")
            identifier = entity[1]
            canonical_url = target
            if parsed.hostname.casefold() == "tgstat.ru":
                canonical_url = urllib.parse.urlunsplit(("https", "tgstat.com", parsed.path, "", ""))
            return identifier, entity[0], canonical_url
        if parsed.hostname in {"t.me", "www.t.me"}:
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) != 1 or not PUBLIC_USERNAME_RE.fullmatch(parts[0]):
                raise TGStatError("t.me target must be a public username link, not an invite or message link")
            return f"@{parts[0]}", None, None
        raise TGStatError("target URL must be a tgstat.com entity or t.me link")
    if target.startswith("@") and PUBLIC_USERNAME_RE.fullmatch(target[1:]):
        return target, None, None
    if re.fullmatch(r"\d+", target):
        return f"id{target}", None, None
    if re.fullmatch(r"id\d+", target, re.IGNORECASE):
        return f"id{target[2:]}", None, None
    if PUBLIC_USERNAME_RE.fullmatch(target):
        return f"@{target}", None, None
    raise TGStatError("target must be @username, a t.me link, TGStat entity URL, or id<number>")


def _connected_username() -> str:
    value = os.environ.get("TGSTAT_USERNAME", "").strip()
    if not value:
        raise TGStatError("TGSTAT_USERNAME is not configured; reconnect TGStat with a public Telegram username")
    identifier, _, _ = _normalize_target(value)
    if not identifier or not identifier.startswith("@"):
        raise TGStatError("TGSTAT_USERNAME must be a public Telegram username such as @durov")
    return identifier


def _target_or_profile(target: str) -> str:
    return target.strip() or _connected_username()


def command_profile(args: argparse.Namespace) -> None:
    username = _connected_username()
    _json_out(
        {
            "mode": "public",
            "username": username,
            "telegram_url": f"https://t.me/{username[1:]}",
            "verified": False,
        }
    )


def _web_queries(query: str, peer_type: str, language: str, country: str) -> List[str]:
    suffix = " ".join(part for part in (language, country) if part).strip()
    quoted = f'"{query}"'
    kinds = [peer_type] if peer_type != "all" else ["chat", "channel"]
    queries = [f"site:tgstat.com/{kind}/ {quoted} {suffix}".strip() for kind in kinds]
    queries.extend(f"site:t.me/ {quoted} {kind} {suffix}".strip() for kind in kinds)
    return queries


def command_search(args: argparse.Namespace) -> None:
    query = args.query.strip()
    if len(query) < 3:
        raise TGStatError("query must contain at least 3 characters")
    _json_out(
        {
            "mode": "public",
            "query": query,
            "requires_web_search": True,
            "web_queries": _web_queries(query, args.type, args.language, args.country),
            "instructions": (
                "Run web_search for each query, keep only tgstat.com and t.me results, "
                "deduplicate by username, then inspect shortlisted TGStat URLs with the info command."
            ),
            "limitations": "TGStat's own keyword-search results require sign-in; public web indexes may be incomplete.",
        }
    )


def _ranking_fallback(url: str, peer_type: str, query: str, reason: str) -> None:
    subject = query.strip() or ("Telegram channels" if peer_type == "channel" else "Telegram groups")
    _json_out(
        {
            "mode": "public",
            "status": "unavailable",
            "source": url,
            "reason": reason,
            "requires_web_fetch": True,
            "web_fetch_url": url,
            "requires_web_search": True,
            "web_queries": [
                f'site:tgstat.com/{peer_type}/ "{subject}"',
                f'site:t.me/ "{subject}"',
            ],
            "limitations": "Fallback results are web-index discoveries, not an authoritative TGStat ranking.",
        }
    )


def command_rankings(args: argparse.Namespace) -> None:
    base = _public_base(args.host)
    plural = "channels" if args.type == "channel" else "chats"
    url = f"{base}/ratings/{plural}"
    try:
        html = _request(url, args.timeout)
    except TGStatError as exc:
        _ranking_fallback(url, args.type, args.query, str(exc))
        return
    normalized_html = html.casefold()
    if "authentication required" in normalized_html or "too many requests" in normalized_html:
        _ranking_fallback(url, args.type, args.query, "TGStat returned an authentication or rate-limit interstitial")
        return
    items = parse_rankings_html(html)
    if not items:
        _ranking_fallback(url, args.type, args.query, "TGStat ranking HTML was empty or not recognized")
        return
    if args.query:
        needle = args.query.casefold()
        items = [
            item
            for item in items
            if needle in " ".join(str(item.get(key) or "") for key in ("title", "username", "category")).casefold()
        ]
    _json_out({"mode": "public", "source": url, "count": min(len(items), args.limit), "items": items[: args.limit]})


def _public_info(args: argparse.Namespace, target: str, peer_type: str) -> dict:
    identifier, inferred_type, exact_url = _normalize_target(target)
    types = [inferred_type] if inferred_type else ([peer_type] if peer_type != "auto" else ["channel", "chat"])
    if exact_url:
        urls = [re.sub(r"/stat/?$", "", exact_url)]
    else:
        urls = [f"{_public_base(args.host)}/{kind}/{identifier}" for kind in types]
    errors: List[str] = []
    for url in urls:
        if not url:
            continue
        try:
            html, final_url = _request_with_url(url, args.timeout)
            final_host = urllib.parse.urlparse(final_url).hostname or ""
            if not (TGSTAT_HOST_RE.fullmatch(final_host) or TGSTAT_INPUT_HOST_RE.fullmatch(final_host)):
                raise TGStatError(f"TGStat redirected to an unexpected host: {final_host}")
            result = parse_detail_html(html, final_url)
        except TGStatError as exc:
            errors.append(str(exc))
            continue
        if result["status"] == "ok" and result.get("title"):
            if not result["metrics"] and result.get("type") in {"channel", "chat"}:
                plural = "channels" if result["type"] == "channel" else "chats"
                ranking_url = f"{_public_base(args.host)}/ratings/{plural}"
                try:
                    ranking_items = parse_rankings_html(_request(ranking_url, args.timeout))
                except TGStatError:
                    ranking_items = []
                normalized = str(result.get("identifier") or "").casefold()
                snapshot = next(
                    (item for item in ranking_items if str(item.get("identifier") or "").casefold() == normalized),
                    None,
                )
                if snapshot:
                    result["metrics"] = snapshot["metrics"]
                    result["metrics_display"] = snapshot["metrics_display"]
                    result["ranking_snapshot"] = {
                        "rank": snapshot.get("rank"),
                        "category": snapshot.get("category"),
                        "source": ranking_url,
                    }
            return result
        errors.append(f"{result['status']} public page: {url}")
    raise TGStatError("; ".join(errors) or "could not resolve target on public TGStat pages")


def command_info(args: argparse.Namespace) -> None:
    _json_out({"mode": "public", **_public_info(args, _target_or_profile(args.target), args.type)})


def command_stat(args: argparse.Namespace) -> None:
    _json_out(
        {"mode": "public", "limited_metrics": True, **_public_info(args, _target_or_profile(args.target), args.type)}
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("TGSTAT_PUBLIC_HOST", DEFAULT_PUBLIC_BASE))
    parser.add_argument("--timeout", type=int, default=45)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("profile").set_defaults(func=command_profile)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--type", choices=("channel", "chat", "all"), default="all")
    search.add_argument("--language", default="")
    search.add_argument("--country", default="")
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=command_search)

    rankings = sub.add_parser("rankings")
    rankings.add_argument("--type", choices=("channel", "chat"), default="channel")
    rankings.add_argument("--query", default="", help="Filter the public top list locally")
    rankings.add_argument("--limit", type=int, default=20)
    rankings.set_defaults(func=command_rankings)

    for name, func in (("info", command_info), ("stat", command_stat)):
        command = sub.add_parser(name)
        command.add_argument("target", nargs="?", default="")
        command.add_argument("--type", choices=("auto", "channel", "chat"), default="auto")
        command.set_defaults(func=func)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except TGStatError as exc:
        _json_out({"error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
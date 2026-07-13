#!/usr/bin/env python3
"""Public TGStat research CLI with a connected Telegram username."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple, Union

DEFAULT_PUBLIC_BASE = "https://tgstat.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)
PUBLIC_USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,}")
TGSTAT_HOST_RE = re.compile(r"^(?:[a-z]{2,3}\.)?tgstat\.com$", re.IGNORECASE)
TGSTAT_INPUT_HOST_RE = re.compile(r"^(?:(?:[a-z]{2,3}\.)?tgstat\.com|tgstat\.ru)$", re.IGNORECASE)
ENTITY_PATH_RE = re.compile(r"/(channel|chat)/(@[A-Za-z0-9_]{3,}|id\d+)/stat/?", re.IGNORECASE)


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


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, initial_host: str) -> None:
        super().__init__()
        self.initial_host = initial_host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_request_url(newurl, self.initial_host)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_url(request: urllib.request.Request, timeout: int):
    initial_url = request.full_url
    _validate_request_url(initial_url)
    initial_host = urllib.parse.urlsplit(initial_url).hostname or ""
    opener = urllib.request.build_opener(SafeRedirectHandler(initial_host))
    return opener.open(request, timeout=timeout)


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

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
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
        elif tag == "h4":
            kind = "metric_value"
        elif tag == "div" and {"text-muted", "text-truncate"}.issubset(classes):
            if self.pending_metric is not None:
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
        elif kind == "metric_value" and value:
            self.pending_metric = value
        elif kind == "metric_label" and value and self.pending_metric is not None:
            key = _metric_key(value)
            self.metrics_display[key] = self.pending_metric
            number = _metric_number(self.pending_metric)
            self.metrics[key] = number if number is not None else self.pending_metric
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
    recognized = bool(entity and parser.meta.get("og:title") and title and "tgstat" in title.casefold())
    result = {
        "status": (
            "restricted"
            if "authentication required" in text.lower()
            else "ok" if recognized else "unrecognized"
        ),
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


def _request_with_url(
    url: str, timeout: int, data: Optional[bytes] = None, headers: Optional[dict] = None
) -> Tuple[str, str]:
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        **(headers or {}),
    }
    request = urllib.request.Request(url, data=data, headers=request_headers)
    try:
        with _open_url(request, timeout) as response:
            return response.read().decode("utf-8", "replace"), response.geturl()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise TGStatError(f"HTTP {exc.code} from {_safe_url(url)}: {_safe_error_body(body)}") from exc
    except urllib.error.URLError as exc:
        raise TGStatError(f"network error for {_safe_url(url)}: {_safe_error_body(str(exc.reason))}") from exc


def _request(url: str, timeout: int, data: Optional[bytes] = None, headers: Optional[dict] = None) -> str:
    return _request_with_url(url, timeout, data, headers)[0]


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
    urls = [exact_url] if exact_url else [f"{_public_base(args.host)}/{kind}/{identifier}/stat" for kind in types]
    errors: List[str] = []
    for url in urls:
        if not url:
            continue
        try:
            html, final_url = _request_with_url(url, args.timeout)
            final_host = urllib.parse.urlparse(final_url).hostname or ""
            if not TGSTAT_HOST_RE.fullmatch(final_host):
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
        errors.append(f"restricted or empty public page: {url}")
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
    parser.add_argument("--timeout", type=int, default=30)
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
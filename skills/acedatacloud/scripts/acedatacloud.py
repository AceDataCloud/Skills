#!/usr/bin/env python3
"""AceDataCloud platform management CLI (self-contained, stdlib only).

Talks to the management API at https://platform.acedata.cloud/api/v1 using a
platform token (ACEDATACLOUD_PLATFORM_TOKEN). Read commands are always safe;
write commands are dry-run unless --yes is passed.

Examples:
    python3 platform.py balance
    python3 platform.py usage-summary --days 30
    python3 platform.py keys
    python3 platform.py create-key --application <app-id> --name ci --yes
    python3 platform.py send-announcement --title T --content C --yes
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = os.environ.get("PLATFORM_API_BASE_URL", "https://platform.acedata.cloud")
SECRET_KEYS = {"token", "password", "pay_url", "pay_id"}


def _die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _token(args: argparse.Namespace) -> str:
    token = args.token or os.environ.get("ACEDATACLOUD_PLATFORM_TOKEN", "")
    if not token:
        _die(
            "no platform token. Set ACEDATACLOUD_PLATFORM_TOKEN or pass --token.\n"
            "Create one at https://platform.acedata.cloud/console/platform-tokens"
        )
    return token


def _request(args: argparse.Namespace, method: str, path: str,
             params: dict | None = None, body: dict | None = None,
             auth_required: bool = True, lang: str | None = None) -> tuple[int, object]:
    base = args.base_url.rstrip("/")
    url = f"{base}/api/v1{path}"
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"accept": "application/json", "content-type": "application/json"}
    if lang:
        headers["accept-language"] = lang
    token = args.token or os.environ.get("ACEDATACLOUD_PLATFORM_TOKEN", "")
    if not token and auth_required:
        token = _token(args)  # dies with a helpful message
    if token:
        headers["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw
    except urllib.error.URLError as e:
        _die(f"network error: {e.reason}")
    return 0, None  # unreachable


def _get_all(args: argparse.Namespace, path: str, params: dict | None = None,
             page: int = 200, cap: int = 2000) -> tuple[int, list]:
    """Fetch every page of a {count, items} list endpoint (capped)."""
    base = dict(params or {})
    out: list = []
    offset = 0
    total = 0
    while len(out) < cap:
        base.update({"limit": page, "offset": offset})
        status, payload = _request(args, "GET", path, base)
        _check_ok(status, payload)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        total = payload.get("count", 0) if isinstance(payload, dict) else 0
        out.extend(items)
        offset += page
        if not items or offset >= total:
            break
    return total, out


def _mask(obj: object, reveal: bool) -> object:
    if reveal:
        return obj
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in SECRET_KEYS and isinstance(v, str) and v:
                out[k] = v[:10] + "…" + f"({len(v)} chars)" if len(v) > 10 else "***"
            else:
                out[k] = _mask(v, reveal)
        return out
    if isinstance(obj, list):
        return [_mask(x, reveal) for x in obj]
    return obj


def _emit(args: argparse.Namespace, payload: object, rows: list[tuple] | None = None,
          headers: tuple | None = None, force_reveal: bool = False) -> None:
    reveal = force_reveal or getattr(args, "reveal", False)
    if args.json:
        print(json.dumps(_mask(payload, reveal), ensure_ascii=False, indent=2))
        return
    if rows is not None and headers is not None:
        widths = [len(h) for h in headers]
        for r in rows:
            for i, cell in enumerate(r):
                widths[i] = max(widths[i], len(str(cell)))
        line = "  ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
        print(line)
        print("  ".join("-" * widths[i] for i in range(len(headers))))
        for r in rows:
            print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))
    else:
        print(json.dumps(_mask(payload, reveal), ensure_ascii=False, indent=2))


def _check_ok(status: int, payload: object) -> None:
    if status >= 400:
        msg = payload
        if isinstance(payload, dict):
            err = payload.get("error")
            msg = (err.get("message") if isinstance(err, dict) else err) or payload.get("detail") or payload
        _die(f"HTTP {status}: {msg}", code=2)


def _since(days: int | None) -> str | None:
    if not days:
        return None
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- read commands -------------------------------------------------------

def cmd_balance(args):
    status, payload = _request(args, "GET", "/applications/", {"limit": args.limit})
    _check_ok(status, payload)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    rows = [(
        it.get("service_id", "")[:8],
        it.get("remaining_amount"),
        it.get("used_amount"),
        it.get("scope"),
        it.get("id", "")[:8],
    ) for it in items]
    _emit(args, payload, rows, ("service", "remaining", "used", "scope", "app_id"))


def cmd_services(args):
    if args.search:
        total, items = _get_all(args, "/services/")
        s = args.search.lower()
        items = [it for it in items if s in (it.get("alias") or "").lower() or s in (it.get("title") or "").lower()]
        payload = {"count": len(items), "items": items}
        if not args.json:
            print(f"# {len(items)} match '{args.search}' / {total} total services\n")
    else:
        status, payload = _request(args, "GET", "/services/", {"limit": args.limit})
        _check_ok(status, payload)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not args.json:
            print(f"# {len(items)} shown / {payload.get('count')} total services\n")
    rows = [(it.get("alias"), (it.get("title") or "")[:28], it.get("unit"), it.get("applied_count"), it.get("id", "")[:8]) for it in items]
    _emit(args, payload, rows, ("alias", "title", "unit", "applied", "id"))


def cmd_usage(args):
    params = {"limit": args.limit, "status_code": args.status_code,
              "api_id": args.api, "created_at_from": _since(args.days)}
    status, payload = _request(args, "GET", "/usage/apis/", params)
    _check_ok(status, payload)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    rows = [(
        ((it.get("api") or {}).get("title") or "")[:30],
        it.get("status_code"),
        it.get("deducted_amount"),
        it.get("elapsed"),
        (it.get("created_at") or "")[:19],
    ) for it in items]
    _emit(args, payload, rows, ("api", "status", "credits", "elapsed", "created_at"))


def cmd_usage_summary(args):
    params = {"created_at_from": _since(args.days or 30), "api_id": args.api}
    status, payload = _request(args, "GET", "/usage/apis/aggregate/", params)
    _check_ok(status, payload)
    apis = payload.get("apis", {}) if isinstance(payload, dict) else {}
    by_api: dict[str, float] = {}
    for it in (payload.get("items", []) if isinstance(payload, dict) else []):
        by_api[it.get("api_id")] = by_api.get(it.get("api_id"), 0.0) + (it.get("amount") or 0.0)
    rows = sorted(((apis.get(k, {}).get("title", k or "?")[:36], round(v, 4)) for k, v in by_api.items()),
                  key=lambda r: -r[1])
    if not args.json:
        print(f"# total spend: {payload.get('total')} Credits over last {args.days or 30} days\n")
    _emit(args, payload, rows, ("api", "credits"))


def cmd_keys(args):
    status, payload = _request(args, "GET", "/credentials/", {"limit": args.limit, "application_id": args.application})
    _check_ok(status, payload)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    rows = [(
        it.get("id", "")[:8],
        it.get("name") or "-",
        it.get("type"),
        it.get("limited_amount"),
        it.get("used_amount"),
        (it.get("created_at") or "")[:10],
    ) for it in items]
    _emit(args, payload, rows, ("id", "name", "type", "limit", "used", "created"))


def cmd_orders(args):
    status, payload = _request(args, "GET", "/orders/", {"limit": args.limit, "state": args.state, "pay_way": args.pay_way})
    _check_ok(status, payload)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    rows = [(
        it.get("id", "")[:8],
        (it.get("description") or "")[:26],
        it.get("price"),
        it.get("state"),
        it.get("pay_way"),
        (it.get("created_at") or "")[:10],
    ) for it in items]
    _emit(args, payload, rows, ("id", "description", "price", "state", "pay_way", "created"))


def cmd_tokens(args):
    status, payload = _request(args, "GET", "/platform-tokens/", {"limit": args.limit})
    _check_ok(status, payload)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    rows = [(it.get("id", "")[:8], (it.get("used_at") or "never")[:19], (it.get("created_at") or "")[:19]) for it in items]
    _emit(args, payload, rows, ("id", "last_used", "created"))


def cmd_models(args):
    status, payload = _request(args, "GET", "/models/")
    _check_ok(status, payload)
    data = payload.get("data", []) if isinstance(payload, dict) else []
    rows = [(m.get("id"), (m.get("label") or "")[:24], m.get("owned_by"), m.get("type"), ",".join(m.get("capabilities") or [])) for m in data]
    _emit(args, payload, rows, ("id", "label", "owned_by", "type", "capabilities"))


def cmd_announcements(args):
    status, payload = _request(args, "GET", "/announcements/", {"limit": args.limit})
    _check_ok(status, payload)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    rows = [(it.get("id", "")[:8], (it.get("title") or "")[:40], it.get("rank"), (it.get("publish_at") or "")[:10]) for it in items]
    _emit(args, payload, rows, ("id", "title", "rank", "publish_at"))


# ---- public catalog / docs commands (no token required) ------------------

def cmd_service(args):
    status, payload = _request(args, "GET", f"/services/{args.service}", auth_required=False)
    _check_ok(status, payload)
    if not args.json and isinstance(payload, dict):
        print(f"# {payload.get('title')} ({payload.get('alias')}) — unit {payload.get('unit')}, "
              f"free {payload.get('free_amount')}; {len(payload.get('apis') or [])} APIs, "
              f"{len(payload.get('packages') or [])} packages\n")
    _emit(args, payload)


def cmd_apis(args):
    status, payload = _request(args, "GET", "/apis/",
                               {"service": args.service, "stage": ["Beta", "Production"]},
                               auth_required=False)
    _check_ok(status, payload)
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    items = [a for a in (items or []) if isinstance(a, dict) and a.get("stage") in ("Beta", "Production")]
    rows = [(a.get("method"), a.get("path"), (a.get("title") or "")[:36], a.get("stage")) for a in items]
    _emit(args, {"count": len(items), "items": items}, rows, ("method", "path", "title", "stage"))


def cmd_spec(args):
    if not args.path and not args.service:
        _die("provide --path (e.g. /suno/audios) or --service")
    status, payload = _request(args, "GET", "/apis/",
                               {"service": args.service, "path": args.path,
                                "stage": ["Beta", "Production"]}, auth_required=False)
    _check_ok(status, payload)
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    items = [a for a in (items or []) if isinstance(a, dict) and a.get("stage") in ("Beta", "Production")]
    if args.path:
        items = [a for a in items if args.path in (a.get("path"), a.get("path2"))]
    specs = [{"name": a.get("name"), "path": a.get("path"), "method": a.get("method"),
              "definition": a.get("definition")} for a in items if a.get("definition")]
    if not specs:
        _die("no public API spec matched")
    print(json.dumps(specs, ensure_ascii=False, indent=2))


def cmd_pricing(args):
    total, items = _get_all_public(args, "/services/")
    rows = []
    for s in items:
        if args.service and s.get("alias") != args.service and str(s.get("id")) != args.service:
            continue
        rows.append((s.get("alias"), (s.get("title") or "")[:26], s.get("unit"), s.get("free_amount"), json.dumps(s.get("cost"), ensure_ascii=False)[:40]))
    _emit(args, {"items": [r for r in items if not args.service or r.get("alias") == args.service]},
          rows, ("alias", "title", "unit", "free", "cost"))


def cmd_docs_search(args):
    status, payload = _request(args, "GET", "/search/",
                               {"q": args.query, "lang": args.lang, "limit": args.limit},
                               auth_required=False)
    _check_ok(status, payload)
    results = payload.get("results", payload) if isinstance(payload, dict) else payload
    rows = [((r.get("title") or r.get("name") or "")[:44], r.get("alias") or r.get("id", "")) for r in (results or []) if isinstance(r, dict)]
    _emit(args, results, rows, ("title", "alias"))


def cmd_docs_list(args):
    status, payload = _request(args, "GET", "/documents/",
                               {"private": "false", "limit": args.limit, "offset": args.offset, "type": args.type},
                               auth_required=False)
    _check_ok(status, payload)
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    rows = [(d.get("alias"), (d.get("title") or d.get("name") or "")[:42], d.get("type")) for d in (items or []) if isinstance(d, dict)]
    _emit(args, {"items": items}, rows, ("alias", "title", "type"))


def cmd_doc(args):
    status, payload = _request(args, "GET", f"/documents/{args.ref}", auth_required=False, lang=args.lang)
    _check_ok(status, payload)
    if not args.json and isinstance(payload, dict):
        print(f"# {payload.get('title')} ({payload.get('alias')})\n")
        print(payload.get("content") or "")
        return
    _emit(args, payload)


def cmd_distributions(args):
    s_status, s_payload = _request(args, "GET", "/distribution-statuses/", {"limit": 1})
    _check_ok(s_status, s_payload)
    h_status, h_payload = _request(args, "GET", "/distribution-histories/", {"limit": args.limit})
    _check_ok(h_status, h_payload)
    s_items = s_payload.get("items", []) if isinstance(s_payload, dict) else []
    h_items = h_payload.get("items", []) if isinstance(h_payload, dict) else []
    _emit(args, {"status": s_items[0] if s_items else None, "histories": h_items},
          [( (it.get("created_at") or "")[:10], it.get("price"), it.get("reward")) for it in h_items],
          ("date", "price", "reward"))


def _get_all_public(args: argparse.Namespace, path: str, page: int = 200, cap: int = 2000) -> tuple[int, list]:
    out: list = []
    offset = 0
    total = 0
    while len(out) < cap:
        status, payload = _request(args, "GET", path, {"private": "false", "limit": page, "offset": offset}, auth_required=False)
        _check_ok(status, payload)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        total = payload.get("count", 0) if isinstance(payload, dict) else 0
        out.extend(items)
        offset += page
        if not items or offset >= total:
            break
    return total, out


# ---- write commands (gated by --yes) -------------------------------------

def _guard(args, action: str, detail: dict) -> bool:
    if args.yes:
        return True
    print("DRY RUN — pass --yes to execute.")
    print(f"action: {action}")
    print(f"target: {json.dumps(detail, ensure_ascii=False)}")
    return False


def cmd_create_key(args):
    body = {"application_id": args.application}
    if args.name:
        body["name"] = args.name
    if args.limited_amount is not None:
        body["limited_amount"] = args.limited_amount
    if args.expired_at:
        body["expired_at"] = args.expired_at
    if not _guard(args, "POST /credentials/", body):
        return
    status, payload = _request(args, "POST", "/credentials/", body=body)
    _check_ok(status, payload)
    print("# new key created — store the token now, it is shown in full only once")
    _emit(args, payload, force_reveal=True)


def cmd_delete_key(args):
    if not _guard(args, f"DELETE /credentials/{args.id}", {"id": args.id}):
        return
    status, payload = _request(args, "DELETE", f"/credentials/{args.id}")
    _check_ok(status, payload)
    print(f"deleted credential {args.id} (HTTP {status})")


def cmd_create_order(args):
    body = {"application_id": args.application, "package_id": args.package}
    if not _guard(args, "POST /orders/", body):
        return
    status, payload = _request(args, "POST", "/orders/", body=body)
    _check_ok(status, payload)
    _emit(args, payload)


def cmd_pay_order(args):
    body = {"pay_way": args.pay_way}
    if not _guard(args, f"POST /orders/{args.id}/pay/", body):
        return
    status, payload = _request(args, "POST", f"/orders/{args.id}/pay/", body=body)
    _check_ok(status, payload)
    if isinstance(payload, dict) and payload.get("pay_url"):
        print(f"pay_url: {payload['pay_url']}")
    _emit(args, payload)


def cmd_create_token(args):
    if not _guard(args, "POST /platform-tokens/", {}):
        return
    status, payload = _request(args, "POST", "/platform-tokens/", body={})
    _check_ok(status, payload)
    print("# new platform token — store it now, it is shown in full only once")
    _emit(args, payload, force_reveal=True)


def cmd_delete_token(args):
    if not _guard(args, f"DELETE /platform-tokens/{args.id}/", {"id": args.id}):
        return
    status, payload = _request(args, "DELETE", f"/platform-tokens/{args.id}/")
    _check_ok(status, payload)
    print(f"deleted platform token {args.id} (HTTP {status})")


def cmd_send_announcement(args):
    body = {"title": args.title, "content": args.content, "published": not args.draft}
    if args.rank is not None:
        body["rank"] = args.rank
    if args.tags:
        body["tags"] = args.tags.split(",")
    if not _guard(args, "POST /announcements/admin/ (superuser only)", body):
        return
    status, payload = _request(args, "POST", "/announcements/admin/", body=body)
    _check_ok(status, payload)
    _emit(args, payload)


def build_parser() -> argparse.ArgumentParser:
    # Global options use SUPPRESS defaults so a value parsed BEFORE the
    # subcommand is not clobbered by the subparser re-injecting its own
    # default. Without SUPPRESS, argparse overwrites `--json foo` back to
    # False. Real defaults are applied in main() via _GLOBAL_DEFAULTS, so the
    # options work in both positions (e.g. `--json keys` and `keys --json`).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--token", default=argparse.SUPPRESS,
                        help="platform token (default: $ACEDATACLOUD_PLATFORM_TOKEN)")
    common.add_argument("--base-url", default=argparse.SUPPRESS, help="API base URL")
    common.add_argument("--timeout", type=float, default=argparse.SUPPRESS,
                        help="request timeout in seconds (default: 30)")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="raw JSON output")
    common.add_argument("--reveal", action="store_true", default=argparse.SUPPRESS,
                        help="do not mask secrets in output")

    p = argparse.ArgumentParser(description="AceDataCloud platform management CLI", parents=[common])
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, fn, help_):
        sp = sub.add_parser(name, help=help_, parents=[common])
        sp.set_defaults(func=fn)
        return sp

    sp = add("balance", cmd_balance, "remaining credits per subscription")
    sp.add_argument("--limit", type=int, default=50)

    sp = add("services", cmd_services, "list/search subscribed services")
    sp.add_argument("--limit", type=int, default=100)
    sp.add_argument("--search", help="filter by alias/title substring")

    sp = add("usage", cmd_usage, "recent API call records")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--days", type=int, help="only records newer than N days")
    sp.add_argument("--status-code", type=int)
    sp.add_argument("--api", help="filter by api_id")

    sp = add("usage-summary", cmd_usage_summary, "spend aggregated by API")
    sp.add_argument("--days", type=int, default=30)
    sp.add_argument("--api", help="filter by api_id")

    sp = add("keys", cmd_keys, "list API keys (credentials)")
    sp.add_argument("--limit", type=int, default=50)
    sp.add_argument("--application", help="filter by application_id")

    sp = add("orders", cmd_orders, "list recharge orders")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--state")
    sp.add_argument("--pay-way", dest="pay_way")

    sp = add("tokens", cmd_tokens, "list platform tokens")
    sp.add_argument("--limit", type=int, default=50)

    add("models", cmd_models, "list available chat models")

    sp = add("announcements", cmd_announcements, "list announcements")
    sp.add_argument("--limit", type=int, default=20)

    # public catalog / docs (no token needed)
    sp = add("service", cmd_service, "service detail (apis + pricing) [public]")
    sp.add_argument("service", help="service alias or UUID")

    sp = add("apis", cmd_apis, "list public API endpoints [public]")
    sp.add_argument("--service", help="filter to one service alias/id")

    sp = add("spec", cmd_spec, "OpenAPI spec for an API [public]")
    sp.add_argument("--path", help="API path, e.g. /suno/audios")
    sp.add_argument("--service", help="service alias for all its specs")

    sp = add("pricing", cmd_pricing, "display pricing for services [public]")
    sp.add_argument("--service", help="filter to one service alias/id")

    sp = add("docs-search", cmd_docs_search, "search the documentation [public]")
    sp.add_argument("query", help="keywords or a question")
    sp.add_argument("--lang", default="zh-cn")
    sp.add_argument("--limit", type=int, default=10)

    sp = add("docs-list", cmd_docs_list, "list documentation pages [public]")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--offset", type=int, default=0)
    sp.add_argument("--type", help="Api/Proxy/Integration/Dataset/Text")

    sp = add("doc", cmd_doc, "read a documentation page [public]")
    sp.add_argument("ref", help="doc alias, UUID, or documents/<alias> URL")
    sp.add_argument("--lang", default="zh-cn")

    sp = add("distributions", cmd_distributions, "referral status + commissions")
    sp.add_argument("--limit", type=int, default=20)

    sp = add("create-key", cmd_create_key, "create an API key (needs --yes)")
    sp.add_argument("--application", required=True)
    sp.add_argument("--name")
    sp.add_argument("--limited-amount", dest="limited_amount", type=float)
    sp.add_argument("--expired-at", dest="expired_at")
    sp.add_argument("--yes", action="store_true")

    sp = add("delete-key", cmd_delete_key, "delete an API key (needs --yes)")
    sp.add_argument("--id", required=True)
    sp.add_argument("--yes", action="store_true")

    sp = add("create-order", cmd_create_order, "create a recharge order (needs --yes)")
    sp.add_argument("--application", required=True)
    sp.add_argument("--package", required=True)
    sp.add_argument("--yes", action="store_true")

    sp = add("pay-order", cmd_pay_order, "create a pay link for an order (needs --yes)")
    sp.add_argument("--id", required=True)
    sp.add_argument("--pay-way", dest="pay_way", default="Stripe")
    sp.add_argument("--yes", action="store_true")

    sp = add("create-token", cmd_create_token, "create a platform token (needs --yes)")
    sp.add_argument("--yes", action="store_true")

    sp = add("delete-token", cmd_delete_token, "delete a platform token (needs --yes)")
    sp.add_argument("--id", required=True)
    sp.add_argument("--yes", action="store_true")

    sp = add("send-announcement", cmd_send_announcement, "publish an announcement (superuser; needs --yes)")
    sp.add_argument("--title", required=True)
    sp.add_argument("--content", required=True)
    sp.add_argument("--rank", type=int)
    sp.add_argument("--tags", help="comma-separated")
    sp.add_argument("--draft", action="store_true", help="create unpublished")
    sp.add_argument("--yes", action="store_true")

    return p


_GLOBAL_DEFAULTS = {
    "token": None,
    "base_url": DEFAULT_BASE_URL,
    "timeout": 30.0,
    "json": False,
    "reveal": False,
}


def main() -> None:
    args = build_parser().parse_args()
    # Apply defaults for any global option not supplied in either position
    # (they use argparse.SUPPRESS so unset attrs are simply absent).
    for attr, default in _GLOBAL_DEFAULTS.items():
        if not hasattr(args, attr):
            setattr(args, attr, default)
    args.func(args)


if __name__ == "__main__":
    main()

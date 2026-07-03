#!/usr/bin/env python3
"""
substack — read & publish on Substack (substack.com) with the user's own login
cookies (BYOC). Standard-library only (urllib), no third-party deps.

Substack has no official public write API, so this drives the same internal
endpoints the website uses, authenticated by the session cookies
(``substack.sid`` / ``substack.lli`` on ``.substack.com``). The publish flow
mirrors the community ``python-substack`` library: create draft → prepublish →
publish. Draft content is a ProseMirror ``doc`` (JSON string in ``draft_body``).

The connector injects the cookie jar as a JSON env var ``SUBSTACK_COOKIES``.

Read commands run directly. ``publish`` is GATED by a trailing ``--confirm``
(honored only as the last arg). ``--draft-only`` stops at a private draft.
Publishing does NOT email subscribers unless ``--send-email`` is passed.

Examples:
  python3 substack.py whoami
  python3 substack.py articles --limit 20
  python3 substack.py publish --title T --content-file a.md --draft-only --confirm
  python3 substack.py publish --title T --content-file a.md --confirm
"""

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

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PLATFORM = "substack"
ROOT = "https://substack.com/api/v1"

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


# ── Cookie jar ──────────────────────────────────────────────────────

def load_cookies() -> list:
    env = f"{PLATFORM.upper()}_COOKIES"
    raw = os.environ.get(env)
    if not raw:
        die(f"{env} is not set — connect Substack at "
            f"https://auth.acedata.cloud/user/connections, then retry.")
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"{env} is not valid JSON: {e}")
    if not isinstance(jar, list):
        die(f"{env} must be a JSON list of cookies, got {type(jar).__name__}")
    return jar


def _domain_matches(host: str, domain: str) -> bool:
    d = domain.lstrip(".").lower()
    h = host.lower()
    return not d or h == d or h.endswith("." + d)


def cookie_header(jar: list, url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    host_in_scope = any(
        c.get("domain") and _domain_matches(host, str(c["domain"])) for c in jar
    )
    parts = []
    for c in jar:
        name, value = c.get("name"), c.get("value")
        if not name or value is None:
            continue
        domain = c.get("domain")
        if domain:
            if not _domain_matches(host, str(domain)):
                continue
        elif not host_in_scope:
            continue
        parts.append(f"{name}={value}")
    return "; ".join(parts)


# ── HTTP ────────────────────────────────────────────────────────────

def request(method, url, jar, *, body=None):
    host = urllib.parse.urlsplit(url)
    origin = f"{host.scheme}://{host.hostname}"
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Origin": origin,
        "Referer": origin + "/",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → the cookie is not re-sent if the API 30x-redirects to a
    # different host (e.g. a login page), so the jar never leaks off-site.
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        die(f"network error reaching {url}: {e.reason}")


def api(method, url, jar, *, body=None, _retried=False):
    status, text = request(method, url, jar, body=body)
    # Substack sits behind Cloudflare, which intermittently 403s/429s an
    # otherwise valid session; one retry after a short pause clears the
    # transient block. Only retry idempotent GETs — never replay a write.
    if status in (403, 429) and method == "GET" and not _retried:
        time.sleep(1.5)
        return api(method, url, jar, body=body, _retried=True)
    if status in (401, 403):
        die(f"auth failed ({status}) on {url} — cookie likely expired. "
            f"Reconnect at https://auth.acedata.cloud/user/connections.")
    try:
        d = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {url}: {text[:300]}")
    if status >= 400:
        msg = d.get("error") if isinstance(d, dict) else None
        die(f"Substack API error ({status}) on {url}: {msg or text[:200]}")
    return d


# ── identity / publication ──────────────────────────────────────────

def _publication_web(pub: dict) -> str:
    custom = pub.get("custom_domain")
    if custom and not pub.get("custom_domain_optional"):
        return f"https://{custom}"
    return f"https://{pub.get('subdomain')}.substack.com"


def resolve(jar) -> dict:
    """Return {user_id, name, handle, publication_url(web), publication_api, publication_name}."""
    prof = api("GET", f"{ROOT}/user/profile/self", jar)
    if not isinstance(prof, dict) or not prof.get("id"):
        die(f"could not read Substack profile (cookie expired?): {str(prof)[:200]}")
    pub = None
    for pu in prof.get("publicationUsers") or []:
        if pu.get("is_primary") and pu.get("publication"):
            pub = pu["publication"]
            break
    if pub is None:
        for pu in prof.get("publicationUsers") or []:
            if pu.get("publication"):
                pub = pu["publication"]
                break
    if pub is None:
        die("no Substack publication on this account — create one at "
            "https://substack.com, then reconnect.")
    web = _publication_web(pub)
    return {
        "user_id": prof.get("id"),
        "name": prof.get("name"),
        "handle": prof.get("handle"),
        "publication_url": web,
        "publication_api": web + "/api/v1",
        "publication_name": pub.get("name"),
    }


def cmd_whoami(jar, _args):
    me = resolve(jar)
    out({
        "user_id": me["user_id"],
        "name": me["name"],
        "handle": me["handle"],
        "publication": me["publication_name"],
        "publication_url": me["publication_url"],
    })


def cmd_articles(jar, args):
    me = resolve(jar)
    d = api("GET", f"{me['publication_api']}/post_management/published"
            f"?offset=0&limit={args.limit}&order_by=post_date&order_direction=desc", jar)
    posts = d.get("posts") if isinstance(d, dict) else d
    posts = posts or []
    web = me["publication_url"]
    out({"count": len(posts), "articles": [{
        "id": p.get("id"),
        "title": p.get("title"),
        "url": f"{web}/p/{p.get('slug')}" if p.get("slug") else None,
        "audience": p.get("audience"),
        "post_date": p.get("post_date"),
        "reactions": p.get("reaction_count") or (p.get("reactions") or {}).get("❤"),
        "comments": p.get("comment_count"),
    } for p in posts]})


# ── markdown → ProseMirror doc ──────────────────────────────────────

# Inline: 1/2 link, 3 bold+italic, 4 bold, 5 code, 6 italic, 7 strike, 8 bare url
_INLINE = re.compile(
    r"\[([^\]]+)\]\((https?://[^)\s]+)\)"
    r"|\*\*\*([^*]+)\*\*\*"
    r"|\*\*([^*]+)\*\*"
    r"|`([^`]+)`"
    r"|(?<![\w*])\*([^*\n]+)\*(?![\w*])"
    r"|~~([^~]+)~~"
    r"|(https?://[^\s<>()\[\]]+)"
)


def _text_node(text, marks=None):
    n = {"type": "text", "text": text}
    if marks:
        n["marks"] = marks
    return n


def _inline_nodes(text: str) -> list:
    nodes: list = []
    pos = 0
    for m in _INLINE.finditer(text):
        if m.start() > pos:
            nodes.append(_text_node(text[pos:m.start()]))
        if m.group(1) is not None:  # link
            nodes.append(_text_node(m.group(1),
                                    [{"type": "link", "attrs": {"href": m.group(2)}}]))
        elif m.group(3) is not None:  # bold+italic
            nodes.append(_text_node(m.group(3), [{"type": "strong"}, {"type": "em"}]))
        elif m.group(4) is not None:  # bold
            nodes.append(_text_node(m.group(4), [{"type": "strong"}]))
        elif m.group(5) is not None:  # code
            nodes.append(_text_node(m.group(5), [{"type": "code"}]))
        elif m.group(6) is not None:  # italic
            nodes.append(_text_node(m.group(6), [{"type": "em"}]))
        elif m.group(7) is not None:  # strike
            nodes.append(_text_node(m.group(7), [{"type": "strikethrough"}]))
        elif m.group(8) is not None:  # bare url
            url = m.group(8)
            nodes.append(_text_node(url, [{"type": "link", "attrs": {"href": url}}]))
        pos = m.end()
    if pos < len(text):
        nodes.append(_text_node(text[pos:]))
    return nodes or [_text_node("")]


def _para(text: str) -> dict:
    return {"type": "paragraph", "content": _inline_nodes(text)}


def markdown_to_doc(md: str) -> dict:
    """Convert Markdown → a Substack ProseMirror ``doc`` node.

    Supports: ATX headings (#..######), fenced code (```), blockquotes (>),
    bullet/ordered lists, horizontal rules (---/***/___), and paragraphs with
    inline bold/italic/code/strike/links.
    """
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    content: list = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            buf = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            node = {"type": "code_block",
                    "content": [{"type": "text", "text": "\n".join(buf)}] if buf else []}
            if lang:
                node["attrs"] = {"language": lang}
            content.append(node)
            continue

        # heading
        mh = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if mh:
            content.append({"type": "heading",
                            "attrs": {"level": len(mh.group(1))},
                            "content": _inline_nodes(mh.group(2).strip())})
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            content.append({"type": "horizontal_rule"})
            i += 1
            continue

        # blockquote (consecutive > lines)
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            content.append({"type": "blockquote",
                            "content": [_para(" ".join(x.strip() for x in buf if x.strip()))]})
            continue

        # bullet / ordered list (consecutive matching items)
        mli = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", line)
        if mli:
            ordered = bool(re.match(r"^\s*\d+\.", line))
            items = []
            while i < n:
                m2 = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", lines[i])
                if not m2:
                    break
                is_ord = bool(re.match(r"^\s*\d+\.", lines[i]))
                if is_ord != ordered:
                    break
                items.append({"type": "list_item", "content": [_para(m2.group(2).strip())]})
                i += 1
            content.append({"type": "ordered_list" if ordered else "bullet_list",
                            "content": items})
            continue

        # paragraph (gather until blank / block start)
        buf = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", ">", "```"))
                    or re.match(r"^(-{3,}|\*{3,}|_{3,})$", nxt)
                    or re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i])):
                break
            buf.append(nxt)
            i += 1
        content.append(_para(" ".join(buf)))

    if not content:
        content = [_para("")]
    return {"type": "doc", "content": content}


# ── publish (GATED) ─────────────────────────────────────────────────

def _read_content(args) -> str:
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    if args.content:
        return args.content
    die("provide --content or --content-file")


def cmd_publish(jar, args):
    me = resolve(jar)
    md = _read_content(args)
    doc = markdown_to_doc(md)
    audience = args.audience
    pub_api = me["publication_api"]

    plan = {
        "action": "publish",
        "dry_run": not CONFIRM,
        "draft_only": args.draft_only,
        "send_email": args.send_email,
        "title": args.title,
        "subtitle": args.subtitle,
        "audience": audience,
        "publication": me["publication_name"],
        "publication_url": me["publication_url"],
        "blocks": len(doc["content"]),
    }
    if not CONFIRM:
        plan["note"] = ("DRY-RUN — re-run with --confirm as the LAST argument to "
                        "create the draft. Add --draft-only to stop at a private "
                        "draft; omit it to go live. --send-email emails subscribers.")
        out(plan)
        return

    body = {
        "draft_title": args.title,
        "draft_subtitle": args.subtitle or "",
        "draft_body": json.dumps(doc),
        "draft_bylines": [{"id": int(me["user_id"]), "is_guest": False}],
        "audience": audience,
        "write_comment_permissions": audience,
        "section_chosen": False,
    }
    draft = api("POST", f"{pub_api}/drafts", jar, body=body)
    draft_id = draft.get("id") if isinstance(draft, dict) else None
    if not draft_id:
        die(f"draft create returned no id: {str(draft)[:200]}")

    if args.draft_only:
        out({**plan, "status": "draft_created", "draft_id": draft_id,
             "edit_url": f"{me['publication_url']}/publish/post/{draft_id}"})
        return

    # prepublish validation, then publish
    api("GET", f"{pub_api}/drafts/{draft_id}/prepublish", jar)
    pub = api("POST", f"{pub_api}/drafts/{draft_id}/publish", jar,
              body={"send": bool(args.send_email), "share_automatically": False})
    slug = (pub or {}).get("slug") if isinstance(pub, dict) else None
    out({**plan, "status": "published", "draft_id": draft_id,
         "post_id": (pub or {}).get("id") if isinstance(pub, dict) else None,
         "url": f"{me['publication_url']}/p/{slug}" if slug else me["publication_url"],
         "emailed_subscribers": bool(args.send_email)})


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Substack BYOC CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="who is logged in + primary publication")

    pa = sub.add_parser("articles", help="my published posts + stats")
    pa.add_argument("--limit", type=int, default=20)

    pp = sub.add_parser("publish", help="publish a post (GATED by --confirm)")
    pp.add_argument("--title", required=True)
    pp.add_argument("--subtitle", default="")
    pp.add_argument("--content", help="inline markdown body")
    pp.add_argument("--content-file", help="path to a markdown file")
    pp.add_argument("--audience", default="everyone",
                    choices=["everyone", "only_paid", "founding", "only_free"])
    pp.add_argument("--draft-only", action="store_true",
                    help="stop at a private draft (recommended default)")
    pp.add_argument("--send-email", action="store_true",
                    help="also email subscribers (off by default)")

    args = p.parse_args(ARGV)
    jar = load_cookies()
    {"whoami": cmd_whoami, "articles": cmd_articles, "publish": cmd_publish}[args.cmd](jar, args)


if __name__ == "__main__":
    main()

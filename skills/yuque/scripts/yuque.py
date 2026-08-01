#!/usr/bin/env python3
"""Read and write Yuque (语雀) documents.

Two authentication modes, picked automatically from the environment:

* ``YUQUE_TOKEN``   — the official open API (``/api/v2`` + ``X-Auth-Token``).
                      Requires a paid 语雀超级会员.
* ``YUQUE_COOKIES`` — the user's own browser login jar (BYOC) driving the
                      internal web API (``/api/*``). Free, no membership.

Standard-library only (urllib), no third-party deps, so it runs in the bare
sandbox without an image change.

Writes are GATED: without a trailing ``--confirm`` they only dry-run.
``--confirm`` is honored ONLY as the last argument, so a title or body that
merely contains "--confirm" can never silently write.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import pathlib
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://www.yuque.com"
API_BASE = f"{ORIGIN}/api/v2"
WEB_API = f"{ORIGIN}/api"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
GATED_COMMANDS = {"create", "update", "delete"}
# Commands the internal web API cannot serve safely; see SKILL.md.
TOKEN_ONLY_COMMANDS = {"update", "delete"}
MAX_CONTENT_BYTES = 10 * 1024 * 1024
MAX_ITEMS = 100

RECONNECT = "https://studio.acedata.cloud/console/connectors"


def output(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def die(message: str, code: int = 1) -> None:
    output({"error": message})
    raise SystemExit(code)


def split_confirmation(argv: list[str]) -> tuple[list[str], bool]:
    confirmed = bool(argv) and argv[-1] == "--confirm"
    return (argv[:-1] if confirmed else list(argv), confirmed)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects outright.

    ``add_unredirected_header`` protects only the Cookie header — urllib copies
    every *other* header onto a redirected request, so ``x-csrf-token`` would
    follow a 30x to an arbitrary host. Refusing redirects closes that leak.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# ── Cookie jar (shared pattern across the cookie-BYOC skills) ──────────────


def load_cookies(raw: str) -> list:
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as error:
        die(f"YUQUE_COOKIES is not valid JSON: {error}")
    if not isinstance(jar, list):
        die(f"YUQUE_COOKIES must be a JSON list of cookies, got {type(jar).__name__}")
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


def csrf_token(jar: list) -> str:
    """Yuque's internal API takes its CSRF token from the yuque_ctoken cookie."""
    for c in jar:
        if c.get("name") == "yuque_ctoken" and c.get("value"):
            return str(c["value"])
    die(
        "The 语雀 cookie jar has no yuque_ctoken cookie, so no write can be "
        f"signed. Log in at {ORIGIN} and reconnect at {RECONNECT}."
    )
    return ""  # unreachable; die() raises


class YuqueClient:
    """One client, two modes. ``mode`` drives the base URL and the auth headers."""

    def __init__(self, mode: str, *, token: str = "", cookies: list | None = None, opener=None) -> None:
        self.mode = mode
        self._token = token
        self._cookies = cookies or []
        self._csrf = csrf_token(self._cookies) if mode == "cookie" else ""
        self._books_cache: list[dict] | None = None
        self._book_meta: dict[int, dict] = {}
        self._opener = opener or urllib.request.build_opener(NoRedirectHandler())

    @classmethod
    def from_environment(cls):
        token = os.environ.get("YUQUE_TOKEN", "").strip()
        if token:
            if "\r" in token or "\n" in token:
                die("YUQUE_TOKEN contains invalid characters.")
            return cls("token", token=token)
        raw = os.environ.get("YUQUE_COOKIES", "").strip()
        if raw:
            return cls("cookie", cookies=load_cookies(raw))
        die(
            "No 语雀 credential is available. Connect 语雀 with the browser "
            f"extension (free) or a personal token at {RECONNECT}."
        )

    # -- transport ---------------------------------------------------------

    def _open(self, request: urllib.request.Request, *, what: str, write: bool):
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw
        except urllib.error.HTTPError as error:
            if error.code in {301, 302, 303, 307, 308}:
                die(
                    f"语雀 redirected {what} — not followed, so no credential left "
                    f"yuque.com. You are most likely logged out; reconnect at {RECONNECT}."
                    + (
                        " This was a WRITE: its outcome is UNKNOWN — list the "
                        "documents before retrying so you do not create a duplicate."
                        if write
                        else ""
                    )
                )
            if error.code in {401, 403}:
                hint = (
                    "The token is invalid or lacks scope. Note the 语雀 open API "
                    "requires a paid 语雀超级会员."
                    if self.mode == "token"
                    else "The login session expired or the request was rejected by 语雀's "
                    "CSRF check."
                )
                die(f"语雀 HTTP {error.code} for {what}. {hint} Reconnect at {RECONNECT}.")
            if error.code == 404:
                die(f"语雀 404 for {what}; the knowledge base or document does not exist.")
            die(f"语雀 HTTP {error.code} for {what}.")
        except (urllib.error.URLError, OSError, socket.timeout) as error:
            if write:
                die(
                    f"语雀 write {what} did not return a result ({error}); the outcome "
                    "is UNKNOWN. List the documents before retrying so you do not "
                    "create a duplicate."
                )
            die(f"Network error while calling 语雀 {what}.")

    def request(self, method: str, path: str, *, body=None, write: bool = False, expect_json: bool = True):
        """Call the API of whichever mode is active and return the ``data`` payload."""
        what = f"{method} {path}"
        if self.mode == "token":
            url = f"{API_BASE}{path}"
            headers = {
                "Accept": "application/json",
                "X-Auth-Token": self._token,
                "Content-Type": "application/json",
                "User-Agent": "AceDataCloud-Yuque-Skill/2.0",
            }
        else:
            url = f"{WEB_API}{path}"
            # Yuque's CSRF layer rejects writes without Origin/Referer — the
            # upstream WechatSync adapter injects both for every /api/ call.
            headers = {
                "Accept": "application/json",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Content-Type": "application/json",
                "User-Agent": UA,
                "Origin": ORIGIN,
                "Referer": f"{ORIGIN}/dashboard",
                "x-csrf-token": self._csrf,
                "x-requested-with": "XMLHttpRequest",
            }

        encoded = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=encoded, method=method, headers=headers)
        if self.mode == "cookie":
            request.add_unredirected_header("Cookie", cookie_header(self._cookies, url))

        raw = self._open(request, what=what, write=write)
        if not expect_json or not raw:
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            die(f"语雀 returned invalid JSON for {what}.")
        if not isinstance(payload, dict) or "data" not in payload:
            die(f"语雀 returned an unexpected envelope for {what}.")
        return payload["data"]

    # -- reads -------------------------------------------------------------

    def user(self) -> dict:
        path = "/user" if self.mode == "token" else "/mine"
        value = self.request("GET", path)
        if not isinstance(value, dict):
            die("语雀 returned malformed user data.")
        return value

    def repos(self, login: str | None = None) -> list[dict]:
        if self.mode == "token":
            quoted = urllib.parse.quote(str(login), safe="")
            value = self.request("GET", f"/users/{quoted}/repos")
            if not isinstance(value, list):
                die("语雀 returned malformed repo data.")
            return value
        # Internal API: books are nested under the "common used" payload and
        # carry the book id as target_id.
        value = self.request("GET", "/mine/common_used")
        books = (value or {}).get("books") if isinstance(value, dict) else None
        if not isinstance(books, list):
            die("语雀 returned malformed knowledge-base data.")
        return books

    def docs(self, repo: str) -> list[dict]:
        if self.mode == "token":
            quoted = urllib.parse.quote(str(repo), safe="")
            value = self.request("GET", f"/repos/{quoted}/docs")
        else:
            value = self.request("GET", f"/books/{self._book_id(repo)}/docs")
        if not isinstance(value, list):
            die("语雀 returned malformed document data.")
        return value

    def doc(self, repo: str, doc_id: str) -> tuple[dict, str | None]:
        book_id = None
        if self.mode == "token":
            repo_q = urllib.parse.quote(str(repo), safe="")
            doc_q = urllib.parse.quote(str(doc_id), safe="")
            value = self.request("GET", f"/repos/{repo_q}/docs/{doc_q}")
        else:
            book_id = self._book_id(repo)
            query = urllib.parse.urlencode({"book_id": book_id, "mode": "markdown"})
            doc_q = urllib.parse.quote(str(doc_id), safe="")
            value = self.request("GET", f"/docs/{doc_q}?{query}")
        if not isinstance(value, dict):
            die("语雀 returned malformed document data.")
        return value, self.doc_url(book_id, value)

    # -- writes ------------------------------------------------------------

    def create_doc(self, repo: str, args, content: str) -> tuple[dict, str | None]:
        book_id = None
        if self.mode == "token":
            quoted = urllib.parse.quote(str(repo), safe="")
            body = {
                "title": args.title,
                "body": content,
                "format": "markdown",
                "public": 1 if args.public else 0,
            }
            if args.slug:
                body["slug"] = args.slug
            value = self.request("POST", f"/repos/{quoted}/docs", body=body, write=True)
        else:
            # The internal API accepts markdown directly, so we skip the extra
            # /api/docs/convert round trip, and insert_to_catalog puts the new
            # doc in the book's 目录 (the plain create leaves it unlisted).
            book_id = self._book_id(repo)
            body = {
                "book_id": book_id,
                "title": args.title,
                "format": "markdown",
                "body": content,
                "body_draft": content,
                "public": 1 if args.public else 0,
                "insert_to_catalog": True,
                "action": "appendByDocs",
                "target_uuid": "",
            }
            if args.slug:
                body["slug"] = args.slug
            value = self.request("POST", "/docs", body=body, write=True)
        if not isinstance(value, dict) or not value.get("id"):
            die("语雀 did not return a valid created document.")
        return value, self.doc_url(book_id, value)

    def update_doc(self, repo: str, doc_id: str, args, content: str) -> dict:
        repo_q = urllib.parse.quote(str(repo), safe="")
        doc_q = urllib.parse.quote(str(doc_id), safe="")
        body = {
            "title": args.title,
            "body": content,
            "format": "markdown",
            "public": 1 if args.public else 0,
        }
        if args.slug:
            body["slug"] = args.slug
        value = self.request("PUT", f"/repos/{repo_q}/docs/{doc_q}", body=body, write=True)
        if not isinstance(value, dict) or not value.get("id"):
            die("语雀 did not return a valid updated document.")
        return value

    def delete_doc(self, repo: str, doc_id: str) -> None:
        repo_q = urllib.parse.quote(str(repo), safe="")
        doc_q = urllib.parse.quote(str(doc_id), safe="")
        self.request("DELETE", f"/repos/{repo_q}/docs/{doc_q}", write=True, expect_json=False)

    # -- helpers -----------------------------------------------------------

    def _book_id(self, repo: str) -> int:
        """Resolve a repo reference to a numeric book id for the internal API.

        The internal endpoints are addressed by numeric book id only, so a
        ``user/book`` namespace has to be looked up against the account's own
        knowledge bases first.
        """
        text = str(repo).strip()
        # isdigit() is Unicode-aware but int() is not, and non-ASCII digits
        # would otherwise either crash or resolve to a different number.
        if text.isascii() and text.isdigit():
            return int(text)
        wanted = text.rsplit("/", 1)[-1].lower()
        if not wanted:
            die("Empty knowledge base reference; run `repos` and pass a repo_id.")
        matches = []
        for book in self._books():
            slug = str(book.get("slug") or "").lower()
            name = str(book.get("name") or "").lower()
            if wanted in {slug, name}:
                raw = book.get("target_id") or book.get("id")
                try:
                    matches.append((int(raw), book))
                except (TypeError, ValueError):
                    continue
        if len(matches) > 1:
            die(
                f"{repo!r} matches {len(matches)} knowledge bases "
                f"({', '.join(str(m[0]) for m in matches)}). Pass the numeric "
                "repo_id from `repos` instead — writing to the wrong base is silent."
            )
        if matches:
            self._book_meta[matches[0][0]] = matches[0][1]
            return matches[0][0]
        die(
            f"Could not resolve knowledge base {repo!r} to a book id. Run "
            "`repos` and pass the numeric repo_id shown there."
        )
        return 0  # unreachable; die() raises

    def _books(self) -> list[dict]:
        """Knowledge bases, fetched once — a doc loop must not re-query per item."""
        if self._books_cache is None:
            self._books_cache = self.repos()
        return self._books_cache

    def doc_url(self, book_id, doc: dict) -> str | None:
        """Public URL for a doc, using the book namespace when we know it."""
        slug = doc.get("slug")
        book = (doc.get("book") or {}) if isinstance(doc.get("book"), dict) else {}
        namespace = book.get("namespace")
        if not namespace and self.mode == "cookie":
            try:
                meta = self._book_meta.get(int(book_id)) or {}
            except (TypeError, ValueError):
                meta = {}
            user = (meta.get("user") or {}) if isinstance(meta.get("user"), dict) else {}
            login = user.get("login")
            book_slug = meta.get("slug")
            if login and book_slug:
                namespace = f"{login}/{book_slug}"
        if namespace and slug:
            return f"{ORIGIN}/{namespace}/{slug}"
        return None


def read_content(args) -> str:
    if args.content_file:
        path = pathlib.Path(args.content_file)
        try:
            if path.stat().st_size > MAX_CONTENT_BYTES:
                die("Content file exceeds the 10 MiB safety limit.")
            return path.read_text(encoding="utf-8")
        except OSError as error:
            die(f"Cannot read --content-file: {error}")
    if args.content is not None:
        if len(args.content.encode("utf-8")) > MAX_CONTENT_BYTES:
            die("Content exceeds the 10 MiB safety limit.")
        return args.content
    die("Provide --content-file <path.md> or --content <markdown>.")


def format_repo(repo: dict) -> dict:
    # The internal API nests books under a "common used" record whose own `id`
    # is NOT the book id — the book id is target_id. Prefer it, or `repos`
    # would print an id that no other endpoint accepts.
    repo_id = repo.get("target_id") or repo.get("id")
    user = repo.get("user") if isinstance(repo.get("user"), dict) else {}
    namespace = repo.get("namespace")
    if not namespace and user.get("login") and repo.get("slug"):
        namespace = f"{user['login']}/{repo['slug']}"
    return {
        "repo_id": repo_id,
        "namespace": namespace,
        "name": repo.get("name"),
        "slug": repo.get("slug"),
        "type": repo.get("type"),
        "public": repo.get("public"),
        "items_count": repo.get("items_count"),
    }


def format_doc(doc: dict, repo: str | None = None, url: str | None = None) -> dict:
    namespace = repo or (doc.get("book") or {}).get("namespace")
    slug = doc.get("slug")
    if url is None and namespace and slug and not str(namespace).isdigit():
        url = f"{ORIGIN}/{namespace}/{slug}"
    return {
        "doc_id": doc.get("id"),
        "title": doc.get("title"),
        "slug": slug,
        "public": doc.get("public"),
        "status": doc.get("status"),
        "url": url,
        "word_count": doc.get("word_count"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yuque.py", description="Yuque CLI (token or cookie)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the connected account and the active auth mode")

    repos = sub.add_parser("repos", help="list the account's knowledge bases")
    repos.add_argument("--login", help="user login; token mode only, defaults to the own account")

    docs = sub.add_parser("docs", help="list documents in a knowledge base")
    docs.add_argument("repo", help="repo namespace (user/book) or numeric repo id")
    docs.add_argument("--limit", type=int, default=20)

    one = sub.add_parser("doc", help="read one document")
    one.add_argument("repo")
    one.add_argument("doc_id", help="document id or slug")

    for command in ("create", "update"):
        write = sub.add_parser(command, help=f"{command} a document (GATED by trailing --confirm)")
        write.add_argument("repo")
        if command == "update":
            write.add_argument("doc_id")
        write.add_argument("--title", required=True)
        write.add_argument("--content")
        write.add_argument("--content-file")
        write.add_argument("--slug")
        write.add_argument(
            "--public",
            action="store_true",
            help="publish publicly; omit to keep the document private",
        )

    delete = sub.add_parser("delete", help="delete a document (GATED by trailing --confirm)")
    delete.add_argument("repo")
    delete.add_argument("doc_id")
    return parser


def dry_run(args, content: str | None = None) -> None:
    value = {"dry_run": True, "command": args.command, "platform": "yuque", "repo": args.repo}
    if args.command in {"create", "update"}:
        value.update(
            {
                "doc_id": getattr(args, "doc_id", None),
                "title": args.title,
                "visibility": "public" if args.public else "private",
                "slug": args.slug,
                "content_characters": len(content or ""),
            }
        )
    else:
        value["doc_id"] = args.doc_id
    value["note"] = "Re-run with --confirm as the final argument to write to 语雀."
    output(value)


def main(argv: list[str] | None = None) -> None:
    raw = list(sys.argv[1:] if argv is None else argv)
    clean_argv, confirmed = split_confirmation(raw)
    args = build_parser().parse_args(clean_argv)
    content = read_content(args) if args.command in {"create", "update"} else None
    if args.command in GATED_COMMANDS and not confirmed:
        dry_run(args, content)
        return

    client = YuqueClient.from_environment()
    if client.mode == "cookie" and args.command in TOKEN_ONLY_COMMANDS:
        die(
            f"`{args.command}` is only available when 语雀 is connected with a "
            "personal token (the open API). This connection uses login cookies. "
            "Create a new document instead, or edit the existing one in 语雀."
        )

    mode = {"auth_mode": client.mode}
    if args.command == "whoami":
        user = client.user()
        login = user.get("login")
        output(
            {
                **mode,
                "user_id": user.get("id"),
                "login": login,
                "name": user.get("name"),
                "url": f"{ORIGIN}/{login}" if login else None,
                "books_count": user.get("books_count"),
                "public_books_count": user.get("public_books_count"),
            }
        )
    elif args.command == "repos":
        if client.mode == "token":
            login = args.login or client.user().get("login")
            if not login:
                die("Could not resolve the account login; pass --login explicitly.")
            items = client.repos(login)
        else:
            items = client.repos()
        output({**mode, "repos": [format_repo(item) for item in items]})
    elif args.command == "docs":
        if not 1 <= args.limit <= MAX_ITEMS:
            die(f"--limit must be between 1 and {MAX_ITEMS}.")
        items = client.docs(args.repo)[: args.limit]
        output({**mode, "count": len(items), "docs": [format_doc(item, args.repo) for item in items]})
    elif args.command == "doc":
        doc, url = client.doc(args.repo, args.doc_id)
        result = format_doc(doc, args.repo, url)
        result["body"] = doc.get("body")
        output({**mode, **result})
    elif args.command == "create":
        result, url = client.create_doc(args.repo, args, content or "")
        output({**mode, "ok": True, **format_doc(result, args.repo, url), "public": bool(args.public)})
    elif args.command == "update":
        result = client.update_doc(args.repo, args.doc_id, args, content or "")
        output({**mode, "ok": True, **format_doc(result, args.repo), "public": bool(args.public)})
    elif args.command == "delete":
        client.delete_doc(args.repo, args.doc_id)
        output({**mode, "ok": True, "repo": args.repo, "doc_id": args.doc_id, "deleted": True})


if __name__ == "__main__":
    main()

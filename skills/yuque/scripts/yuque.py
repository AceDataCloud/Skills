#!/usr/bin/env python3
"""Read and write Yuque (语雀) documents through its official open API."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://www.yuque.com/api/v2"
GATED_COMMANDS = {"create", "update", "delete"}
MAX_CONTENT_BYTES = 10 * 1024 * 1024
MAX_ITEMS = 100


def output(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def die(message: str, code: int = 1) -> None:
    output({"error": message})
    raise SystemExit(code)


def split_confirmation(argv: list[str]) -> tuple[list[str], bool]:
    confirmed = bool(argv) and argv[-1] == "--confirm"
    return (argv[:-1] if confirmed else list(argv), confirmed)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class YuqueClient:
    def __init__(self, token: str, opener=None) -> None:
        self._token = token
        self._opener = opener or urllib.request.build_opener(NoRedirectHandler())

    @classmethod
    def from_environment(cls):
        token = os.environ.get("YUQUE_TOKEN", "").strip()
        if not token:
            die(
                "YUQUE_TOKEN is not set. Reconnect 语雀 at "
                "https://auth.acedata.cloud/user/connections."
            )
        return cls(token)

    def request(self, method: str, path: str, *, body=None, write: bool = False, expect_json: bool = True):
        encoded = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            data=encoded,
            method=method,
            headers={
                "Accept": "application/json",
                "X-Auth-Token": self._token,
                "Content-Type": "application/json",
                "User-Agent": "AceDataCloud-Yuque-Skill/1.0",
            },
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            if error.code in {301, 302, 303, 307, 308}:
                die(f"Yuque API redirected {method} {path}; credentials were not forwarded.")
            if error.code in {401, 403}:
                die(
                    f"Yuque API HTTP {error.code} for {method} {path}. The token is invalid or "
                    "lacks scope. Reconnect with a token from https://www.yuque.com/settings/tokens."
                )
            if error.code == 404:
                die(f"Yuque API 404 for {method} {path}; the repo or document does not exist.")
            die(f"Yuque API HTTP {error.code} for {method} {path}.")
        except (urllib.error.URLError, OSError, socket.timeout):
            if write:
                die(
                    f"Yuque write {method} {path} did not return a result; outcome is unknown. "
                    "List the documents before retrying so you do not create a duplicate."
                )
            die(f"Network error while calling Yuque {method} {path}.")
        if not expect_json or not raw:
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            die(f"Yuque returned invalid JSON for {method} {path}.")
        if not isinstance(payload, dict) or "data" not in payload:
            die(f"Yuque returned an unexpected envelope for {method} {path}.")
        return payload["data"]

    def user(self) -> dict:
        value = self.request("GET", "/user")
        if not isinstance(value, dict):
            die("Yuque returned malformed user data.")
        return value

    def repos(self, login: str) -> list[dict]:
        quoted = urllib.parse.quote(str(login), safe="")
        value = self.request("GET", f"/users/{quoted}/repos")
        if not isinstance(value, list):
            die("Yuque returned malformed repo data.")
        return value

    def docs(self, repo: str) -> list[dict]:
        quoted = urllib.parse.quote(str(repo), safe="")
        value = self.request("GET", f"/repos/{quoted}/docs")
        if not isinstance(value, list):
            die("Yuque returned malformed document data.")
        return value

    def doc(self, repo: str, doc_id: str) -> dict:
        repo_q = urllib.parse.quote(str(repo), safe="")
        doc_q = urllib.parse.quote(str(doc_id), safe="")
        value = self.request("GET", f"/repos/{repo_q}/docs/{doc_q}")
        if not isinstance(value, dict):
            die("Yuque returned malformed document data.")
        return value

    def create_doc(self, repo: str, body: dict) -> dict:
        quoted = urllib.parse.quote(str(repo), safe="")
        value = self.request("POST", f"/repos/{quoted}/docs", body=body, write=True)
        if not isinstance(value, dict) or not value.get("id"):
            die("Yuque did not return a valid created document.")
        return value

    def update_doc(self, repo: str, doc_id: str, body: dict) -> dict:
        repo_q = urllib.parse.quote(str(repo), safe="")
        doc_q = urllib.parse.quote(str(doc_id), safe="")
        value = self.request("PUT", f"/repos/{repo_q}/docs/{doc_q}", body=body, write=True)
        if not isinstance(value, dict) or not value.get("id"):
            die("Yuque did not return a valid updated document.")
        return value

    def delete_doc(self, repo: str, doc_id: str) -> None:
        repo_q = urllib.parse.quote(str(repo), safe="")
        doc_q = urllib.parse.quote(str(doc_id), safe="")
        self.request("DELETE", f"/repos/{repo_q}/docs/{doc_q}", write=True, expect_json=False)


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
    return {
        "repo_id": repo.get("id"),
        "namespace": repo.get("namespace"),
        "name": repo.get("name"),
        "slug": repo.get("slug"),
        "type": repo.get("type"),
        "public": repo.get("public"),
        "items_count": repo.get("items_count"),
    }


def format_doc(doc: dict, repo: str | None = None) -> dict:
    namespace = repo or (doc.get("book") or {}).get("namespace")
    slug = doc.get("slug")
    return {
        "doc_id": doc.get("id"),
        "title": doc.get("title"),
        "slug": slug,
        "public": doc.get("public"),
        "status": doc.get("status"),
        "url": f"https://www.yuque.com/{namespace}/{slug}" if namespace and slug else None,
        "word_count": doc.get("word_count"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def build_body(args, content: str) -> dict:
    # public: 0 = private, 1 = public. Yuque has no separate "draft" state, so a
    # private doc is the closest equivalent and is the default.
    body = {
        "title": args.title,
        "body": content,
        "format": "markdown",
        "public": 1 if args.public else 0,
    }
    if args.slug:
        body["slug"] = args.slug
    return body


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yuque.py", description="Yuque open API CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the token's account")

    repos = sub.add_parser("repos", help="list the account's knowledge bases")
    repos.add_argument("--login", help="user login; defaults to the token's own account")

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
    value["note"] = "Re-run with --confirm as the final argument to write to Yuque."
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
    if args.command == "whoami":
        user = client.user()
        output(
            {
                "user_id": user.get("id"),
                "login": user.get("login"),
                "name": user.get("name"),
                "url": f"https://www.yuque.com/{user.get('login')}" if user.get("login") else None,
                "books_count": user.get("books_count"),
                "public_books_count": user.get("public_books_count"),
            }
        )
    elif args.command == "repos":
        login = args.login or client.user().get("login")
        if not login:
            die("Could not resolve the account login; pass --login explicitly.")
        output({"repos": [format_repo(item) for item in client.repos(login)]})
    elif args.command == "docs":
        if not 1 <= args.limit <= MAX_ITEMS:
            die(f"--limit must be between 1 and {MAX_ITEMS}.")
        items = client.docs(args.repo)[: args.limit]
        output({"count": len(items), "docs": [format_doc(item, args.repo) for item in items]})
    elif args.command == "doc":
        doc = client.doc(args.repo, args.doc_id)
        result = format_doc(doc, args.repo)
        result["body"] = doc.get("body")
        output(result)
    elif args.command == "create":
        result = client.create_doc(args.repo, build_body(args, content or ""))
        output({"ok": True, **format_doc(result, args.repo), "public": bool(args.public)})
    elif args.command == "update":
        result = client.update_doc(args.repo, args.doc_id, build_body(args, content or ""))
        output({"ok": True, **format_doc(result, args.repo), "public": bool(args.public)})
    elif args.command == "delete":
        client.delete_doc(args.repo, args.doc_id)
        output({"ok": True, "repo": args.repo, "doc_id": args.doc_id, "deleted": True})


if __name__ == "__main__":
    main()

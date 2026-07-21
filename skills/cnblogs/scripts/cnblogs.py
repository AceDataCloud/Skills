#!/usr/bin/env python3
"""Read and write CNBlogs posts through its official-client JSON API."""

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

API_BASE = "https://write.cnblogs.com/api"
GATED_COMMANDS = {"create", "update", "delete"}
MAX_CONTENT_BYTES = 10 * 1024 * 1024
MAX_POSTS = 100


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


class CNBlogsClient:
    def __init__(self, token: str, opener=None) -> None:
        self._token = token
        self._opener = opener or urllib.request.build_opener(NoRedirectHandler())

    @classmethod
    def from_environment(cls):
        token = os.environ.get("CNBLOGS_TOKEN", "").strip()
        if not token:
            die(
                "CNBLOGS_TOKEN is not set. Reconnect 博客园 at "
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
                "Authorization": f"Bearer {self._token}",
                "Authorization-Type": "pat",
                "Content-Type": "application/json",
                "User-Agent": "AceDataCloud-CNBlogs-Skill/1.0",
            },
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            if error.code in {301, 302, 303, 307, 308}:
                die(f"CNBlogs API redirected {method} {path}; credentials were not forwarded.")
            suffix = " Reconnect with a valid PAT." if error.code in {401, 403} else ""
            die(f"CNBlogs API HTTP {error.code} for {method} {path}.{suffix}")
        except (urllib.error.URLError, OSError, socket.timeout):
            if write:
                die(
                    f"CNBlogs write {method} {path} did not return a result; outcome is unknown. "
                    "Inspect the post list before retrying."
                )
            die(f"Network error while calling CNBlogs {method} {path}.")
        if not expect_json or not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            die(f"CNBlogs returned invalid JSON for {method} {path}.")

    def template(self) -> dict:
        value = self.request("GET", "/posts/-1")
        post = value.get("blogPost") if isinstance(value, dict) else None
        if not isinstance(post, dict):
            die("CNBlogs returned malformed post template data.")
        return post

    def categories(self) -> list[dict]:
        value = self.request("GET", "/v2/blog-category-types/1/categories")
        if not isinstance(value, list):
            die("CNBlogs returned malformed category data.")
        return value

    def posts(self, limit: int) -> list[dict]:
        query = urllib.parse.urlencode({"t": 1, "p": 1, "s": limit})
        value = self.request("GET", f"/posts/list?{query}")
        posts = value.get("postList") if isinstance(value, dict) else None
        if not isinstance(posts, list):
            die("CNBlogs returned malformed post-list data.")
        return posts

    def post(self, post_id: int) -> dict:
        value = self.request("GET", f"/posts/{post_id}")
        post = value.get("blogPost") if isinstance(value, dict) else None
        if not isinstance(post, dict):
            die("CNBlogs returned malformed post data.")
        return post

    def save(self, post: dict) -> dict:
        value = self.request("POST", "/posts", body=post, write=True)
        if not isinstance(value, dict) or not isinstance(value.get("id"), int) or value["id"] <= 0:
            die("CNBlogs did not return a valid saved post.")
        return value

    def delete(self, post_id: int) -> None:
        self.request("DELETE", f"/posts/{post_id}", write=True, expect_json=False)


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


def csv_strings(raw: str | None) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def csv_ids(raw: str | None) -> list[int]:
    try:
        return [int(item) for item in csv_strings(raw)]
    except ValueError:
        die("--category-ids must be a comma-separated list of integers.")


def apply_post_fields(post: dict, args, content: str) -> dict:
    post.update(
        {
            "title": args.title,
            "postBody": content,
            "isMarkdown": True,
            "isPublished": args.publish,
            "isDraft": not args.publish,
        }
    )
    if args.category_ids is not None:
        post["categoryIds"] = csv_ids(args.category_ids)
    if args.tags is not None:
        post["tags"] = csv_strings(args.tags)
    return post


def format_post(post: dict) -> dict:
    return {
        "post_id": post.get("id"),
        "title": post.get("title"),
        "url": post.get("url"),
        "published": post.get("isPublished"),
        "draft": post.get("isDraft"),
        "category_ids": post.get("categoryIds") or [],
        "tags": post.get("tags") or [],
        "created_at": post.get("datePublished"),
        "updated_at": post.get("dateUpdated"),
    }


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CNBlogs PAT API CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami")
    sub.add_parser("categories")
    posts = sub.add_parser("posts")
    posts.add_argument("--limit", type=int, default=20)
    one = sub.add_parser("post")
    one.add_argument("post_id", type=positive_int)

    for command in ("create", "update"):
        write = sub.add_parser(command)
        if command == "update":
            write.add_argument("post_id", type=positive_int)
        write.add_argument("--title", required=True)
        write.add_argument("--content")
        write.add_argument("--content-file")
        write.add_argument("--category-ids")
        write.add_argument("--tags")
        visibility = write.add_mutually_exclusive_group(required=command == "update")
        visibility.add_argument("--publish", action="store_true")
        if command == "update":
            visibility.add_argument("--draft", action="store_true")

    delete = sub.add_parser("delete")
    delete.add_argument("post_id", type=positive_int)
    return parser


def dry_run(args, content: str | None = None) -> None:
    value = {"dry_run": True, "command": args.command, "platform": "cnblogs"}
    if args.command in {"create", "update"}:
        value.update(
            {
                "post_id": getattr(args, "post_id", None),
                "title": args.title,
                "visibility": "published" if args.publish else "draft",
                "category_ids": csv_ids(args.category_ids) if args.category_ids is not None else None,
                "tags": csv_strings(args.tags) if args.tags is not None else None,
                "content_characters": len(content or ""),
            }
        )
    else:
        value["post_id"] = args.post_id
    value["note"] = "Re-run with --confirm as the final argument to write to CNBlogs."
    output(value)


def main(argv: list[str] | None = None) -> None:
    raw = list(sys.argv[1:] if argv is None else argv)
    clean_argv, confirmed = split_confirmation(raw)
    args = build_parser().parse_args(clean_argv)
    content = read_content(args) if args.command in {"create", "update"} else None
    if args.command in GATED_COMMANDS and not confirmed:
        dry_run(args, content)
        return

    client = CNBlogsClient.from_environment()
    if args.command == "whoami":
        template = client.template()
        output({"author": template.get("author"), "blog_id": template.get("blogId"), "template": format_post(template)})
    elif args.command == "categories":
        output({"categories": client.categories()})
    elif args.command == "posts":
        if not 1 <= args.limit <= MAX_POSTS:
            die(f"--limit must be between 1 and {MAX_POSTS}.")
        output({"posts": [format_post(item) for item in client.posts(args.limit)]})
    elif args.command == "post":
        output(format_post(client.post(args.post_id)))
    elif args.command == "create":
        result = client.save(apply_post_fields(client.template(), args, content or ""))
        output(
            {
                "ok": True,
                **format_post(result),
                "published": args.publish,
                "draft": not args.publish,
                "edit_url": f"https://i.cnblogs.com/posts/edit;postId={result['id']}",
            }
        )
    elif args.command == "update":
        result = client.save(apply_post_fields(client.post(args.post_id), args, content or ""))
        output({"ok": True, **format_post(result), "published": args.publish, "draft": not args.publish})
    elif args.command == "delete":
        client.delete(args.post_id)
        output({"ok": True, "post_id": args.post_id, "deleted": True})


if __name__ == "__main__":
    main()

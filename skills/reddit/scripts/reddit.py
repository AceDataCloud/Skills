#!/usr/bin/env python3
"""Read and submit Reddit posts with OAuth or the user's login cookies.

Cookie mode uses Reddit's first-party web JSON endpoints and the ``modhash``
returned by ``/api/me.json``. OAuth mode uses ``oauth.reddit.com``. The helper
automatically selects ``REDDIT_TOKEN`` first, then ``REDDIT_COOKIES``.

State-changing commands are dry-runs unless ``--confirm`` is the final argv
token. Credentials, cookie values and modhashes are never emitted.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WEB_BASE = "https://www.reddit.com"
OAUTH_BASE = "https://oauth.reddit.com"
USER_AGENT = "web:cloud.acedata.reddit:v2.0 (by /u/acedatacloud)"
GATED_COMMANDS = {"submit-text", "submit-link"}
SUBREDDIT_RE = re.compile(r"^[A-Za-z0-9_]{2,21}$")
COOKIE_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


def output(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def die(message: str, code: int = 1) -> None:
    output({"error": message})
    raise SystemExit(code)


def split_confirmation(argv: list[str]) -> tuple[list[str], bool]:
    confirmed = bool(argv) and argv[-1] == "--confirm"
    return (argv[:-1] if confirmed else list(argv), confirmed)


def parse_cookie_jar(raw: str) -> list[dict]:
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as error:
        die(f"REDDIT_COOKIES is not valid JSON: {error}")
    if not isinstance(jar, list):
        die(f"REDDIT_COOKIES must be a JSON list of cookies, got {type(jar).__name__}")
    normalized = []
    for item in jar:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if not isinstance(name, str) or not COOKIE_NAME_RE.fullmatch(name) or not isinstance(value, str):
            continue
        if any(character == ";" or ord(character) < 0x20 or ord(character) == 0x7F for character in value):
            continue
        domain = item.get("domain")
        if not isinstance(domain, str) or not reddit_cookie_domain(domain):
            continue
        path = str(item.get("path") or "/")
        if not path.startswith("/"):
            continue
        expiration = item.get("expirationDate")
        if expiration not in (None, ""):
            try:
                if float(expiration) <= time.time():
                    continue
            except (TypeError, ValueError):
                continue
        normalized.append(
            dict(
                item,
                name=name,
                value=value,
                domain=domain,
                path=path,
                secure=bool(item.get("secure")),
            )
        )
    if not any(
        cookie.get("name") == "reddit_session"
        and cookie.get("value")
        and cookie_applies(cookie, WEB_BASE + "/api/me.json")
        for cookie in normalized
    ):
        die(
            "REDDIT_COOKIES is missing a valid reddit_session — log in on reddit.com, "
            "re-capture with the ACE extension, then reconnect at "
            "https://auth.acedata.cloud/user/connections."
        )
    return normalized


def reddit_cookie_domain(domain: str) -> bool:
    normalized_domain = domain.strip().lstrip(".").lower()
    return normalized_domain == "reddit.com" or normalized_domain.endswith(".reddit.com")


def domain_matches(host: str, domain: str) -> bool:
    raw_domain = domain.strip().lower()
    normalized_domain = raw_domain.lstrip(".")
    normalized_host = host.lower()
    if not normalized_domain:
        return False
    if raw_domain.startswith("."):
        return normalized_host == normalized_domain or normalized_host.endswith("." + normalized_domain)
    return normalized_host == normalized_domain


def cookie_domain_matches(cookie: dict, host: str) -> bool:
    domain = str(cookie.get("domain") or "")
    if cookie.get("hostOnly") is True:
        return host.lower() == domain.lstrip(".").lower()
    if cookie.get("hostOnly") is False:
        normalized = domain.lstrip(".")
        return bool(normalized) and (
            host.lower() == normalized.lower() or host.lower().endswith("." + normalized.lower())
        )
    return domain_matches(host, domain)


def path_matches(request_path: str, cookie_path: str) -> bool:
    if request_path == cookie_path:
        return True
    if not request_path.startswith(cookie_path):
        return False
    return cookie_path.endswith("/") or request_path[len(cookie_path) :].startswith("/")


def cookie_applies(cookie: dict, url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    domain = str(cookie.get("domain") or "")
    path = str(cookie.get("path") or "/")
    if not reddit_cookie_domain(domain) or not cookie_domain_matches(cookie, host):
        return False
    if not path.startswith("/") or not path_matches(parsed.path or "/", path):
        return False
    if cookie.get("secure") and parsed.scheme != "https":
        return False
    expiration = cookie.get("expirationDate")
    if expiration not in (None, ""):
        try:
            if float(expiration) <= time.time():
                return False
        except (TypeError, ValueError):
            return False
    return True


def cookie_header(jar: list[dict], url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    if not reddit_cookie_domain(host):
        return ""
    applicable = [
        (index, cookie)
        for index, cookie in enumerate(jar)
        if cookie_applies(cookie, url)
    ]
    applicable.sort(key=lambda item: (-len(str(item[1].get("path") or "/")), item[0]))
    parts = []
    seen = set()
    for _, cookie in applicable:
        identity = (
            cookie.get("name"),
            cookie.get("domain"),
            cookie.get("path") or "/",
        )
        if identity in seen:
            continue
        seen.add(identity)
        parts.append(f"{cookie['name']}={cookie['value']}")
    return "; ".join(parts)


def normalize_subreddit(value: str) -> str:
    subreddit = value.strip().strip("/")
    if subreddit.lower().startswith("r/"):
        subreddit = subreddit[2:]
    if not SUBREDDIT_RE.fullmatch(subreddit):
        die("subreddit must contain only letters, numbers or underscores (2-21 characters)")
    return subreddit


def validate_title(value: str) -> str:
    title = value.strip()
    if not title:
        die("title cannot be empty")
    if len(title) > 300:
        die("title exceeds Reddit's 300-character limit")
    return title


def validate_link(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        die("url must be an http(s) URL without embedded credentials")
    return value.strip()


def read_text(args: argparse.Namespace) -> str:
    if args.text_file:
        try:
            with open(args.text_file, encoding="utf-8") as file_handle:
                text = file_handle.read()
        except OSError as error:
            die(f"cannot read text file {args.text_file}: {error}")
    else:
        text = args.text or ""
    if len(text) > 40_000:
        die("text exceeds Reddit's 40,000-character limit")
    return text


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Return 30x responses to the caller instead of replaying credentials."""

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def open_request(request: urllib.request.Request):
    return urllib.request.build_opener(NoRedirect()).open(request, timeout=30)


class RedditClient:
    def __init__(self, mode: str, *, cookies: list[dict] | None = None, token: str = ""):
        self.mode = mode
        self.cookies = cookies or []
        self.token = token
        self.modhash = ""
        self.username = ""

    @classmethod
    def from_environment(cls) -> "RedditClient":
        token = os.environ.get("REDDIT_TOKEN", "").strip()
        if token:
            if "\r" in token or "\n" in token:
                die("REDDIT_TOKEN contains invalid characters")
            return cls("oauth", token=token)
        raw_cookies = os.environ.get("REDDIT_COOKIES", "").strip()
        if raw_cookies:
            return cls("cookie", cookies=parse_cookie_jar(raw_cookies))
        die(
            "No Reddit credential is available — connect Reddit with Cookie or OAuth at "
            "https://auth.acedata.cloud/user/connections."
        )

    @property
    def base_url(self) -> str:
        return WEB_BASE if self.mode == "cookie" else OAUTH_BASE

    def request(self, method: str, path: str, *, query: dict | None = None, form: dict | None = None):
        is_write = method.upper() == "POST"
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }
        if self.mode == "oauth":
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            headers.update({"Origin": WEB_BASE, "Referer": WEB_BASE + "/", "X-Requested-With": "XMLHttpRequest"})

        data = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        if self.mode == "cookie":
            request.add_unredirected_header("Cookie", cookie_header(self.cookies, url))

        try:
            with open_request(request) as response:
                status = response.status
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
        except urllib.error.HTTPError as error:
            try:
                status = error.code
                raw = error.read()
                if error.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            except Exception:
                if is_write:
                    die_unknown_write_outcome("The Reddit HTTP error response for the write request could not be read")
                die("The Reddit HTTP error response could not be read; authenticated response content was omitted.")
            finally:
                with contextlib.suppress(Exception):
                    error.close()
        except urllib.error.URLError as error:
            if is_write:
                die_unknown_write_outcome("A network error interrupted the Reddit write request")
            die(f"network error reaching Reddit: {error.reason}")
        except Exception:
            if is_write:
                die_unknown_write_outcome("The Reddit write response could not be read or decompressed")
            die("The Reddit response could not be read or decompressed; authenticated response content was omitted.")

        text = raw.decode("utf-8", "replace")
        if 300 <= status < 400:
            if is_write:
                die_unknown_write_outcome("Reddit redirected the write request; credentials were not forwarded")
            die("Reddit returned an unexpected redirect; credentials were not forwarded. Reconnect before retrying the read.")
        if status in {401, 403}:
            die(
                f"Reddit authentication failed ({status}) — the credential may be expired or blocked. "
                "Reconnect at https://auth.acedata.cloud/user/connections."
            )
        if status == 429:
            die("Reddit rate limit reached (429). Wait before retrying; do not loop-retry.")
        if status >= 400:
            if is_write and status >= 500:
                die_unknown_write_outcome(f"Reddit returned HTTP {status} for the write request")
            die(f"Reddit returned HTTP {status}; authenticated response content was omitted.")
        if text.lstrip().startswith("<"):
            if is_write:
                die_unknown_write_outcome("Reddit returned HTML for the write request")
            die("Reddit returned HTML instead of JSON — the session expired or the web endpoint changed.")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if is_write:
                die_unknown_write_outcome("Reddit returned invalid JSON for the write request")
            die(f"Reddit returned non-JSON data ({status}); authenticated response content was omitted.")

    def me(self) -> dict:
        if self.mode == "cookie":
            payload = self.request("GET", "/api/me.json", query={"raw_json": 1})
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
                die("Reddit returned a malformed identity response; authenticated response content was omitted.")
            data = payload["data"]
            self.modhash = str(data.get("modhash") or "")
        else:
            data = self.request("GET", "/api/v1/me")
            if not isinstance(data, dict):
                die("Reddit returned a malformed identity response; authenticated response content was omitted.")
        self.username = str(data.get("name") or "")
        if not self.username:
            die("Reddit did not return an authenticated username — reconnect the account.")
        return data

    def submissions(self, limit: int) -> list[dict]:
        username = self.username or str(self.me().get("name") or "")
        suffix = ".json" if self.mode == "cookie" else ""
        payload = self.request(
            "GET",
            f"/user/{urllib.parse.quote(username, safe='')}/submitted{suffix}",
            query={"limit": limit, "raw_json": 1},
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            die("Reddit returned a malformed submissions response; authenticated response content was omitted.")
        children = payload["data"].get("children")
        if not isinstance(children, list) or any(
            not isinstance(child, dict)
            or not valid_submission_data(child.get("data"))
            for child in children
        ):
            die("Reddit returned a malformed submissions response; authenticated response content was omitted.")
        return [child["data"] for child in children]

    def submit(self, *, subreddit: str, title: str, kind: str, text: str = "", url: str = "") -> dict:
        if self.mode == "cookie" and not self.modhash:
            self.me()
        form = {
            "api_type": "json",
            "kind": kind,
            "sr": subreddit,
            "title": title,
            "resubmit": "true",
            "sendreplies": "true",
            "raw_json": "1",
        }
        if kind == "self":
            form["text"] = text
        else:
            form["url"] = url
        if self.mode == "cookie":
            if not self.modhash:
                die("Reddit did not return a modhash; the Cookie session cannot perform writes.")
            form["uh"] = self.modhash

        payload = self.request("POST", "/api/submit", form=form)
        if not isinstance(payload, dict) or not isinstance(payload.get("json"), dict):
            die_unknown_post_response()
        json_payload = payload["json"]
        errors = json_payload.get("errors")
        if not isinstance(errors, list):
            die_unknown_post_response()
        if errors:
            die(
                "Reddit rejected the post. Check subreddit rules, account eligibility, "
                "flair requirements and rate limits; authenticated error details were omitted."
            )
        post = json_payload.get("data")
        if not isinstance(post, dict):
            die_unknown_post_response()
        post_url = post.get("url") or post.get("permalink")
        if not isinstance(post_url, str) or not post_url:
            die_unknown_post_response()
        if post_url.startswith("/"):
            post_url = WEB_BASE + post_url
        parsed_post_url = urllib.parse.urlsplit(post_url)
        if parsed_post_url.scheme != "https" or not parsed_post_url.hostname or not reddit_cookie_domain(
            parsed_post_url.hostname
        ):
            die_unknown_post_response()
        return {"ok": True, "posted": True, "id": post.get("id"), "name": post.get("name"), "url": post_url}


def format_profile(data: dict, mode: str) -> dict:
    return {
        "auth_mode": mode,
        "id": data.get("id"),
        "name": data.get("name"),
        "total_karma": data.get("total_karma"),
        "link_karma": data.get("link_karma"),
        "comment_karma": data.get("comment_karma"),
        "created_utc": data.get("created_utc"),
    }


def valid_submission_data(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    required_strings = ("id", "title", "subreddit", "permalink")
    return all(isinstance(item.get(key), str) and item.get(key) for key in required_strings) and str(
        item["permalink"]
    ).startswith("/")


def die_unknown_write_outcome(reason: str) -> None:
    die(
        f"{reason}; authenticated response content was omitted and the post outcome is unknown. "
        "Check recent submissions before taking any further action and do not replay automatically."
    )


def die_unknown_post_response() -> None:
    die_unknown_write_outcome("Reddit returned a malformed write response")


def format_submission(item: dict) -> dict:
    permalink = item.get("permalink")
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "subreddit": item.get("subreddit"),
        "url": WEB_BASE + permalink if isinstance(permalink, str) and permalink.startswith("/") else item.get("url"),
        "score": item.get("score"),
        "num_comments": item.get("num_comments"),
        "created_utc": item.get("created_utc"),
    }


def dry_run(args: argparse.Namespace) -> None:
    value = {
        "dry_run": True,
        "command": args.command,
        "subreddit": normalize_subreddit(args.subreddit),
        "title": validate_title(args.title),
        "note": "No request was sent. Re-run with --confirm as the final argument after explicit user approval.",
    }
    if args.command == "submit-text":
        value["text_length"] = len(read_text(args))
    else:
        value["url"] = validate_link(args.url)
    output(value)


def positive_limit(value: str) -> int:
    parsed = int(value)
    if parsed < 1 or parsed > 100:
        raise argparse.ArgumentTypeError("limit must be between 1 and 100")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reddit via OAuth or login cookies")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("whoami", help="show the connected Reddit identity")

    submissions = commands.add_parser("submissions", help="list my recent submissions")
    submissions.add_argument("--limit", type=positive_limit, default=10)

    text_post = commands.add_parser("submit-text", help="submit a text post (gated)")
    text_post.add_argument("--subreddit", "-r", required=True)
    text_post.add_argument("--title", required=True)
    text_source = text_post.add_mutually_exclusive_group(required=True)
    text_source.add_argument("--text")
    text_source.add_argument("--text-file", dest="text_file")

    link_post = commands.add_parser("submit-link", help="submit a link post (gated)")
    link_post.add_argument("--subreddit", "-r", required=True)
    link_post.add_argument("--title", required=True)
    link_post.add_argument("--url", required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parsed_argv, confirmed = split_confirmation(raw_argv)
    args = build_parser().parse_args(parsed_argv)

    if args.command in GATED_COMMANDS and not confirmed:
        dry_run(args)
        return

    client = RedditClient.from_environment()
    if args.command == "whoami":
        output(format_profile(client.me(), client.mode))
        return
    if args.command == "submissions":
        items = client.submissions(args.limit)
        output({"auth_mode": client.mode, "count": len(items), "submissions": [format_submission(item) for item in items]})
        return

    subreddit = normalize_subreddit(args.subreddit)
    title = validate_title(args.title)
    if args.command == "submit-text":
        output(client.submit(subreddit=subreddit, title=title, kind="self", text=read_text(args)))
    elif args.command == "submit-link":
        output(client.submit(subreddit=subreddit, title=title, kind="link", url=validate_link(args.url)))


if __name__ == "__main__":
    main()
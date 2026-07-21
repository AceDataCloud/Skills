from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "habr.py"
SPEC = importlib.util.spec_from_file_location("habr_skill_script", SCRIPT)
habr = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = habr
SPEC.loader.exec_module(habr)


def cookies():
    return [
        {"name": "session", "value": "secret", "domain": ".habr.com"},
        {"name": "host", "value": "valid", "domain": "habr.com"},
        {"name": "child", "value": "skip", "domain": "account.habr.com"},
        {"name": "empty", "value": "skip", "domain": ""},
        {"name": "evil", "value": "leak", "domain": ".evil.example"},
    ]


def test_cookie_header_only_includes_habr_domains() -> None:
    value = habr.cookie_header(cookies())
    assert value == "session=secret; host=valid"
    assert "leak" not in value and "skip" not in value


def test_raw_request_rejects_non_habr_hosts() -> None:
    with pytest.raises(SystemExit):
        habr.raw_request("GET", "https://evil.example/", cookies())


def test_save_dry_run_does_not_read_cookie_or_network(tmp_path: pathlib.Path) -> None:
    payload = tmp_path / "draft.json"
    payload.write_text('{"title":"Hello","textMarkdown":"Body"}', encoding="utf-8")
    stream = io.StringIO()
    with patch.dict(os.environ, {"HABR_COOKIES": json.dumps(cookies())}, clear=True), patch.object(
        habr, "request"
    ) as request, redirect_stdout(stream):
        old_args, old_confirmed = habr.ARGS, habr.CONFIRMED
        try:
            habr.ARGS = ["save", "--id", "123", "--payload-file", str(payload)]
            habr.CONFIRMED = False
            habr.main()
        finally:
            habr.ARGS, habr.CONFIRMED = old_args, old_confirmed
    value = json.loads(stream.getvalue())
    assert value["dry_run"] is True
    assert value["operation"] == "save"
    assert value["request"]["title"] == "Hello"
    assert value["request"]["idempotenceKey"]
    request.assert_not_called()
    assert "secret" not in stream.getvalue()

    stream2 = io.StringIO()
    with patch.dict(os.environ, {"HABR_COOKIES": json.dumps(cookies())}, clear=True), patch.object(
        habr, "request"
    ) as request2, redirect_stdout(stream2):
        old_args, old_confirmed = habr.ARGS, habr.CONFIRMED
        try:
            habr.ARGS = ["save", "--id", "123", "--payload-file", str(payload)]
            habr.CONFIRMED = False
            habr.main()
        finally:
            habr.ARGS, habr.CONFIRMED = old_args, old_confirmed
    assert json.loads(stream2.getvalue())["request"]["idempotenceKey"] == value["request"]["idempotenceKey"]
    request2.assert_not_called()


def test_write_timeout_is_ambiguous() -> None:
    with patch.object(habr, "raw_request", side_effect=TimeoutError("timeout")), redirect_stdout(io.StringIO()):
        with pytest.raises(SystemExit):
            habr.request("POST", "/publication/save/123", cookies(), {}, write=True)


def test_write_5xx_is_ambiguous() -> None:
    with patch.object(habr, "csrf_token", return_value="csrf"), patch.object(
        habr, "raw_request", return_value=(500, '{"message":"error"}')
    ), redirect_stdout(io.StringIO()):
        with pytest.raises(SystemExit):
            habr.request("POST", "/publication/save/123", cookies(), {}, write=True)


def test_redirect_handler_refuses_redirects() -> None:
    assert habr.NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://evil.example") is None


def test_preview_requires_csrf_without_write_ambiguity() -> None:
    with patch.object(habr, "csrf_token", return_value="csrf"), patch.object(
        habr, "raw_request", return_value=(200, '{"preview":true}')
    ) as raw:
        result = habr.request("POST", "/publication/preview", cookies(), {"title": "T"}, csrf_required=True)
    assert result == {"preview": True}
    assert raw.call_args.args[-1] == "csrf"


def test_find_article_url_requires_real_habr_article_url() -> None:
    assert habr.find_article_url({"url": "https://habr.com/ru/articles/123/"}) == "https://habr.com/ru/articles/123/"
    assert habr.find_article_url({"url": "https://evil.example/ru/articles/123/"}) is None


def test_idempotence_key_changes_with_payload_and_ignores_stale_key() -> None:
    first = habr.idempotence_key({"title": "A", "idempotenceKey": "stale"})
    same = habr.idempotence_key({"title": "A", "idempotenceKey": "other"})
    changed = habr.idempotence_key({"title": "B", "idempotenceKey": "stale"})
    assert first == same
    assert changed != first


def test_publish_verification_failure_warns_not_to_republish() -> None:
    stream = io.StringIO()
    with patch.dict(os.environ, {"HABR_COOKIES": json.dumps(cookies())}, clear=True), patch.object(
        habr, "request", side_effect=[{"status": "accepted"}, habr.HabrError("verification failed")]
    ), redirect_stdout(stream), pytest.raises(SystemExit):
        old_args, old_confirmed = habr.ARGS, habr.CONFIRMED
        try:
            habr.ARGS = ["publish", "--id", "123"]
            habr.CONFIRMED = True
            habr.main()
        finally:
            habr.ARGS, habr.CONFIRMED = old_args, old_confirmed
    assert "Do not publish again" in json.loads(stream.getvalue())["error"]


def test_publish_missing_url_warns_not_to_republish_once() -> None:
    stream = io.StringIO()
    with patch.dict(os.environ, {"HABR_COOKIES": json.dumps(cookies())}, clear=True), patch.object(
        habr, "request", side_effect=[{"status": "accepted"}, {"id": "123"}]
    ), redirect_stdout(stream), pytest.raises(SystemExit):
        old_args, old_confirmed = habr.ARGS, habr.CONFIRMED
        try:
            habr.ARGS = ["publish", "--id", "123"]
            habr.CONFIRMED = True
            habr.main()
        finally:
            habr.ARGS, habr.CONFIRMED = old_args, old_confirmed
    value = json.loads(stream.getvalue())
    assert "Do not publish again" in value["error"]
    assert "verify --id 123" in value["error"]

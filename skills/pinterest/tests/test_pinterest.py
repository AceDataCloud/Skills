from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
from unittest.mock import patch

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "pinterest.py"

SPEC = importlib.util.spec_from_file_location("pinterest_skill_script", SCRIPT)
pinterest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = pinterest
SPEC.loader.exec_module(pinterest)

def run_create(image_url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "create",
            "--board-id",
            "board-1",
            "--title",
            "Hello",
            "--description",
            "Description",
            "--link",
            "https://example.com/article",
            "--image-url",
            image_url,
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PINTEREST_TOKEN": "super-secret-token"},
    )


def test_create_dry_run_builds_official_image_url_payload_without_network() -> None:
    result = run_create("https://cdn.example.com/pin.jpg")
    assert result.returncode == 0
    value = json.loads(result.stdout)
    assert value["dry_run"] is True
    assert value["request"] == {
        "board_id": "board-1",
        "title": "Hello",
        "description": "Description",
        "media_source": {"source_type": "image_url", "url": "https://cdn.example.com/pin.jpg"},
        "link": "https://example.com/article",
    }
    assert "super-secret-token" not in result.stdout


def test_create_rejects_non_https_image_url() -> None:
    result = run_create("http://cdn.example.com/pin.jpg")
    assert result.returncode == 1
    assert json.loads(result.stdout)["error"] == "--image-url must be a public HTTPS URL"


def test_redirect_handler_refuses_to_forward_bearer_token() -> None:
    handler = pinterest.NoRedirect()
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/") is None


def test_write_network_failure_is_reported_as_ambiguous() -> None:
    opener = pinterest.urllib.request.OpenerDirector()
    opener.open = lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("timeout"))
    with patch.dict(os.environ, {"PINTEREST_TOKEN": "secret"}, clear=True), patch.object(
        pinterest.urllib.request, "build_opener", return_value=opener
    ), pytest.raises(SystemExit) as exc:
        pinterest.request("POST", "/pins", {"title": "Hello"})
    assert exc.value.code == 1


def test_write_server_error_is_reported_as_ambiguous() -> None:
    error = urllib.error.HTTPError("https://api.pinterest.com/v5/pins", 500, "error", {}, None)
    opener = pinterest.urllib.request.OpenerDirector()
    opener.open = lambda *_args, **_kwargs: (_ for _ in ()).throw(error)
    with patch.dict(os.environ, {"PINTEREST_TOKEN": "secret"}, clear=True), patch.object(
        pinterest.urllib.request, "build_opener", return_value=opener
    ), pytest.raises(SystemExit) as exc:
        pinterest.request("POST", "/pins", {"title": "Hello"})
    assert exc.value.code == 1


def test_malformed_read_response_uses_structured_error() -> None:
    response = type(
        "Response",
        (),
        {
            "__enter__": lambda self: self,
            "__exit__": lambda self, *_args: False,
            "read": lambda self: b"not-json",
        },
    )()
    opener = pinterest.urllib.request.OpenerDirector()
    opener.open = lambda *_args, **_kwargs: response
    with patch.dict(os.environ, {"PINTEREST_TOKEN": "secret"}, clear=True), patch.object(
        pinterest.urllib.request, "build_opener", return_value=opener
    ), pytest.raises(SystemExit) as exc:
        pinterest.request("GET", "/user_account")
    assert exc.value.code == 1

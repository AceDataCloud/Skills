from __future__ import annotations

import base64
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from unittest.mock import patch

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "ghost.py"
SPEC = importlib.util.spec_from_file_location("ghost_skill_script", SCRIPT)
ghost = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = ghost
SPEC.loader.exec_module(ghost)


def decode_segment(value: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def test_admin_token_uses_ghost_audience_and_five_minute_lifetime() -> None:
    with patch.object(ghost.time, "time", return_value=1_700_000_000):
        token = ghost.admin_token("key-id:00112233445566778899aabbccddeeff")

    header, payload, signature = token.split(".")
    assert decode_segment(header) == {"alg": "HS256", "kid": "key-id", "typ": "JWT"}
    assert decode_segment(payload) == {"iat": 1_700_000_000, "exp": 1_700_000_300, "aud": "/admin/"}
    assert signature


def test_create_dry_run_never_requires_or_exposes_credentials(tmp_path: pathlib.Path) -> None:
    html = tmp_path / "post.html"
    html.write_text("<p>Hello</p>", encoding="utf-8")
    env = {**os.environ, "GHOST_ADMIN_API_KEY": "secret-id:001122", "GHOST_SITE_URL": "https://ghost.example"}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "create", "--title", "Hello", "--html-file", str(html)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    value = json.loads(result.stdout)
    assert value["dry_run"] is True
    assert value["request"]["posts"][0]["status"] == "draft"
    assert "secret-id" not in result.stdout


def test_config_rejects_non_https_site() -> None:
    with patch.dict(os.environ, {"GHOST_SITE_URL": "http://ghost.example", "GHOST_ADMIN_API_KEY": "id:00"}, clear=True):
        try:
            ghost.config()
        except SystemExit:
            pass
        else:
            raise AssertionError("non-HTTPS Ghost site was accepted")


@pytest.mark.parametrize(
    "site",
    [
        "https://blog.example@evil.example",
        "https://127.0.0.1",
        "https://10.0.0.1",
        "https://ghost.example/path",
        "https://ghost.example?target=evil",
        "https://ghost.example#fragment",
    ],
)
def test_config_rejects_unsafe_site_roots(site: str) -> None:
    with patch.dict(os.environ, {"GHOST_SITE_URL": site, "GHOST_ADMIN_API_KEY": "id:00"}, clear=True), patch.object(
        ghost.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("203.0.113.10", 443))]
    ):
        with pytest.raises(SystemExit):
            ghost.config()


def test_config_rejects_hostname_resolving_to_private_address() -> None:
    with patch.dict(
        os.environ,
        {"GHOST_SITE_URL": "https://ghost.example", "GHOST_ADMIN_API_KEY": "id:00"},
        clear=True,
    ), patch.object(ghost.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("10.0.0.5", 443))]), pytest.raises(
        SystemExit
    ):
        ghost.config()


def test_pinned_connection_uses_validated_ip_and_original_tls_hostname() -> None:
    connection = ghost.PinnedHTTPSConnection("ghost.example", 443, "93.184.216.34")
    raw_socket = object()
    tls_socket = object()
    with patch.object(ghost.socket, "create_connection", return_value=raw_socket) as create, patch.object(
        connection._context, "wrap_socket", return_value=tls_socket
    ) as wrap:
        connection.connect()
    create.assert_called_once_with(("93.184.216.34", 443), 30, None)
    wrap.assert_called_once_with(raw_socket, server_hostname="ghost.example")
    assert connection.sock is tls_socket


def test_write_network_failure_is_reported_as_ambiguous() -> None:
    connection = ghost.PinnedHTTPSConnection("ghost.example", 443, "93.184.216.34")
    connection.request = lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("timeout"))
    with patch.dict(
        os.environ,
        {"GHOST_SITE_URL": "https://ghost.example", "GHOST_ADMIN_API_KEY": "id:001122"},
        clear=True,
    ), patch.object(
        ghost.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]
    ), patch.object(ghost, "PinnedHTTPSConnection", return_value=connection), pytest.raises(SystemExit) as exc:
        ghost.request("POST", "/posts/?source=html", {"posts": [{"title": "Hello"}]})
    assert exc.value.code == 1


def test_write_server_error_is_reported_as_ambiguous() -> None:
    response = type("Response", (), {"status": 500, "read": lambda self: b'{"errors":[]}'} )()
    connection = ghost.PinnedHTTPSConnection("ghost.example", 443, "93.184.216.34")
    connection.request = lambda *_args, **_kwargs: None
    connection.getresponse = lambda: response
    with patch.dict(
        os.environ,
        {"GHOST_SITE_URL": "https://ghost.example", "GHOST_ADMIN_API_KEY": "id:001122"},
        clear=True,
    ), patch.object(
        ghost.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]
    ), patch.object(ghost, "PinnedHTTPSConnection", return_value=connection), pytest.raises(SystemExit) as exc:
        ghost.request("POST", "/posts/?source=html", {"posts": [{"title": "Hello"}]})
    assert exc.value.code == 1

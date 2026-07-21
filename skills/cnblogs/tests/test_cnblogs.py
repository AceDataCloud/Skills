from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import sys
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "cnblogs.py"
SPEC = importlib.util.spec_from_file_location("cnblogs_skill_script", SCRIPT)
cnblogs = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = cnblogs
SPEC.loader.exec_module(cnblogs)


class FakeResponse:
    def __init__(self, payload=None, *, raw=None):
        self.payload = raw if raw is not None else (b"" if payload is None else json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def make_client(*responses):
    opener = MagicMock()
    opener.open.side_effect = [FakeResponse(item) for item in responses]
    return cnblogs.CNBlogsClient("secret-token", opener=opener), opener


def test_request_uses_official_pat_contract():
    client, opener = make_client({"postList": []})
    assert client.posts(20) == []
    request = opener.open.call_args.args[0]
    assert request.full_url == "https://write.cnblogs.com/api/posts/list?t=1&p=1&s=20"
    assert request.get_header("Authorization") == "Bearer secret-token"
    assert request.get_header("Authorization-type") == "pat"


def test_create_uses_server_template_and_returns_real_api_url():
    template = {"blogPost": {"id": -1, "blogId": 7, "isAllowComments": True}}
    saved = {"id": 123, "title": "Hello", "url": "https://www.cnblogs.com/alice/p/123"}
    client, opener = make_client(template, saved)
    args = cnblogs.build_parser().parse_args(
        ["create", "--title", "Hello", "--content", "# Body", "--category-ids", "12,34", "--tags", "api, agent"]
    )

    result = client.save(cnblogs.apply_post_fields(client.template(), args, "# Body"))

    assert result["url"] == "https://www.cnblogs.com/alice/p/123"
    request = opener.open.call_args_list[1].args[0]
    payload = json.loads(request.data)
    assert payload["blogId"] == 7
    assert payload["postBody"] == "# Body"
    assert payload["isMarkdown"] is True
    assert payload["categoryIds"] == [12, 34]
    assert payload["tags"] == ["api", "agent"]
    assert payload["isPublished"] is False
    assert payload["isDraft"] is True


def test_dry_run_never_loads_credentials_or_calls_network():
    stream = io.StringIO()
    with patch.dict(os.environ, {}, clear=True), patch.object(
        cnblogs.CNBlogsClient, "from_environment"
    ) as from_environment, redirect_stdout(stream):
        cnblogs.main(["create", "--title", "Hello", "--content", "Body"])

    value = json.loads(stream.getvalue())
    assert value["dry_run"] is True
    assert value["visibility"] == "draft"
    from_environment.assert_not_called()


def test_confirm_is_recognized_only_as_final_argument():
    args, confirmed = cnblogs.split_confirmation(["create", "--content", "--confirm", "--title", "Hello"])
    assert confirmed is False
    assert "--confirm" in args
    args, confirmed = cnblogs.split_confirmation(["delete", "123", "--confirm"])
    assert confirmed is True
    assert "--confirm" not in args


def test_successful_create_update_and_delete_commands():
    template = {"blogPost": {"id": -1}}
    created = {"id": 123, "title": "New", "url": "https://www.cnblogs.com/a/p/123"}
    client, _ = make_client(template, created)
    stream = io.StringIO()
    with patch.object(cnblogs.CNBlogsClient, "from_environment", return_value=client), redirect_stdout(stream):
        cnblogs.main(["create", "--title", "New", "--content", "Body", "--confirm"])
    create_output = json.loads(stream.getvalue())
    assert create_output["url"] == created["url"]
    assert create_output["published"] is False
    assert create_output["draft"] is True

    current = {"blogPost": {"id": 123, "title": "Old", "categoryIds": [9], "tags": ["keep"]}}
    updated = {"id": 123, "title": "Updated", "url": "https://www.cnblogs.com/a/p/123"}
    client, opener = make_client(current, updated)
    stream = io.StringIO()
    with patch.object(cnblogs.CNBlogsClient, "from_environment", return_value=client), redirect_stdout(stream):
        cnblogs.main(["update", "123", "--title", "Updated", "--content", "Body", "--publish", "--confirm"])
    update_output = json.loads(stream.getvalue())
    assert update_output["published"] is True
    assert update_output["draft"] is False
    update_payload = json.loads(opener.open.call_args_list[1].args[0].data)
    assert update_payload["categoryIds"] == [9]
    assert update_payload["tags"] == ["keep"]

    opener = MagicMock()
    opener.open.return_value = FakeResponse(raw=b"successful response with no JSON contract")
    client = cnblogs.CNBlogsClient("secret-token", opener=opener)
    stream = io.StringIO()
    with patch.object(cnblogs.CNBlogsClient, "from_environment", return_value=client), redirect_stdout(stream):
        cnblogs.main(["delete", "123", "--confirm"])
    assert json.loads(stream.getvalue()) == {"ok": True, "post_id": 123, "deleted": True}


@pytest.mark.parametrize(("method", "path"), [("POST", "/posts"), ("DELETE", "/posts/123")])
def test_write_network_failure_reports_unknown_outcome(method, path):
    opener = MagicMock()
    opener.open.side_effect = urllib.error.URLError("secret-token")
    client = cnblogs.CNBlogsClient("secret-token", opener=opener)
    stream = io.StringIO()
    with pytest.raises(SystemExit), redirect_stdout(stream):
        client.request(method, path, body={} if method == "POST" else None, write=True)
    assert "outcome is unknown" in stream.getvalue()
    assert "secret-token" not in stream.getvalue()


def test_rejects_malformed_responses_and_oversized_content(tmp_path):
    client, _ = make_client({"blogPost": None})
    with pytest.raises(SystemExit), redirect_stdout(io.StringIO()):
        client.template()

    large = tmp_path / "large.md"
    large.write_bytes(b"x" * (cnblogs.MAX_CONTENT_BYTES + 1))
    args = cnblogs.build_parser().parse_args(["create", "--title", "T", "--content-file", str(large)])
    with pytest.raises(SystemExit), redirect_stdout(io.StringIO()):
        cnblogs.read_content(args)
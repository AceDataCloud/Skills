from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "personal_wechat.py"
SPEC = importlib.util.spec_from_file_location("personal_wechat_skill_script", SCRIPT)
assert SPEC and SPEC.loader
sys.path.insert(0, str(SCRIPT.parent))
personal_wechat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(personal_wechat)


# Routes Wisdom removed. The skill kept calling all of these until they started
# 404ing in production; keep them from creeping back in.
RETIRED_ROUTES = (
    "/api/auth/status",
    "/api/conversations/history",
    "/api/messages/history",
    "/api/messages/history/query",
    "/api/messages/history/refresh",
)


def run(argv: list[str], *, responses=None, task_result=None):
    """Invoke main() with argv, capturing every HTTP call the CLI would make."""
    calls: list[dict] = []

    def fake_request(method, path, *, params=None, body=None):
        calls.append({"method": method, "path": path, "params": params, "body": body})
        if responses and path in responses:
            return responses[path]
        if path.startswith("/api/tasks/"):
            return {"status": "succeeded", "result": task_result}
        return {} if method == "GET" else {"id": "task-1"}

    printed: list[str] = []
    with patch.object(personal_wechat, "request", side_effect=fake_request):
        with patch("builtins.print", side_effect=lambda *a, **k: printed.append(a[0] if a else "")):
            with patch.object(sys, "argv", ["personal_wechat.py", *argv]):
                personal_wechat.main()

    stdout = [json.loads(line) for line in printed if isinstance(line, str) and line.startswith(("{", "["))]
    return calls, stdout


def test_wait_task_returns_successful_result() -> None:
    with patch.object(
        personal_wechat,
        "request",
        return_value={"status": "succeeded", "result": {"sent": True}},
    ):
        result = personal_wechat.wait_task("task-1", timeout=0.1)

    assert result == {"sent": True}


def test_script_references_no_retired_routes() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    for route in RETIRED_ROUTES:
        assert route not in source, f"{route} was removed from Wisdom"


def test_skill_doc_references_no_retired_routes() -> None:
    doc = (SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")
    for route in RETIRED_ROUTES:
        assert route not in doc, f"{route} was removed from Wisdom"


def test_status_only_reads_api_status() -> None:
    """The 404 outage: status also probed /api/auth/status, failing the whole command."""
    calls, _ = run(["status"], responses={"/api/status": {"status": "ready", "logged_in": True}})

    assert [c["path"] for c in calls] == ["/api/status"]


@pytest.mark.parametrize(
    "argv,ceiling,path,response",
    [
        (["contacts", "--limit", "500"], 200, "/api/contacts", {"total": 0, "contacts": []}),
        (["conversations", "--limit", "500"], 200, "/api/conversations", {"total": 0, "conversations": []}),
        (["messages", "CONV", "--limit", "500"], 200, "/api/messages", []),
        (["poll", "--since", "1", "--limit", "5000"], 500, "/api/messages/poll", []),
    ],
)
def test_limit_is_clamped_instead_of_422(argv, ceiling, path, response) -> None:
    calls, _ = run(argv, responses={path: response})

    assert calls[0]["params"]["limit"] == ceiling


def test_send_dry_runs_by_default() -> None:
    calls, stdout = run(["send", "Alice", "hi"])

    assert calls == []
    assert stdout[0]["dry_run"] is True


def test_send_with_confirm_posts_the_payload() -> None:
    calls, _ = run(["send", "Alice", "hi", "--confirm"], task_result={"sent": True})

    assert calls[0]["path"] == "/api/messages/send"
    assert calls[0]["body"] == {"target": "Alice", "type": "text", "text": "hi"}


def test_mentions_go_to_the_api_not_into_the_text() -> None:
    """A pasted '@Name' notifies nobody; only the mentions field is a real @-mention."""
    calls, _ = run(
        ["send", "项目群", "周报", "--mention", "Doms Jay", "--mention", "Alice", "--confirm"],
        task_result={"sent": True},
    )

    body = calls[0]["body"]
    assert body["mentions"] == ["Doms Jay", "Alice"]
    assert body["text"] == "周报"


def test_mention_all_is_forwarded() -> None:
    calls, _ = run(["send", "项目群", "通知", "--mention-all", "--confirm"], task_result={"sent": True})

    assert calls[0]["body"]["mention_all"] is True


def test_quote_and_idempotency_key_are_forwarded() -> None:
    calls, _ = run(
        ["send", "Alice", "我来跟", "--quote-text", "谁跟一下", "--idempotency-key", "k-1", "--confirm"],
        task_result={"sent": True},
    )

    body = calls[0]["body"]
    assert body["quote_text"] == "谁跟一下"
    assert body["idempotency_key"] == "k-1"


def test_media_send_requires_its_url() -> None:
    with pytest.raises(SystemExit):
        run(["send", "Alice", "--type", "image", "--confirm"])


def test_media_send_forwards_the_url() -> None:
    calls, _ = run(
        ["send", "Alice", "--type", "image", "--image-url", "https://example.com/a.png", "--confirm"],
        task_result={"sent": True},
    )

    assert calls[0]["body"]["image_url"] == "https://example.com/a.png"


@pytest.mark.parametrize(
    "argv,path,method",
    [
        (["moment-post", "hello"], "/api/moments", "POST"),
        (["moment-delete", "some distinctive text"], "/api/moments", "DELETE"),
        (["group-create", "Alice", "Bob"], "/api/groups", "POST"),
        (["group-invite", "项目群", "Carol"], "/api/groups/invite", "POST"),
        (["group-remove", "项目群", "Carol"], "/api/groups/remove", "POST"),
        (["group-rename", "项目群", "新名字"], "/api/groups/rename", "POST"),
    ],
)
def test_every_write_dry_runs_then_executes(argv, path, method) -> None:
    dry_calls, stdout = run(argv)
    assert dry_calls == [], f"{argv[0]} must not touch the API without --confirm"
    assert stdout[0]["dry_run"] is True

    calls, _ = run([*argv, "--confirm"], task_result={"ok": True})
    assert calls[0]["path"] == path
    assert calls[0]["method"] == method


def test_group_create_needs_two_members() -> None:
    with pytest.raises(SystemExit):
        run(["group-create", "Alice", "--confirm"])


def test_moment_post_needs_text_or_images() -> None:
    with pytest.raises(SystemExit):
        run(["moment-post", "--confirm"])


def test_unattended_confirm_is_denied_outside_a_scheduled_task(monkeypatch) -> None:
    monkeypatch.delenv("AICHAT_UNATTENDED_MODE", raising=False)
    calls, stdout = run(["send", "Alice", "hi", "--unattended-confirm"])

    assert calls == []
    assert stdout[0]["error"] == "unattended_confirmation_denied"


def test_unattended_confirm_allows_a_preauthorized_skill(monkeypatch) -> None:
    monkeypatch.setenv("AICHAT_UNATTENDED_MODE", "true")
    monkeypatch.setenv("AICHAT_ACTIVE_SKILL", "acedatacloud/personal-wechat")
    monkeypatch.setenv("AICHAT_UNATTENDED_ALLOWED_SKILLS", '["acedatacloud/personal-wechat"]')
    calls, _ = run(["send", "Alice", "hi", "--unattended-confirm"], task_result={"sent": True})

    assert calls[0]["path"] == "/api/messages/send"

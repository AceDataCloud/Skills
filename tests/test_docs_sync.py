from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_claude_messages_effort_is_documented() -> None:
    body = (ROOT / "skills" / "ai-chat" / "SKILL.md").read_text()

    assert "`POST /v1/messages`" in body
    assert "`output_config.effort` accepts" in body
    assert '"xhigh"' in body
    assert '"max"' in body


def test_seedance_web_search_limits_are_documented() -> None:
    body = (ROOT / "skills" / "seedance-video" / "SKILL.md").read_text()

    assert "At most one Seedance 2.5 `web_search` tool" in body
    assert "`limit` / `max_keyword` are 1–50" in body
    assert "`search_engine`" in body


def test_kling_async_and_motion_contract_are_documented() -> None:
    body = (ROOT / "skills" / "kling-video" / "SKILL.md").read_text()

    assert '"action": "retrieve"' in body
    assert "`model_name` (`/kling/motion`)" in body
    assert "`keep_original_sound` (`/kling/motion`)" in body
    assert "`async` | `true`, `false`" in body

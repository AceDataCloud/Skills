from pathlib import Path


SKILLS_DIR = Path(__file__).parents[2]
BROWSER_CORE = Path(__file__).parents[1] / "contracts" / "browser-manifest.compact.json"
TIKTOK_SKILL = SKILLS_DIR / "tiktok" / "SKILL.md"


def test_browser_core_has_no_xiaohongshu_or_tiktok_semantics() -> None:
    core = BROWSER_CORE.read_text(encoding="utf-8").casefold()

    for site_term in (
        "xiaohongshu",
        "creator.xiaohongshu.com",
        "tiktok",
        "open.tiktokapis.com",
        "publish_id",
        "pull_from_url",
    ):
        assert site_term not in core


def test_tiktok_remains_an_api_skill_until_browser_canary_is_approved() -> None:
    skill = TIKTOK_SKILL.read_text(encoding="utf-8")

    assert "allowed_tools: [Bash]" in skill
    assert "https://open.tiktokapis.com/v2" in skill
    assert "execution:\n  browser:" not in skill
    assert "browser." not in skill

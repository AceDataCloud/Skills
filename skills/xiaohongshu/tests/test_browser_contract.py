from __future__ import annotations

import re
from pathlib import Path


SKILL_DIR = Path(__file__).parents[1]
SKILL = SKILL_DIR / "SKILL.md"
EXPECTED_ORIGINS = {
    "https://www.xiaohongshu.com",
    "https://creator.xiaohongshu.com",
}
EXPECTED_CAPABILITIES = {
    "tabs",
    "read_page",
    "screenshot",
    "navigate",
    "trusted_input",
}


def _frontmatter(text: str) -> str:
    assert text.startswith("---\n")
    parts = text.split("---\n")
    assert len(parts) == 3
    return parts[1]


def _nested_list(frontmatter: str, key: str) -> set[str]:
    match = re.search(
        rf"^    {re.escape(key)}:\n((?:      - .+\n)+)",
        frontmatter,
        re.MULTILINE,
    )
    assert match, f"missing execution.browser.{key}"
    return {
        line.removeprefix("      - ").strip()
        for line in match.group(1).splitlines()
    }


def test_browser_execution_frontmatter_contract() -> None:
    frontmatter = _frontmatter(SKILL.read_text(encoding="utf-8"))

    assert re.search(r"^execution:\n  browser:\n", frontmatter, re.MULTILINE)
    assert _nested_list(frontmatter, "origins") == EXPECTED_ORIGINS
    assert _nested_list(frontmatter, "capabilities") == EXPECTED_CAPABILITIES
    assert not re.search(r"^allowed_tools:.*\bBash\b", frontmatter, re.MULTILINE)


def test_browser_skill_has_no_legacy_cloud_runtime() -> None:
    text = SKILL.read_text(encoding="utf-8")
    legacy_terms = (
        "XIAOHONGSHU_COOKIES",
        "Cookie Connection",
        "allowed_tools: [Bash]",
        "python3",
        "playwright",
        "chromium",
        "CDP",
        "xiaohongshu.py",
    )

    assert not any(term.casefold() in text.casefold() for term in legacy_terms)
    assert {path.name for path in SKILL_DIR.iterdir()} == {"SKILL.md", "tests"}


def test_browser_skill_documents_local_write_safety() -> None:
    text = SKILL.read_text(encoding="utf-8").casefold()

    assert "local account attestation" in text
    assert "local confirmation" in text
    assert "every write" in text
    assert "semantic reconciliation" in text
    assert "before retry" in text
    assert "dedicated test account" in text
    assert "canary" in text
    assert "stop on warning" in text
    assert "no local file upload capability" in text
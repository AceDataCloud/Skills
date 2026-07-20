from __future__ import annotations

import re
from pathlib import Path


SKILL_DIR = Path(__file__).parents[1]
SKILL = SKILL_DIR / "SKILL.md"
REFERENCES = {
    "login.md",
    "browse.md",
    "publish.md",
    "interactions.md",
    "reconciliation.md",
}
EXPECTED_ORIGINS = {
    "https://www.xiaohongshu.com",
    "https://creator.xiaohongshu.com",
}
EXPECTED_CAPABILITIES = {
    "tabs",
    "snapshot",
    "screenshot",
    "navigate",
    "click",
    "click_at",
    "form_input",
    "key",
    "scroll",
    "file_upload",
}
DEPLOYED_BROWSER_TOOLS = {
    "browser.snapshot",
    "browser.get_text",
    "browser.find",
    "browser.screenshot",
    "browser.element_info",
    "browser.navigate",
    "browser.click",
    "browser.click_at",
    "browser.hover",
    "browser.drag",
    "browser.form_input",
    "browser.type_text",
    "browser.select_option",
    "browser.set_checked",
    "browser.file_upload",
    "browser.key",
    "browser.scroll",
    "browser.scroll_to",
    "browser.tabs",
    "browser.wait_for",
    "browser.handle_dialog",
    "browser.download",
    "browser.console_messages",
    "browser.page_errors",
    "browser.network_requests",
    "browser.save_pdf",
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

    assert re.search(r"^name: xiaohongshu$", frontmatter, re.MULTILINE)
    assert re.search(
        r"^description: \|\n(?:  .+\n)+when_to_use: \|$",
        frontmatter,
        re.MULTILINE,
    )
    assert "  Operate Xiaohongshu / RED through the user's attached local browser:" in frontmatter
    assert re.search(r"^execution:\n  browser:\n", frontmatter, re.MULTILINE)
    assert re.search(r"^    provider: xiaohongshu/xiaohongshu$", frontmatter, re.MULTILINE)
    assert _nested_list(frontmatter, "origins") == EXPECTED_ORIGINS
    assert _nested_list(frontmatter, "capabilities") == EXPECTED_CAPABILITIES
    assert not re.search(r"^allowed_tools:.*\bBash\b", frontmatter, re.MULTILINE)


def test_browser_skill_has_no_legacy_cloud_runtime() -> None:
    text = SKILL.read_text(encoding="utf-8")
    legacy_terms = (
        "XIAOHONGSHU_COOKIES",
        "Cookie Connection",
        "allowed_tools: [Bash]",
        "playwright",
        "chromium",
        "CDP",
        "xiaohongshu.py",
    )

    assert not any(term.casefold() in text.casefold() for term in legacy_terms)
    assert {path.name for path in SKILL_DIR.iterdir()} == {"SKILL.md", "references", "scripts", "tests"}


def test_browser_skill_progressively_loads_domain_workflows() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert {path.name for path in (SKILL_DIR / "references").iterdir()} == REFERENCES
    for reference in REFERENCES:
        assert f"./references/{reference}" in text
    assert "scripts/xhs_contract.py" in text
    assert "Xiaohongshu-specific page semantics" in text
    assert "generic `browser.*` tools" in text


def test_browser_skill_matches_complete_local_runtime() -> None:
    documents = [SKILL, *(SKILL_DIR / "references").glob("*.md")]
    text = "\n".join(path.read_text(encoding="utf-8") for path in documents).casefold()
    mentioned_tools = set(re.findall(r"`(browser\.[a-z_]+)`", text))

    assert "attach current tab" in text
    assert "pair new" in text
    assert mentioned_tools <= DEPLOYED_BROWSER_TOOLS
    assert "browser.tabs_context" not in text
    assert "browser.attach_tab" not in text
    assert "cryptographic account attestation" in text
    assert "browser.file_upload" in mentioned_tools
    assert "browser.clear_cookies" not in text
    assert "never extract, clear, or return cookie values" in text
    assert "ask the user to open `https://creator.xiaohongshu.com`" in text
    assert "opaque resource ids" in text
    assert "trusted_input" not in _nested_list(_frontmatter(SKILL.read_text(encoding="utf-8")), "capabilities")
    assert "browser.read_page" not in text
    assert "browser.wait" not in text
    assert "local approval" not in text
    assert "publish image, video, or long-article notes" in text
    assert "long_article" in text
    assert "schedule" in text
    assert "originality" in text
    assert "visibility" in text
    assert "products" in text
    assert "search and filters" in text
    assert "/explore/<alphanumeric-note-id>" in text
    assert "/user/profile/<alphanumeric-user-id>" in text
    assert "empty-name links" in text
    assert "exactly one named same-origin" in text
    assert "unavailable" in text and "ambiguous" in text
    assert "unlabeled visible engagement value" in text
    assert "do not use this heuristic on creator pages" in text
    assert "detail and comments" in text
    assert "profile" in text
    assert "like and favorite" in text
    assert "comment" in text and "reply" in text
    assert "content planning" in text
    assert "reconciliation after uncertain browser writes" in text
    assert "stop on warning" in text
    assert "explicit confirmation" in text
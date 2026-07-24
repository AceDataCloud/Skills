from __future__ import annotations

import json
import re
from pathlib import Path


SKILL_DIR = Path(__file__).parents[1]
SKILL = SKILL_DIR / "SKILL.md"
MANIFEST = SKILL_DIR / "contracts" / "browser-manifest.compact.json"
MANIFEST_DATA = json.loads(MANIFEST.read_text(encoding="utf-8"))
REFERENCES = {
    "login.md",
    "browse.md",
    "publish.md",
    "interactions.md",
    "reconciliation.md",
    "mcp-parity.md",
}
EXPECTED_ORIGINS = {
    "https://www.xiaohongshu.com",
    "https://creator.xiaohongshu.com",
}
EXPECTED_FACADES = {
    "browser.snapshot",
    "browser.get_text",
    "browser.find",
    "browser.element_info",
    "browser.screenshot",
    "browser.click",
    "browser.hover",
    "browser.fill",
    "browser.type",
    "browser.select",
    "browser.check",
    "browser.press",
    "browser.scroll",
    "browser.scroll_to",
    "browser.navigate",
    "browser.tabs",
    "browser.wait",
    "browser.dialog",
    "browser.upload",
    "browser.batch",
}
EXPECTED_CAPABILITIES = {
    "tabs.read",
    "tabs.manage",
    "page.observe",
    "page.screenshot",
    "page.navigate",
    "input.pointer",
    "input.keyboard",
    "input.form",
    "file.upload",
}
DEPLOYED_BROWSER_TOOLS = set(MANIFEST_DATA["facades"])


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


def _top_level_list(frontmatter: str, key: str) -> set[str]:
    match = re.search(
        rf"^{re.escape(key)}:\n((?:  - .+\n)+)",
        frontmatter,
        re.MULTILINE,
    )
    assert match, f"missing {key}"
    return {
        line.removeprefix("  - ").strip()
        for line in match.group(1).splitlines()
    }


def _operation_block(frontmatter: str, operation: str) -> str:
    match = re.search(
        rf"^      {re.escape(operation)}:\n(.*?)(?=^      [a-z][a-z_]+:|^license:)",
        frontmatter,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing execution.browser.operations.{operation}"
    return match.group(1)


def _operation_names(frontmatter: str) -> set[str]:
    match = re.search(r"^    operations:\n(.*?)(?=^license:)", frontmatter, re.MULTILINE | re.DOTALL)
    assert match, "missing execution.browser.operations"
    return set(re.findall(r"^      ([a-z][a-z_]+):$", match.group(1), re.MULTILINE))


def _operation_tools(block: str) -> set[str]:
    match = re.search(r"^        allowed_tools:\n((?:          - .+\n)+)", block, re.MULTILINE)
    assert match, "missing operation allowed_tools"
    return {
        line.removeprefix("          - ").strip()
        for line in match.group(1).splitlines()
    }


def _operation_commands(block: str) -> set[str]:
    match = re.search(r"^        allowed_commands:\n((?:          - .+\n)+)", block, re.MULTILINE)
    assert match, "missing operation allowed_commands"
    return {
        line.removeprefix("          - ").strip()
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
    assert "  Operate Xiaohongshu / RED through the user's paired browser device:" in frontmatter
    assert re.search(r"^skill_revision: 4\.2\.0$", frontmatter, re.MULTILINE)
    assert re.search(r"^execution:\n  browser:\n", frontmatter, re.MULTILINE)
    assert re.search(r"^    skill_revision: 4\.2\.0$", frontmatter, re.MULTILINE)
    assert re.search(r"^    provider: xiaohongshu/xiaohongshu$", frontmatter, re.MULTILINE)
    assert _nested_list(frontmatter, "origins") == EXPECTED_ORIGINS
    assert _nested_list(frontmatter, "capabilities") == EXPECTED_CAPABILITIES
    assert _top_level_list(frontmatter, "allowed_tools") == EXPECTED_FACADES
    assert "  browser_contract: contracts/browser-manifest.compact.json" in frontmatter
    for legacy_key in ("protocol_version", "manifest_version", "manifest_digest", "wire_operation"):
        assert not re.search(rf"^    {legacy_key}:", frontmatter, re.MULTILINE)
    assert not re.search(r"^allowed_tools:.*\bBash\b", frontmatter, re.MULTILINE)


def test_compact_manifest_matches_final_generated_profile() -> None:
    manifest = MANIFEST_DATA
    facade_policies = manifest["facades"]
    all_policies = set(manifest["policy_capabilities"])
    mapped_policies = {
        facade["policy_capability"] for facade in facade_policies.values()
    }

    generated = manifest["_generated"]
    assert generated["generator"] == "aichat2/worker/scripts/generate-browser-manifest.ts"
    assert re.fullmatch(r"[0-9a-f]{40}", generated["source_commit"])
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", generated["wire_contract_digest"])
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", generated["facade_catalog_digest"])
    assert generated["facade_catalog_digest"] == manifest["facade_catalog_digest"]
    assert set(facade_policies) == DEPLOYED_BROWSER_TOOLS
    assert len(facade_policies) == 30
    assert all_policies
    assert mapped_policies <= all_policies


def test_operation_descriptors_define_exact_tool_union() -> None:
    skill_text = SKILL.read_text(encoding="utf-8")
    frontmatter = _frontmatter(skill_text)
    operation_names = _operation_names(frontmatter)
    assert operation_names == {"read_content", "publish_note", "comment_or_reply", "toggle_reaction"}
    operations = {
        name: _operation_block(frontmatter, name)
        for name in operation_names
    }
    operation_tools = {name: _operation_tools(block) for name, block in operations.items()}
    operation_commands = {name: _operation_commands(block) for name, block in operations.items()}

    assert set().union(*operation_tools.values()) == _top_level_list(frontmatter, "allowed_tools")
    assert set().union(*operation_tools.values()) == EXPECTED_FACADES
    assert EXPECTED_FACADES <= DEPLOYED_BROWSER_TOOLS
    for tools in operation_tools.values():
        assert tools <= DEPLOYED_BROWSER_TOOLS

    for name, tools in operation_tools.items():
        expected_commands = {
            f"{MANIFEST_DATA['facades'][tool]['family']}/{MANIFEST_DATA['facades'][tool]['kind']}"
            for tool in tools
        }
        assert operation_commands[name] == expected_commands

    publish = operations["publish_note"]
    assert re.search(r"^        minimum_action_class: protected\.publish$", publish, re.MULTILINE)
    for field in ("title", "content_hash", "media_hashes", "visibility"):
        assert re.search(rf"^            - {field}$", publish, re.MULTILINE)
    assert re.search(
        r'^        semantic_key_template: "\{provider\}:\{operation_id\}:\{preview_hash\}:\{normalized_input_hash\}"$',
        publish,
        re.MULTILINE,
    )
    assert re.search(r"^        minimum_action_class: protected\.interaction$", operations["comment_or_reply"], re.MULTILINE)
    assert re.search(r"^        minimum_action_class: reversible\.write$", operations["toggle_reaction"], re.MULTILINE)
    assert re.search(r"^        minimum_action_class: read$", operations["read_content"], re.MULTILINE)
    for block in operations.values():
        template = re.search(r'^        semantic_key_template: "([^"]+)"$', block, re.MULTILINE)
        assert template
        fields = set(re.findall(r"\{([^}]+)\}", template.group(1)))
        assert {"provider", "operation_id"} <= fields
        assert fields <= {"provider", "operation_id", "preview_hash", "normalized_input_hash"}


def test_generic_manifest_contains_no_site_specific_logic() -> None:
    text = MANIFEST.read_text(encoding="utf-8").casefold()

    assert "xiaohongshu" not in text
    assert "creator.xiaohongshu.com" not in text
    assert "selector" not in text
    assert "xhs-" not in text


def test_execution_metadata_has_no_tool_shaped_auth_capabilities() -> None:
    frontmatter = _frontmatter(SKILL.read_text(encoding="utf-8"))
    execution = frontmatter.split("license:", maxsplit=1)[0]
    capabilities = _nested_list(frontmatter, "capabilities")

    assert capabilities == EXPECTED_CAPABILITIES
    assert capabilities <= set(json.loads(MANIFEST.read_text(encoding="utf-8"))["policy_capabilities"])
    assert capabilities <= set(MANIFEST_DATA["policy_capabilities"])
    assert not capabilities & {facade.removeprefix("browser.") for facade in DEPLOYED_BROWSER_TOOLS}
    assert not re.search(r"^      - (?:browser\.)?(?:snapshot|click|form_input|file_upload|tabs)$", execution, re.MULTILINE)


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
    assert {path.name for path in SKILL_DIR.iterdir()} == {"SKILL.md", "contracts", "references", "scripts", "tests"}


def test_browser_skill_progressively_loads_domain_workflows() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert {path.name for path in (SKILL_DIR / "references").iterdir()} == REFERENCES
    for reference in REFERENCES:
        assert f"./references/{reference}" in text
    assert "scripts/xhs_contract.py" in text
    assert "Xiaohongshu-specific page semantics" in text
    assert "generic `browser.*` facades" in text


def test_browser_skill_matches_complete_local_runtime() -> None:
    documents = [SKILL, *(SKILL_DIR / "references").glob("*.md")]
    text = "\n".join(path.read_text(encoding="utf-8") for path in documents).casefold()
    mentioned_tools = set(re.findall(r"`(browser\.[a-z_]+)`", text))

    assert mentioned_tools <= EXPECTED_FACADES
    assert "browsersession" in text
    assert "online-compatible paired browser device" in text
    for manual_instruction in (
        "attach current tab",
        "attached tab",
        "attached page",
        "separately open and attach",
        "focus the relevant tab",
        "navigate or attach",
        "attach that tab",
    ):
        assert manual_instruction not in text
    assert "browser.tabs_context" not in text
    assert "browser.attach_tab" not in text
    assert "cryptographic account attestation" in text
    assert "browser.upload" in mentioned_tools
    assert "browser.clear_cookies" not in text
    assert "never extract, clear, or return cookie values" in text
    assert "aichat2 create or reuse the browsersession" in text
    assert "opaque resource ids" in text
    assert "trusted_input" not in _nested_list(_frontmatter(SKILL.read_text(encoding="utf-8")), "capabilities")
    for alias in (
        "browser.observe",
        "browser.act",
        "browser.transfer",
        "browser.debug",
        "browser.form_input",
        "browser.type_text",
        "browser.select_option",
        "browser.set_checked",
        "browser.key",
        "browser.wait_for",
        "browser.handle_dialog",
        "browser.file_upload",
    ):
        assert alias not in text
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


def test_upstream_mcp_feature_parity_and_skill_ownership() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [SKILL, *(SKILL_DIR / "references").glob("*.md")]
    ).casefold()

    for feature in (
        "check_login_status",
        "get_login_qrcode",
        "publish_content",
        "publish_with_video",
        "list_feeds",
        "search_feeds",
        "get_feed_detail",
        "user_profile",
        "get_me",
        "post_comment_to_feed",
        "reply_comment_in_feed",
        "like_feed",
        "favorite_feed",
    ):
        assert feature in text

    for invariant in (
        "上传图文",
        "上传视频",
        "写长文",
        "新的创作",
        "一键排版",
        "xhs-publish-btn",
        "submit-disabled=true",
        "img-preview-area",
        "10 minutes",
        "15 seconds",
        "4 seconds",
        "never exceed two total clicks",
    ):
        assert invariant.casefold() in text

    assert "a7d1f2f7f45e0b1c27de67c8f8a19131ba321725" in text
    assert "no arbitrary cdp/evaluate" in text
    assert "no cookie deletion/export" in text
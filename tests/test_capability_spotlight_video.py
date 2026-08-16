import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "capability-spotlight-video" / "SKILL.md"
BRAND = ROOT / "skills" / "capability-spotlight-video" / "references" / "brand-kit.md"
TOPICS = ROOT / "skills" / "capability-spotlight-video" / "references" / "topic-registry.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def topic_blocks() -> list[str]:
    return re.findall(r"(?ms)^## TOPIC .+?(?=^## TOPIC |\Z)", text(TOPICS))


def test_skill_declares_runtime_and_series_evidence_contract() -> None:
    body = text(SKILL)
    assert "name: capability-spotlight-video" in body
    assert "connections: [acedatacloud/acedatacloud]" in body
    assert "{{run_count}}" in body
    assert "{{date_iso}}" in body
    assert "maestro_list_tasks(limit=30)" in body
    for key in (
        "FAMILY_ID",
        "TOPIC_ID",
        "DEMO_ID",
        "STYLE_ID",
        "LAYOUT_ID",
        "PALETTE_ID",
        "VOICE_ID",
        "ASSET_HASHES",
        "EXECUTED_APIS",
        "EVIDENCE_URLS",
    ):
        assert key in body
    assert "ADC-SPOTLIGHT:v1" in body
    assert "unconstrained randomness" in body
    assert "one primary capability" in body
    assert "Async hero evidence" in body
    assert "first capability-specific tool call MUST be that provider's" in body
    assert "list_tasks" in body or "batch-list" in body
    assert "24-hour" in body
    assert "Do not call generate/create before this lookup" in body
    assert "reuse a matching completed task" in body
    assert "do not call generate/create" in body
    assert "resume a matching pending task by ID" in body
    assert "Do not poll once and give up" in body
    assert "eight 15-second polls" in body
    assert "ADC-SPOTLIGHT-SOURCE:v1" in body


def test_brand_kit_uses_canonical_transparent_asset_and_authored_name() -> None:
    body = text(BRAND)
    assert "https://cdn.acedata.cloud/logo.png" in body
    assert "A symbol only" in body
    assert "`ACE DATA CLOUD`" in body
    assert "optical vertical centers" in body
    assert "baseline" in body
    assert "decoded frame 0" in body
    assert "36066a80-7a14-4fd9-a7bc-7722f3be8285" in body
    assert "Never use" in body
    assert "legacy `AceData` or `ceData`" in body
    assert "crop box `(50, 47, 251, 231)`" in body
    assert "legacy wordmark begins at `x=264`" in body
    assert "no non-transparent pixel originating at source `x>=264`" in body
    assert "A width-ratio crop is forbidden" in body
    assert "Final CTA must include one readable action phrase" in body
    assert "abstract symbol, endpoint, or decorative target alone is not a CTA" in body


def test_registry_covers_broad_platform_families_and_representative_topics() -> None:
    body = text(TOPICS)
    blocks = topic_blocks()
    assert len(blocks) >= 9
    for topic in (
        "gpt-image-2-craft",
        "minimax-h3-multimodal",
        "seedance-2-reference-control",
        "acechat-agent-workspace",
        "captcha-solving-lifecycle",
        "maestro-agent-production",
    ):
        assert f"## TOPIC {topic}" in body
    families = {re.search(r"(?m)^- FAMILY: (.+)$", block).group(1) for block in blocks}
    assert {"ai-image", "ai-video", "ai-chat-agent", "captcha", "ai-video-production", "platform"} <= families


def test_every_topic_has_multiple_demos_and_live_contract_fields() -> None:
    required = ("- FAMILY:", "- SERVICE:", "- APIS:", "- DOC_QUERY:", "- MCP:", "- PROMISE:", "- DEMOS:", "- EVIDENCE:", "- CREATIVE:", "- LIMITS:")
    for block in topic_blocks():
        for marker in required:
            assert marker in block, (block.splitlines()[0], marker)
        demo_ids = re.findall(r"(?m)^  - `([^`]+)`:", block)
        assert len(demo_ids) >= 2, block.splitlines()[0]
        assert len(demo_ids) == len(set(demo_ids))


def test_registry_demonstrates_unique_capability_strengths() -> None:
    body = text(TOPICS)
    assert "typography" in body and "edit/composite" in body
    assert "both the source URL and the accepted edits output URL are mandatory" in body
    assert "forbidden when only `/openai/images/generations` executed" in body
    assert "requires `/openai/images/edits` in `EXECUTED_APIS`" in body
    assert "Inspect both accepted images at full resolution before scripting" in body
    assert "`present before`, `present after`, and `visibly changed`" in body
    assert "from decoded pixels—not prompt prose" in body
    assert "bind each row to the exact source/output URL" in body
    assert "still visible in the accepted edit cannot be called removed" in body
    assert "absent from the labeled frame cannot be called present" in body
    assert "script, labels, and narration must all agree with the inventory" in body
    assert "first/last frame" in body and "reference audio" in body
    assert "provider-downloadable public HTTPS URL" in body
    assert "never receive `data:`, `blob:`, or local-file reference URLs" in body
    assert "2.5-only options require a Seedance 2.5 model" in body
    assert "real tool trace" in body and "Memory" in body and "Scheduled Tasks" in body
    assert "create→lease/solve→task retrieve→result" in body
    assert "brief→asset manifest→composition→visual review→final MP4" in body
    assert "video is mandatory evidence" in body


def test_skill_rotates_voice_style_layout_and_keeps_review_bounded() -> None:
    body = text(SKILL)
    for voice in ("energetic-male", "bright-female", "clean-female", "calm-male", "storyteller-male", "warm-female", "anchor-female", "deep-male"):
        assert voice in body
    assert "last 3 `PALETTE_ID` and `VOICE_ID`" in body
    assert "14 evidence frames" in body
    assert "one concentrated same-project refinement" in body
    assert "Never restart production routing" in body
    assert "output/result.json" in body
    assert "30-second Standard draft" in body
    assert "may reduce only duration and SKU" in body
    assert "MUST still use a real accepted capability output" in body
    assert "Never disable inner review" in body
    assert "actual accepted output URL/MP4" in body
    assert 'extract decoded frame 0 explicitly at `-ss 0`' in body
    assert "no black/near-black gap" in body
    assert "summary itself" in body
    assert "putting IDs only in tags does not satisfy" in body
    assert "before any further inspection, waiting, polling, or narration" in body
    assert "{'code': 'task_already_exists', 'task_id': '<same UUID>'}" in body
    assert "do not generate another UUID" in body
    assert "do not call `maestro_create_video` again" in body
    assert "next and only allowed tool call is `publish_artifact`" in body
    assert "The outer Producer must then end" in body
    assert "sandbox-root-qualified project paths" in body
    assert "Verify the manifest/contact sheet exists" in body


def test_public_copy_has_no_supplier_or_secret_leaks() -> None:
    combined = "\n".join(map(text, (SKILL, BRAND, TOPICS))).lower()
    for forbidden in (
        "openai-hk",
        "bananarouter",
        "grsai",
        "cqtai",
        "acedatacloud_openai",
        "gpt-image-2-vip",
        "actual_api_key",
    ):
        assert forbidden not in combined

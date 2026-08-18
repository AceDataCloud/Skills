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
        "FILM_ARCHETYPE",
        "VISUAL_WORLD",
        "SHOT_GRAMMAR",
        "RHYTHM_PATTERN",
        "PALETTE_ID",
        "VOICE_ID",
        "SOUND_WORLD",
        "ASSET_HASHES",
        "EXECUTED_APIS",
        "EVIDENCE_URLS",
    ):
        assert key in body
    assert "ADC-SPOTLIGHT:v1" in body
    assert "unconstrained randomness" in body
    assert "one **premium, product-specific sales film**" in body
    assert "## 4. Reuse tasks before spending" in body
    assert "first capability-specific call MUST be the provider's" in body
    assert "list_tasks" in body or "batch-list" in body
    assert "24-hour" in body
    assert "Do not generate before this lookup" in body
    assert "reuse a matching completed request" in body
    assert "accepted public URL" in body
    assert "resume a matching pending task by ID" in body
    assert "Poll according to the returned interval until terminal" in body
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
    assert "`seedance-image-reference-control`" in body
    assert "public fictional product/interface image as `reference_image`" in body
    assert "start/middle/end decoded output frames" in body
    assert "do not claim person/character identity or motion-reference input" in body
    assert "never receive `data:`, `blob:`, or local-file reference URLs" in body
    assert "2.5-only options require a Seedance 2.5 model" in body
    assert "real tool trace" in body and "Memory" in body and "Scheduled Tasks" in body
    assert "create→lease/solve→task retrieve→result" in body
    assert "brief→asset manifest→composition→visual review→final MP4" in body
    assert "video is mandatory evidence" in body


def test_skill_rotates_creative_genome_and_keeps_review_bounded() -> None:
    body = text(SKILL)
    for archetype in (
        "brand anthem",
        "product reveal",
        "workflow transformation",
        "launch trailer",
        "kinetic manifesto",
        "cinematic UI demo",
        "multi-modal montage",
        "visual poem",
    ):
        assert archetype in body
    assert "recent 3 transition-system, voice-family, sound-world, or palette-family" in body
    assert "one concentrated pass" in body
    assert 'actual `Skill` call with `skill="visual-review"`' in body
    assert "second actual confirmation call" in body
    assert "output/result.json" not in body  # worker-owned detail is not part of the outer planner
    assert "before waiting or polling" in body
    assert "task_already_exists" in body
    assert "do not generate another UUID or resubmit" in body
    assert "outer task ends after `recorded=true`" in body


def test_skill_requires_sales_blueprint_before_maestro() -> None:
    body = text(SKILL)
    assert "ACE-DATA-CLOUD-SALES-BLUEPRINT:v3" in body
    for field in (
        "CAMPAIGN_MODE",
        "PRODUCTS",
        "FINAL_OUTCOME",
        "AUDIENCE",
        "PAIN",
        "PROMISE",
        "HERO_CASE",
        "UNIQUE_ADVANTAGE",
        "WORKFLOW",
        "PRICE",
        "OFFER",
        "CTA",
        "MATERIAL_MIX",
        "QUALITY_GATES",
    ):
        assert field in body
    assert "Before Maestro, write" in body
    assert "fixed six-scene or fixed timestamp storyboard" in body
    assert "who buys, what changes, why this product is distinctive" in body
    assert "Integration/price appears only when it advances the sale" in body
    assert "never place labels such as `accepted output`, `decoded proof`" in body


def test_every_topic_has_a_service_specific_sales_playbook() -> None:
    required = (
        "- AUDIENCE:",
        "- PAIN:",
        "- BASIC_INTRO:",
        "- HERO_CASES:",
        "- UNIQUE_ADVANTAGES:",
        "- PRICE_SCENARIOS:",
        "- HOOKS:",
        "- CTA:",
        "- TONE:",
        "- FORBIDDEN_GENERIC_CASES:",
    )
    for block in topic_blocks():
        for marker in required:
            assert marker in block, (block.splitlines()[0], marker)
        assert len(re.findall(r"(?m)^  - `[^`]+`:", block)) >= 2


def test_sales_playbooks_name_distinct_product_drama() -> None:
    body = text(TOPICS)
    for phrase in (
        "fix every headline",
        "premium products",
        "make it move—without losing it",
        "campaign consistency wall",
        "A chat box answers",
        "create→solve→result",
        "script, assets, voice, review, and final film",
        "one token",
    ):
        assert phrase in body
    assert "ordinary architecture or still-life beauty shot" in body
    assert "fake chat bubbles" in body
    assert "pure catalog-card walkthrough" in body


def test_skill_is_a_general_runtime_campaign_planner() -> None:
    body = text(SKILL)
    assert "acedatacloud_list_services(private=false, limit=300)" in body
    assert "Single Capability" in body
    assert "Workflow Campaign" in body
    assert "Platform Story" in body
    assert "at least one eligible candidate in every mode" in body
    assert "ACE-DATA-CLOUD-SALES-BLUEPRINT:v3" in body
    assert "runtime capability graph" in body
    assert "Node contract" in body
    assert "Edge contract" in body
    assert "2–4 services" in body
    assert "proved by OpenAPI or an executed request" in body
    assert "examples, not an allowlist" in body
    assert "recent 6 `FILM_ARCHETYPE`" in body
    assert "recent 4 campaign-mode, climax-device, or rhythm-pattern" in body
    assert "selected 2–4 MCP servers" in body
    assert "real hero evidence" in body
    assert "It MUST NOT contain `ADC-SPOTLIGHT:v1`" in body
    assert "artifact summary—not the Maestro prompt" in body


def test_registry_is_an_anchor_library_not_a_closed_catalog() -> None:
    body = text(TOPICS)
    assert "Anchor library — examples, not an allowlist" in body
    assert "General derivation rubric" in body
    for field in ("buyer/job-to-be-done", "current pain", "observable mechanism", "hero recipe", "price scenario"):
        assert field in body
    assert "could be copied unchanged onto another AI service" in body
    assert "Campaign launch" in body
    assert "Product-to-video" in body
    assert "Agent automation" in body
    assert "Content engine" in body
    assert "Audio-led campaign" in body
    assert "Platform integration" in body


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


def test_v4_routes_production_to_general_video_without_spotlight_renderer_marker() -> None:
    body = text(SKILL)
    assert 'metadata:\n  author: acedatacloud\n  version: "4.0"' in body
    assert 'ACE-DATA-CLOUD-BRAND-FILM:v1' in body
    assert 'route to `/general-video`' in body
    assert '`scenario=auto`, `quality=pro`' in body
    assert 'never use `spotlight_prepare.py`, `spotlight_renderer.py`' in body
    assert 'MUST NOT contain `ADC-SPOTLIGHT:v1`' in body
    assert 'artifact summary—not the Maestro prompt—begins' in body
    assert '`ADC-SPOTLIGHT:v1 | BLUEPRINT=v3' in body


def test_v4_uses_freeform_blueprint_and_structural_creative_genome() -> None:
    body = text(SKILL)
    assert 'ACE-DATA-CLOUD-SALES-BLUEPRINT:v3' in body
    for field in (
        'FILM_ARCHETYPE',
        'VISUAL_WORLD',
        'SHOT_GRAMMAR',
        'RHYTHM_PATTERN',
        'OPENING_DEVICE',
        'CLIMAX_DEVICE',
        'TRANSITION_SYSTEM',
        'BRAND_BEHAVIOR',
        'SOUND_WORLD',
        'MATERIAL_MIX',
    ):
        assert field in body
    assert 'Do **not** write a fixed six-scene or fixed timestamp storyboard' in body
    for obsolete in ('0–3 seconds', '3–7 seconds', '7–17 seconds', '17–22 seconds', '22–26 seconds', '26–30 seconds'):
        assert obsolete not in body
    assert 'creative distance' in body
    assert 'palette or labels' in body
    assert 'generic cyan dashboard' in body


def test_v4_requires_rich_materials_by_campaign_mode() -> None:
    body = text(SKILL)
    assert 'Require at least four useful visual roles' in body
    assert 'Require 5–8 roles covering 2–4 real stages' in body
    assert 'at least three distinct modalities or product surfaces and three real results' in body
    assert 'catalog-only slideshow is forbidden' in body
    assert 'One unchanged still may not be stretched through the film' in body
    assert 'audio-reactive visual world' in body
    assert 'never fake chat bubbles' in body


def test_v4_general_video_professional_director_contract() -> None:
    body = text(SKILL)
    for phrase in (
        'house-style.md',
        'video-composition.md',
        'one-sentence concept angle',
        'embedded font pairing',
        'foreground-density plan',
        'prompt expansion',
        'modular sub-compositions',
        'Fish narration timing',
        'actual `Skill` call with `skill="visual-review"`',
        'second actual confirmation call',
    ):
        assert phrase in body
    assert 'Formal production uses **Pro**, never Standard' in body
    assert 'Reviewer receives the Blueprint, Creative Genome' in body


def test_anchor_topics_supply_multiple_creative_opportunities() -> None:
    for block in topic_blocks():
        for marker in (
            '- VISUAL_WORLDS:',
            '- FILM_ARCHETYPES:',
            '- MATERIAL_OPPORTUNITIES:',
            '- FORBIDDEN_REPETITION:',
        ):
            assert marker in block, (block.splitlines()[0], marker)
    body = text(TOPICS)
    assert 'Creative opportunity fields' in body
    assert 'palette or voice swap alone never counts' in body


def test_brand_identity_is_stable_but_behavior_must_rotate() -> None:
    body = text(BRAND)
    assert 'Identity stays fixed; brand behavior rotates' in body
    assert 'energy rail, mask edge, registration grid, spatial portal' in body
    assert 'Do not repeat the same brand entrance' in body
    assert 'Brand consistency is identity and craft—not template sameness' in body

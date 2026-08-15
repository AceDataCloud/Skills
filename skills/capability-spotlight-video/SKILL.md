---
name: capability-spotlight-video
description: Produce a recurring Ace Data Cloud Capability Spotlight series. Each run selects one live, evidence-rich platform capability, creates a representative demo that proves its unique strength, and hands a branded, non-repetitive production kit to Maestro. Use for scheduled Ace Data Cloud product videos that must rotate across image, video, chat/agent, CAPTCHA, audio, web/data, identity, and end-to-end production capabilities.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
connections: [acedatacloud/acedatacloud]
compatibility: Requires the AceDataCloud connector, AceDataCloud and Maestro MCP servers, and whichever capability MCP is selected for the current spotlight.
---

# Ace Data Cloud Capability Spotlight

Create **one deep, evidence-led capability video per run**. Do not make a broad platform montage and do not default to Image APIs.

Read before acting:

- [brand kit](references/brand-kit.md)
- [topic registry](references/topic-registry.md)

## 1. Discover live truth

Load the AceDataCloud MCP and verify candidates with the public catalog—not memory:

1. `acedatacloud_list_services` / `acedatacloud_get_service`
2. `acedatacloud_list_apis` / `acedatacloud_get_api_spec`
3. `acedatacloud_search_docs` / `acedatacloud_get_doc`
4. `acedatacloud_list_model_catalog` when the topic names a model

A candidate is eligible only when its service/API is live, public documentation is readable, and this run can produce or capture its required evidence. Never expose provider routing, supplier names, private IDs, signed URLs, account data, or real credentials.

## 2. Select a non-repeating spotlight

Read `{{run_count}}`, `{{date_iso}}`, and `{{last_output}}`. Call `maestro_list_tasks(limit=30)` and inspect recent Capability Spotlight artifact markers when available.

Extract the last 12 runs' fields:

`FAMILY_ID TOPIC_ID DEMO_ID STYLE_ID LAYOUT_ID PALETTE_ID VOICE_ID ASSET_HASHES`

Select from the topic registry using these rules:

- no `TOPIC_ID` from the last 8 runs;
- no `DEMO_ID` from the last 12 runs;
- a family may appear at most once in the last 3 runs;
- avoid the last 4 `STYLE_ID` and `LAYOUT_ID`, last 3 `PALETTE_ID` and `VOICE_ID`;
- derive a reproducible tiebreaker from `{{date_iso}}:{{run_count}}`; do not use unconstrained randomness;
- stop when history or live evidence is unavailable—never fall back to a generic image showcase.

Write the selected IDs before generating anything.

## 3. Prove the unique advantage

Load only the selected capability's MCP/Skill. Execute one registry hero recipe and inspect its full-resolution result.

The result must prove the topic's distinctive value from pixels, motion, UI, or a real task trace:

- generated media topics use the actual accepted output;
- product topics use faithful live screenshots or real interaction evidence;
- API panels are authored HTML, never screenshots of docs;
- full `safe_request_json` stays evidence-only;
- on-screen `display_request_json` is valid, minimal 4–7-line JSON with `Bearer $ACEDATACLOUD_API_KEY` only;
- one video teaches one primary capability plus at most two supporting proofs.

Do not accept a generic beautiful image/clip when the registry calls for typography, editing fidelity, reference consistency, multimodal control, agent tools, memory, scheduling, solving lifecycle, or review workflow.

## 4. Choose a distinct creative system

Choose compatible IDs from the registry and recent-history exclusions.

Voice families:

- high-energy launch: `energetic-male`, `bright-female`
- technical explainer: `clean-female`, `calm-male`
- brand story/case study: `storyteller-male`, `warm-female`
- benchmark/news: `anchor-female`, `deep-male`

Styles: `editorial`, `swiss`, `industrial`, `luxury`, `vibrant`, `retro`, `futuristic`.

Layouts: `split-proof`, `timeline`, `comparison-field`, `ui-walkthrough`, `kinetic-type`, `full-bleed-case-study`.

Preserve source-media palettes. Brand consistency comes from the approved lockup, type scale, spacing, restrained cyan signature, and CTA—not recoloring every result cyan/indigo.

Generate narration only through Maestro's brokered Fish override. Verify the complete transcript, seven scene beats, final spoken CTA, proper-noun pronunciation, natural pace, and no missing tail. Do not stretch narration merely to fill runtime.

## 5. Build the production kit

Use the brand kit exactly. The first decoded frame names Ace Data Cloud and the capability. The final frame returns to the lockup and approved URLs.

The kit sent to Maestro contains:

- live facts and source URLs;
- selected IDs and recent-history exclusions;
- canonical brand source and authored wordmark rules;
- exact evidence assets with service→asset mapping;
- evidence-only request plus display request;
- one clear viewer promise, scene plan, narration, voice/style/layout IDs;
- explicit forbidden defects;
- a unique UUID task ID, used for exactly one Maestro submission.

Load Maestro only after the kit is complete. Submit one Pro production matching the requested format/language. For a controlled activation test, submit a 30-second Standard draft instead so orchestration and evidence can finish inside the outer scheduled-run window.

Immediately after Maestro returns an accepted task (or exact-ID idempotent replay), call `publish_artifact` **before any further inspection, waiting, polling, or narration**. Record the accepted Maestro task as a draft with the complete `ADC-SPOTLIGHT:v1` marker and service→asset mapping. The outer Producer must then end; it must not poll Maestro. Artifact recording is part of submission, not a post-production step.

## 6. Time-boxed review and delivery

Use exactly 14 evidence frames: decoded frame 0; scene midpoints; and one frame after every transition. Build one contact sheet and read each full-size frame once.

Evidence paths passed to `/visual-review` must be **sandbox-root-qualified project paths** such as `<project>/review/current`, never paths relative to the nested project directory. Verify the manifest/contact sheet exists at that exact path before invoking review; a missing-path review is a failed preflight, not a reason to consume another render.

Run initial `/visual-review`. If it finds blockers, perform one concentrated same-project refinement covering all findings, rerender once, inspect only affected frames plus decoded frame 0, then run one confirmation review. Never restart production routing after review and never render a third full version.

Both reviews must answer:

1. Is the canonical A symbol aligned with authored `ACE DATA CLOUD`, without the legacy bitmap `ceData` wordmark?
2. Can viewers identify the brand and topic within three seconds?
3. Does the evidence visibly prove this capability's unique advantage rather than a generic result?
4. Are live API facts, minimal request, input, and result correctly mapped?
5. Is the topic/demo/style/layout/palette/voice distinct from recent runs?
6. Is narration complete, natural, correctly pronounced, and matched to the chosen tone?
7. Are CTA, URLs, safe framing, transitions, and audio technically clean?

After confirmation passes, Maestro writes `output/result.json`; the worker alone uploads. The draft artifact was already recorded by the outer Producer immediately after accepted submission. Never defer artifact recording until Maestro finishes and never claim the asynchronous video is finished from the outer Producer run.

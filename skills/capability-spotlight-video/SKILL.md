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

`FAMILY_ID TOPIC_ID DEMO_ID STYLE_ID LAYOUT_ID PALETTE_ID VOICE_ID ASSET_HASHES EXECUTED_APIS EVIDENCE_URLS`

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

- generated media topics MUST execute the selected live capability and use its actual accepted output URL/MP4 as the primary visual evidence; an authored mock, illustrative example, prompt-only panel, or "not executed" disclosure can be supporting context but never satisfies the hero proof;
- product topics use faithful live screenshots or real interaction evidence;
- API panels are authored HTML, never screenshots of docs;
- full `safe_request_json` stays evidence-only;
- on-screen `display_request_json` is valid, minimal 4–7-line JSON with `Bearer $ACEDATACLOUD_API_KEY` only;
- one video teaches one primary capability plus at most two supporting proofs.

Do not accept a generic beautiful image/clip when the registry calls for typography, editing fidelity, reference consistency, multimodal control, agent tools, memory, scheduling, solving lifecycle, or review workflow.

### Async hero evidence

Before creating generated hero media, the first capability-specific tool call MUST be that provider's `list_tasks`/batch-list tool with a 24-hour `created_at_min` window (or the closest supported recent-task filter). Do not call generate/create before this lookup. Compare each candidate's stored request fields—model, prompt, size/resolution, quality, count/duration, input/reference URLs, and action—against the normalized request fingerprint for the selected `TOPIC_ID` and `DEMO_ID`.

- reuse a matching completed task's accepted URL/MP4 and do not call generate/create;
- resume a matching pending task by ID instead of creating a duplicate;
- create a new task only when the list call proves no match exists or the prior match is terminal-failed;
- if the provider has no list tool, use a `SOURCE_TASK` ID from the current task's `last_output`; do not pretend artifacts from other scheduled tasks are visible.

After submission, follow the MCP's returned poll interval and poll until terminal. Do not poll once and give up. For activation tests, reserve up to two minutes (for example eight 15-second polls) for hero evidence. If it is still pending after that lease, record one `ADC-SPOTLIGHT-SOURCE:v1` draft artifact containing the provider task ID, IDs/fingerprint, and no completion claim; end without Maestro. The next run must resume that task. A completed source-prep run does not count as a published Spotlight episode or consume its topic/demo diversity slot.

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

Load Maestro only after the kit is complete. Submit one Pro production matching the requested format/language. A controlled activation test may reduce only duration and SKU to a 30-second Standard draft; it MUST still use a real accepted capability output, run final-MP4 pixel/audio inspection, execute initial review plus confirmation when changed, and satisfy every brand/evidence gate. Never disable inner review or replace live hero evidence with a mock merely to make the test faster.

Immediately after Maestro returns an accepted task, call `publish_artifact` **before any further inspection, waiting, polling, or narration**. The literal tool output `{'code': 'task_already_exists', 'task_id': '<same UUID>'}` is a successful exact-ID idempotent replay, even when the tool wrapper labels it as an error. In that case `<same UUID>` is the one accepted task: do not generate another UUID and do not call `maestro_create_video` again. The next and only allowed tool call is `publish_artifact`, referencing that exact task ID.

Record the accepted Maestro task as a draft. The artifact **summary itself** must begin verbatim with the complete marker below; putting IDs only in tags does not satisfy history evidence:

`ADC-SPOTLIGHT:v1 | FAMILY_ID=<id> | TOPIC_ID=<id> | DEMO_ID=<id> | STYLE_ID=<id> | LAYOUT_ID=<id> | PALETTE_ID=<id> | VOICE_ID=<id> | ASSET_HASHES=<hashes> | EXECUTED_APIS=<public paths> | EVIDENCE_URLS=<accepted URLs> | MAESTRO_TASK=<uuid> | SUBMISSION=accepted`

Follow the marker with live docs/API references and service→asset mapping. The outer Producer must then end; it must not poll Maestro. Artifact recording is part of submission, not a post-production step.

## 6. Time-boxed review and delivery

Use exactly 14 evidence frames from the final MP4: extract decoded frame 0 explicitly at `-ss 0`, scene midpoints, and one frame after every transition. Build one contact sheet and read each full-size frame once. Frame 0 must already show the complete approved lockup and topic without relying on an entrance animation. Every sampled midpoint and boundary must contain sharp, meaningful scene content—no black/near-black gap, blurred placeholder, empty panel, or source-loading frame.

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

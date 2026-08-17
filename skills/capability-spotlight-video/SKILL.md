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

1. `acedatacloud_list_services(private=false, limit=300)` / `acedatacloud_get_service` — enumerate the complete current public service catalog, not a hand-maintained shortlist;
2. `acedatacloud_list_apis` / `acedatacloud_get_api_spec`
3. `acedatacloud_search_docs` / `acedatacloud_get_doc`
4. `acedatacloud_list_model_catalog` when the topic names a model

A candidate is eligible only when its service/API is live, public documentation is readable, and this run can produce or capture its required evidence. Never expose provider routing, supplier names, private IDs, signed URLs, account data, or real credentials.

## 2. Select a non-repeating spotlight

Read `{{run_count}}`, `{{date_iso}}`, and `{{last_output}}`. Call `maestro_list_tasks(limit=30)` and inspect recent Capability Spotlight artifact markers when available.

Extract the last 12 runs' fields:

`FAMILY_ID TOPIC_ID DEMO_ID STYLE_ID LAYOUT_ID PALETTE_ID VOICE_ID ASSET_HASHES EXECUTED_APIS EVIDENCE_URLS`

Do not select from the registry as a closed menu: its anchors are examples, not an allowlist. Build at least one candidate in each mode before choosing:

1. **Single Capability** — one service/model, one distinctive hero result;
2. **Workflow Campaign** — 2–4 services that produce one visible buyer outcome;
3. **Platform Story** — unified auth, catalog, SDK, tasks, billing, Agent, or automation proved by real calls/results.

Score every candidate on live truth, unique sales value, hero evidence, executable authorization, compatible assets, price evidence, and recent-history diversity. The highest-scoring eligible candidate wins; do not default to Image or to the easiest service.

Apply these exclusions:

- no `TOPIC_ID` from the last 8 runs for a single-capability episode;
- no `DEMO_ID` or `HERO_CASE_ID` from the last 12 runs;
- no recent 6 `WORKFLOW_ID` repeats;
- avoid the recent 4 `CAMPAIGN_MODE`, `HOOK_ID`, and climax grammar;
- avoid the last 3 voice families and palettes;
- the same service may return only with a different buyer, job, hero, and offer;
- derive a reproducible tiebreaker from `{{date_iso}}:{{run_count}}`; do not use unconstrained randomness;
- stop when history, authorization, live pricing, or hero evidence is unavailable—never fall back to a generic showcase.

Write the selected campaign mode and all marker IDs before generating anything.

## 3. Build and prove the capability graph

For a workflow candidate, build a small runtime capability graph before calling any generation tool.

**Node contract:** service/model, input modality, output modality, sync/async lifecycle, poll API, supported reference roles, authorized MCP/Skill, price payload, and accepted asset.

**Edge contract:** connect nodes only when an actual output can legally become the next input. Prove every edge from an OpenAPI input/output field or an already executed request. Valid patterns include public image URL→image edit/reference video, public video URL→remix/caption/Maestro, text/research→brief/script/voice, audio URL→reference-audio video/production, and tool trace→artifact/automation evidence. Never connect services because their names merely sound compatible.

A workflow uses **2–4 services** and sells one final outcome, not a logo parade. Each step must contribute to the same hero result and carry request/task/result evidence. A platform story needs at least two real cross-modal calls/results; a catalog card alone is not a hero.

aichat2 supports dynamic `load_mcp_server`, but unattended authorization is bounded. Load only the selected **2–4 MCP servers** from the current authorized pool; do not preload every schema or claim an unconnected service executed. A service outside the execution pool is eligible only when a real accepted public artifact already exists and its provenance is explicit.

## 4. Prove the unique advantage

Load only the selected capability MCPs/Skills. Execute or reuse the selected hero recipe and inspect every final asset at full resolution.

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

## 4. Write the sales blueprint before Maestro

This is a **product sales video**, not an API walkthrough or an internal evidence reel. Before loading Maestro, write the complete human-readable plan below. Do not call Maestro until the complete blueprint passes the preflight at the end of this section.

```text
SPOTLIGHT-SALES-BLUEPRINT:v2
CAMPAIGN_MODE: single | workflow | platform
PRODUCTS: <1–4 service/model ids>
FINAL_OUTCOME: <one thing the buyer gets>
AUDIENCE: <specific buyer in a specific work context>
ONE-LINE VALUE: <the outcome they are buying>
PAIN: <one concrete current frustration>
HOOK: <the first spoken and on-screen line>
BASIC_INTRO: <what it is, for whom, and the outcome>
HERO CASE: <one real representative accepted example>
UNIQUE ADVANTAGE: <the visibly provable reason to choose this capability/workflow/platform>
WORKFLOW: <ordered service/input/output/evidence edges, or N/A>
PRICE: <real quote(s), unit, source, request payload, and verification time>
OFFER: <what is easy or valuable about starting now>
CTA: <action plus destination>
TONE: <emotional arc>
VOICE: <voice id plus performance direction>
```

Then write a scene-by-scene storyboard. Every scene includes its time range, sales purpose, exact asset role/URL, on-screen copy, verbatim narration, transition/pacing, and the claim its pixels prove.

Use this 30-second persuasion sequence:

- **0–3 seconds — Hook:** Ace Data Cloud is visible immediately while a concrete pain, desire, or striking real result earns attention. Never use a slow logo intro or open by reading the product name.
- **3–7 seconds — Basic introduction:** one sentence says what the product is, who it is for, and the outcome it creates. Do not read a feature menu.
- **7–17 seconds — Hero case:** the real accepted output dominates the frame and creates the visual climax. Show input→result, ordinary→distinctive, or blocked→completed according to the topic playbook.
- **17–22 seconds — Three advantages:** at most three short, concrete benefits supported by the hero pixels or real workflow.
- **22–26 seconds — Integration and price:** show one minimal call or one-token workflow plus one understandable live price anchor.
- **26–30 seconds — Offer and CTA:** give a specific action and destination; the voice finishes with an action verb rather than reading URLs.

The complete narration is **65–80 English words**, written before submission. Use short sentences, pauses, and emphasis. Its emotional arc is pain/recognition → discovery → excited reveal → confident price → decisive action. Never say `accepted output`, `decoded-pixel proof`, `evidence bundle`, or other internal review language in customer-facing copy. Do not stretch neutral documentation prose across the runtime.

Map every supplied URL so Maestro never guesses:

```text
ASSET 1 — PAIN / BEFORE — <real URL, or explicitly AUTHOR-RENDERED PAIN with no fake product/UI claim>
ASSET 2 — HERO ACCEPTED OUTPUT — <mandatory accepted URL and why it proves the advantage>
ASSET 3 — DETAIL / COMPARISON — <real URL or declared decoded derivative with exact crop/state>
```

Pricing is evidence, not ad-lib copy. Prefer the actual hero call's returned Credit cost. Otherwise evaluate the topic's explicit `PRICE_SCENARIOS` payload against live pricing. Convert Credits to USD only when the current package rate is available and recorded in the blueprint. If a dynamic price cannot be evaluated, display Credits or `See live pricing`; never guess dollars, a discount, or a competitor comparison.

Preflight all nine questions before loading Maestro:

1. Does the first line create a concrete pain or desire within three seconds?
2. Does one sentence explain the product, buyer, and outcome?
3. Is the hero case distinctive to this service rather than generically attractive?
4. Is there one visible climax that works without narration?
5. Are all three advantages demonstrated by this case?
6. Is the price real, current, understandable, and bound to the demo request?
7. Does the CTA say what to do and where?
8. Does the narration sound like a sales performance rather than documentation?
9. Are hook, case, pacing, and voice visibly different from recent episodes?

If any answer is no, revise the blueprint before Maestro. **No real hero evidence means no Maestro submission.** The exact Maestro prompt must begin with `ADC-SPOTLIGHT:v1` as its first line, with no title, explanation, or Markdown fence before it. Put the complete blueprint verbatim from the second line onward, and include it in the draft artifact metadata so the episode is auditable before asynchronous rendering.

## 5. Choose a distinct creative system

Choose compatible IDs from the registry and recent-history exclusions.

Voice families:

- high-energy launch: `energetic-male`, `bright-female` — urgent hook, visible smile on reveal, decisive CTA;
- premium product desire: `storyteller-male`, `warm-female` — intimate pain, sensory reveal, confident offer;
- technical confidence: `clean-female`, `calm-male`, `anchor-female` — crisp mechanism, energized hero, slower price;
- benchmark/news: `anchor-female`, `deep-male` — use only when a verified metric is the hook, never as the default documentary cadence.

Styles: `editorial`, `swiss`, `industrial`, `luxury`, `vibrant`, `retro`, `futuristic`.

Layouts: `split-proof`, `timeline`, `comparison-field`, `ui-walkthrough`, `kinetic-type`, `full-bleed-case-study`.

Preserve source-media palettes. Brand consistency comes from the approved lockup, type scale, spacing, restrained cyan signature, and CTA—not recoloring every result cyan/indigo.

Generate narration only through Maestro's brokered Fish override. Verify the complete transcript, seven scene beats, final spoken CTA, proper-noun pronunciation, natural pace, and no missing tail. Do not stretch narration merely to fill runtime.

## 6. Build the production kit

Use the brand kit exactly. The first decoded frame names Ace Data Cloud and the capability. The final frame returns to the lockup and approved URLs.

The kit sent to Maestro contains:

- live facts and source URLs;
- for workflow mode, every ordered step's service, input, output, API/task ID, accepted URL, and the OpenAPI/request proof for each edge;
- for platform mode, at least two real cross-modal calls/results rather than catalog-only cards;
- selected IDs and recent-history exclusions;
- canonical brand source and authored wordmark rules;
- exact evidence assets with service→asset mapping;
- evidence-only request plus display request;
- the complete `SPOTLIGHT-SALES-BLUEPRINT:v2`, including hook, pain, basic introduction, hero case, three advantages, price proof, offer, CTA, storyboard, and verbatim narration;
- one clear viewer promise plus voice performance/style/layout IDs;
- explicit forbidden defects;
- a unique UUID task ID, used for exactly one Maestro submission.

Load Maestro only after the kit is complete. Submit one Pro production matching the requested format/language. A controlled activation test may reduce only duration and SKU to a 30-second Standard draft; it MUST still use a real accepted capability output, run final-MP4 pixel/audio inspection, execute initial review plus confirmation when changed, and satisfy every brand/evidence gate. Never disable inner review or replace live hero evidence with a mock merely to make the test faster.

Immediately after Maestro returns an accepted task, call `publish_artifact` **before any further inspection, waiting, polling, or narration**. The literal tool output `{'code': 'task_already_exists', 'task_id': '<same UUID>'}` is a successful exact-ID idempotent replay, even when the tool wrapper labels it as an error. In that case `<same UUID>` is the one accepted task: do not generate another UUID and do not call `maestro_create_video` again. The next and only allowed tool call is `publish_artifact`, referencing that exact task ID.

Record the accepted Maestro task as a draft. The artifact **summary itself** must begin verbatim with the complete marker below; putting IDs only in tags does not satisfy history evidence:

`ADC-SPOTLIGHT:v1 | FAMILY_ID=<id> | TOPIC_ID=<id> | DEMO_ID=<id> | STYLE_ID=<id> | LAYOUT_ID=<id> | PALETTE_ID=<id> | VOICE_ID=<id> | ASSET_HASHES=<hashes> | EXECUTED_APIS=<public paths> | EVIDENCE_URLS=<accepted URLs> | MAESTRO_TASK=<uuid> | SUBMISSION=accepted`

Follow the marker with live docs/API references and service→asset mapping. The outer Producer must then end; it must not poll Maestro. Artifact recording is part of submission, not a post-production step.

## 7. Time-boxed review and delivery

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

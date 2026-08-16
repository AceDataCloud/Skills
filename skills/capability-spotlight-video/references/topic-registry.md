# Capability Spotlight topic registry

Every topic block must keep this schema: `TOPIC`, `FAMILY`, `SERVICE`, `APIS`, `DOC_QUERY`, `MCP`, `PROMISE`, `DEMOS`, `EVIDENCE`, `CREATIVE`, `LIMITS`.

## TOPIC gpt-image-2-craft

- FAMILY: ai-image
- SERVICE: openai
- APIS: `/openai/images/generations`, `/openai/images/edits`
- DOC_QUERY: `gpt-image-2 image generation edits typography`
- MCP: OpenAI
- PROMISE: legible text and faithful edit/composite workflows, not generic text-to-image beauty shots.
- DEMOS:
  - `gpt2-editorial-typography`: a representative editorial poster, packaging system, or wayfinding composition with a short exact headline; inspect every character and spacing. Reject ordinary architecture/still life.
  - `gpt2-faithful-composite`: pass a real product/screenshot/QR source to `/openai/images/edits`; both the source URL and the accepted edits output URL are mandatory. This demo ID is forbidden when only `/openai/images/generations` executed—use `gpt2-editorial-typography` instead. Inspect both accepted images at full resolution before scripting. Record `present before`, `present after`, and `visibly changed` from decoded pixels—not prompt prose, URL order, dimensions, or filenames—and bind each row to the exact source/output URL. Only claim differences that this comparison proves. An element still visible in the accepted edit cannot be called removed, replaced, or omitted; an element absent from the labeled frame cannot be called present.
  - `gpt2-consistent-campaign`: edit one accepted hero into 2–3 placements while preserving product, typography, and brand geometry.
- EVIDENCE: exact source(s), accepted full-resolution result, three-column before/after/change inventory, character/crop checklist, executed API path(s), accepted evidence URL(s), and authored API panel. `gpt2-faithful-composite` specifically requires `/openai/images/edits` in `EXECUTED_APIS` and its accepted output in `EVIDENCE_URLS`; the script, labels, and narration must all agree with the inventory.
- CREATIVE: styles `editorial,vibrant,swiss`; layouts `kinetic-type,split-proof,comparison-field`; palettes must follow the chosen recipe; voices `energetic-male,bright-female,clean-female`.
- LIMITS: maximum 3 image calls; typography failure gets one targeted replacement; never redraw the canonical logo.

## TOPIC nano-banana-consistency

- FAMILY: ai-image
- SERVICE: nano-banana
- APIS: `/nano-banana/images`
- DOC_QUERY: `nano banana consistent subject variants`
- MCP: Nano_Banana
- PROMISE: one unmistakable subject remains coherent while location, angle, season, or usage changes.
- DEMOS:
  - `nano-product-worlds`: one fictional product across four genuinely different commercial environments.
  - `nano-character-continuity`: one non-real fictional character across four narrative beats with stable face, clothing, and proportions.
- EVIDENCE: full 2×2 result; per-quadrant consistency matrix; exact request/result mapping.
- CREATIVE: styles `editorial,warm,pastel`; layouts `comparison-field,full-bleed-case-study`; voices `warm-female,storyteller-male,clean-female`.
- LIMITS: reject if geometry or identity drifts; environments must differ visibly.

## TOPIC seedream-commercial-detail

- FAMILY: ai-image
- SERVICE: seedream
- APIS: `/seedream/images`
- DOC_QUERY: `seedream high resolution commercial image`
- MCP: Seedream
- PROMISE: high-resolution commercial material detail, controlled depth, and art-directed still life.
- DEMOS:
  - `seedream-material-macro`: luxury object/material macro with layered natural depth.
  - `seedream-environmental-campaign`: a bright environmental product scene with useful copy space and precise material rendering.
- EVIDENCE: full-resolution crop details plus full frame; exact model/size request.
- CREATIVE: styles `luxury,warm,editorial`; layouts `full-bleed-case-study,split-proof`; voices `warm-female,calm-male,storyteller-male`.
- LIMITS: do not reuse dark glass/prism studios; no fabricated brand marks.

## TOPIC minimax-h3-multimodal

- FAMILY: ai-video
- SERVICE: minimax
- APIS: `/minimax/videos`, `/minimax/tasks`
- DOC_QUERY: `MiniMax H3 video first last frame multimodal reference`
- MCP: Minimax
- PROMISE: H3 combines text with first/last frame, image, video, or audio references for controlled motion.
- DEMOS:
  - `h3-first-last-transition`: generate distinct first and last frames, then prove a coherent 6–8 second transition between them.
  - `h3-reference-performance`: use one reference image plus reference audio or video and show the accepted input→motion output relationship.
  - `h3-cinematic-t2v`: a camera-specific text-to-video recipe with observable motion, not a static beauty shot.
- EVIDENCE: actual input references, real accepted MP4, start/middle/end frames, request and task lifecycle.
- CREATIVE: styles `cinematic,industrial,futuristic`; layouts `timeline,split-proof,full-bleed-case-study`; voices `energetic-male,deep-male,bright-female`.
- LIMITS: one H3 generation plus one bounded replacement; video is mandatory evidence.

## TOPIC seedance-2-reference-control

- FAMILY: ai-video
- SERVICE: seedance
- APIS: `/seedance/videos`, `/seedance/tasks`
- DOC_QUERY: `Seedance 2.0 reference image audio video character consistency`
- MCP: Seedance
- PROMISE: Seedance 2.0 preserves a referenced person/character and can follow audio/video references at high resolution.
- DEMOS:
  - `seedance-character-reference`: use a safe fictional/non-private character reference across a new scene; compare identity at start/middle/end.
  - `seedance-image-reference-control`: use a public fictional product/interface image as `reference_image`; prove visible structure/text treatment remains recognizable while the accepted MP4 adds requested camera motion. Show the exact reference URL, request, and start/middle/end decoded output frames; do not claim person/character identity or motion-reference input.
  - `seedance-motion-reference`: supply reference video for motion/camera language and show the generated reinterpretation.
  - `seedance-audio-reference`: pair a character image and safe reference audio; verify motion/audio result without identity claims about real people.
- EVIDENCE: actual reference media at a provider-downloadable public HTTPS URL, accepted output MP4, frame/contact sheet, minimal multimodal request, task lifecycle. Remote video APIs must never receive `data:`, `blob:`, or local-file reference URLs; upload references first and verify HTTPS reachability.
- CREATIVE: styles `cinematic,vibrant,futuristic`; layouts `timeline,comparison-field,full-bleed-case-study`; voices `bright-female,energetic-male,storyteller-male`.
- LIMITS: never use private/celebrity identity; one generation plus one replacement; video required; reference media must be a public HTTPS URL and `return_last_frame` or other 2.5-only options require a Seedance 2.5 model.

## TOPIC acechat-agent-workspace

- FAMILY: ai-chat-agent
- SERVICE: aichat
- APIS: `/aichat2/conversations`, `/aichat2/mcp-servers`, `/aichat2/skills`, `/aichat2/memories`, `/aichat2/artifacts`, `/aichat2/scheduled-tasks`, `/aichat2/realtime`
- DOC_QUERY: `AceChat aichat2 MCP Skills Memory Scheduled Tasks Realtime`
- MCP: AceDataCloud
- PROMISE: a stateful agent workspace combines conversations, tools, MCP, Skills, Memory, Artifacts, schedules, and realtime voice.
- DEMOS:
  - `acechat-tool-trace`: run a safe read-only task with one MCP and one Skill; show the real tool trace and resulting artifact.
  - `acechat-memory-schedule`: demonstrate a real memory/scheduled-task lifecycle using sanitized UI screenshots and authored flow.
  - `acechat-realtime-workspace`: demonstrate the real realtime/voice connection and one supported tool interaction without fabricated UI.
- EVIDENCE: faithful live UI capture, sanitized tool trace, public API/docs, real artifact or scheduled run metadata.
- CREATIVE: styles `swiss,industrial,editorial`; layouts `ui-walkthrough,timeline,split-proof`; voices `clean-female,calm-male,anchor-female`.
- LIMITS: no account data, tokens, private memory, fake chat messages, or invented UI.

## TOPIC captcha-solving-lifecycle

- FAMILY: captcha
- SERVICE: hcaptcha,recaptcha,turnstile,image2text
- APIS: `/captcha/tasks`, `/captcha/recognition/image2text`, `/captcha/recognition/hcaptcha`, `/captcha/token/hcaptcha`, `/captcha/recognition/recaptcha2`, `/captcha/token/recaptcha2`, `/captcha/token/recaptcha3`, `/captcha/token/turnstile`
- DOC_QUERY: `captcha task recognition hcaptcha recaptcha turnstile image2text`
- MCP: hCaptcha, reCAPTCHA, Turnstile
- PROMISE: one authenticated asynchronous lifecycle handles multiple challenge families and returns auditable results.
- DEMOS:
  - `captcha-image2text`: use a synthetic/local numeric challenge, submit it, and show the real recognized result.
  - `captcha-task-lifecycle`: show create→lease/solve→task retrieve→result from a safe owned/test challenge.
  - `captcha-family-matrix`: compare hCaptcha/reCAPTCHA/Turnstile request shapes and one successful test result without targeting third-party accounts.
- EVIDENCE: synthetic or owned challenge only, real task IDs redacted in public frames, terminal result, minimal request/lifecycle diagram.
- CREATIVE: styles `industrial,swiss,futuristic`; layouts `timeline,comparison-field,ui-walkthrough`; voices `calm-male,clean-female,anchor-female`.
- LIMITS: authorized test use only; no bypass of third-party controls, credential collection, or private site data.

## TOPIC maestro-agent-production

- FAMILY: ai-video-production
- SERVICE: maestro
- APIS: `/maestro/videos`, `/maestro/tasks`, `/maestro/estimates`
- DOC_QUERY: `Maestro AI video production review remix edit extend`
- MCP: Maestro
- PROMISE: one brief becomes a reviewed, narrated, branded final production—not merely one generated clip.
- DEMOS:
  - `maestro-brief-to-film`: show a real brief→asset manifest→composition→visual review→final MP4 chain.
  - `maestro-review-refine`: show real initial review blockers, one concentrated refinement, confirmation review, and exact-byte delivery.
  - `maestro-remix`: use a safe prior task to demonstrate a targeted edit/remix with before/after evidence.
- EVIDENCE: real sanitized progress, review frames, result manifest, final MP4, actual duration/codec; no self-referential fake process UI.
- CREATIVE: styles `editorial,swiss,futuristic`; layouts `timeline,ui-walkthrough,comparison-field`; voices `storyteller-male,anchor-female,deep-male`.
- LIMITS: one parent Maestro task per Spotlight; avoid recursive unbounded video production.

## TOPIC platform-unified-api

- FAMILY: platform
- SERVICE: acedatacloud
- APIS: public catalog, docs, model catalog, selected service APIs
- DOC_QUERY: `Ace Data Cloud services models unified API documentation`
- MCP: AceDataCloud
- PROMISE: developers discover and call a broad catalog through consistent authentication, docs, task, and billing conventions.
- DEMOS:
  - `platform-live-catalog`: query real services/models/docs, then spotlight three different modalities with live cards and public API paths.
  - `platform-one-token-workflow`: explain one safe credential pattern across chat/image/video/search without showing private values.
- EVIDENCE: live catalog responses, model modalities, public docs, authored architecture; no unsupported model-count claims.
- CREATIVE: styles `swiss,editorial,industrial`; layouts `comparison-field,timeline,ui-walkthrough`; voices `anchor-female,calm-male,energetic-male`.
- LIMITS: use only live catalog facts; this is an occasional platform overview, not the default fallback.

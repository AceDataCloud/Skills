---
name: maestro-video
description: "Produce complete AI videos with Maestro via AceDataCloud API. Use when: Maestro, article-to-video, prompt-to-video, turn a brief or reference media into a finished captioned video, generate scripts/visuals/voiceover/music/editing in one workflow, create a video in a selected language, or remix/edit/extend a previous Maestro video. Covers task creation, progress polling, history, and final output retrieval."
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-maestro for tool-use.
---

# Maestro End-to-End Video Production

Use Maestro when the user wants a **finished video**, not only a generated clip. A headless AI director turns one natural-language brief into a script, visual assets, voiceover, music, edit, captions, quality checks, and one rendered video in one language.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Choose Maestro When

- The user wants an article, idea, product brief, or campaign turned into a complete video.
- The workflow needs scripting, visuals, narration, captions, and editing handled together.
- The user supplies product images, a logo, portrait, source footage, or reference audio.
- The user wants a video in a selected language; different languages require separate tasks.
- A completed Maestro video needs to be remixed, edited, or extended.

Use a model-specific video API such as Seedance, Kling, or Veo when the user only needs a short generated shot and wants direct model controls. Maestro may use multiple media services internally and is optimized for the finished production.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/maestro/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a 30-second beginner-friendly video explaining vector databases. End with one memorable takeaway.",
    "aspect": "16:9",
    "duration": 30,
    "scenario": "narrated",
    "langs": ["en"]
  }'
```

The successful creation response is HTTP `201` and contains a `task_id`. Maestro is asynchronous, so query the task until it reaches `succeeded` or `failed`:

```bash
curl -X POST https://api.acedata.cloud/maestro/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id>", "action": "retrieve"}'
```

Do not invent output URLs or report completion while the task is still running.

## Core Workflow

1. Translate the user's goal into a concrete production brief and choose exactly one output language. Confirm separate billable tasks before producing other language versions.
2. Call `POST /maestro/videos` and preserve the returned `task_id` and `trace_id`.
3. Poll `POST /maestro/tasks` at a reasonable interval.
4. Continue through nonterminal states; stop only at `succeeded` or `failed`.
5. On success, read the single delivered video in `response.data.variants`, including its language and actual `output_url`. Do not treat an empty result as a delivered video.
6. If requested, iterate by creating a new task with `action`, `ref_task_id`, and a change-focused prompt.

Polling and history queries are free; the video task is settled after production based on delivered output. Avoid submitting duplicate creation requests while an existing task is still running.

## Creation Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | required | Natural-language production brief: topic, audience, content, tone, and desired result |
| `action` | string | `generate` | `generate`, `remix`, `edit`, or `extend` |
| `ref_task_id` | string | - | Required for `remix`, `edit`, and `extend` |
| `file_urls` | string[] | - | Public image, video, or audio references, up to the limits enforced by the API |
| `langs` | string[] | `["zh-cn"]` | Exactly one output language code, e.g. `["en"]`; empty or multi-language arrays are invalid |
| `aspect` | string | `9:16` | `9:16`, `16:9`, or `1:1` |
| `duration` | integer | `30` | Target duration from 5 to 300 seconds |
| `scenario` | string | `auto` | `auto`, `narrated`, `captions`, `avatar`, or `drama` |
| `style` | string | `auto` | Preset or freeform visual direction |
| `voice` | string | `auto` | Cross-lingual voice preset or a 32-hex-character Fish reference ID |
| `callback_url` | string | - | Optional webhook called on success or failure |

### Production contract

Every request uses the complete production capability: all actions and scenarios, 5–300 seconds, exactly one language, and 1080p/30fps output. There are no quality tiers. Successful tasks cost **0.7 Credits per actual billed second**, with no scenario multiplier or language surcharge. Billing counts integer seconds, never exceeds the requested duration, and falls back to the requested duration if delivered duration cannot be read. A 30-second billed video costs 21 Credits. Failed tasks and polling are free; submission has no separate fee. Check current service pricing before creating a task.

### Scenarios

- `auto`: let the director choose from the brief.
- `narrated`: multi-scene explainer, documentary, brand, history, or product video with voiceover.
- `captions`: add kinetic captions to a source video supplied in `file_urls`.
- `avatar`: talking-head or digital-human video; provide a portrait in `file_urls`.
- `drama`: acted short drama with characters and dialogue.

### Styles

Named presets include `cinematic`, `glass`, `luxury`, `swiss`, `modern`, `editorial`, `warm`, `vibrant`, `neon`, `mono`, `pastel`, `bold`, `industrial`, `futuristic`, and `retro`. The API also accepts a freeform style hint.

### Voices

Available presets include:

- Female: `warm-female`, `bright-female`, `anchor-female`, `clean-female`
- Male: `calm-male`, `deep-male`, `documentary-male`, `energetic-male`, `storyteller-male`
- Automatic: `auto`

Voice controls timbre rather than language. The same preset speaks the language selected in `langs`.

## Reference Media

Pass public URLs in `file_urls`:

```json
{
  "prompt": "Create a product launch video that clearly shows the camera body and logo. Use the supplied audio as the tone reference.",
  "file_urls": [
    "https://example.com/product.jpg",
    "https://example.com/logo.png",
    "https://example.com/reference.mp3"
  ],
  "scenario": "narrated",
  "style": "editorial",
  "aspect": "16:9"
}
```

Reference URLs must be reachable by the service. Do not pass local file paths. Upload local assets first, then use their public URLs.

## Choose the Output Language

Keep `langs` as an array containing exactly one language code:

```json
{
  "prompt": "A concise English product walkthrough for first-time customers",
  "langs": ["en"],
  "voice": "warm-female",
  "duration": 45
}
```

Omitting `langs` defaults to `["zh-cn"]`. Multiple languages return HTTP 400. For German or Japanese versions, confirm the additional tasks with the user, then submit separate requests with `["de"]` or `["ja"]` and a language-specific brief. Track each task ID independently; do not promise shared visuals across tasks. Each successful task delivers one video in `response.data.variants` at the same per-second rate.

## Iterate on a Previous Video

All iteration actions require `ref_task_id`.

### Remix

Use `remix` for a new creative interpretation that keeps the previous task as context:

```json
{
  "action": "remix",
  "ref_task_id": "previous-task-id",
  "prompt": "Rework this as a faster social cut with a stronger opening hook and neon styling.",
  "aspect": "9:16"
}
```

### Edit

Use `edit` for targeted revisions:

```json
{
  "action": "edit",
  "ref_task_id": "previous-task-id",
  "prompt": "Keep the structure and visuals. Replace the final call to action and use a calmer narrator."
}
```

### Extend

Use `extend` to continue or lengthen the production:

```json
{
  "action": "extend",
  "ref_task_id": "previous-task-id",
  "prompt": "Add a 15-second customer example before the conclusion.",
  "duration": 60
}
```

Iteration creates a new task. Continue polling the new `task_id`; do not overwrite or confuse it with the source task.

## Task Response

Use top-level `status` to determine completion, not `progress.stage` or a progress percentage. Display `progress.percent`, `progress.stage`, and `progress.message` when present; a successful task can still show its last production stage.

On `succeeded`, inspect `response.success` and `response.data.variants`. The array contains one video in the selected language, with fields such as `lang`, `aspect`, `title`, and `output_url`. Return the real delivered URL. `response.data.project` may include `tarball_url` and `outputs`; return a project download only when its URL is present. On `failed`, report the actual error rather than a fabricated video.

Return only fields actually present; never fabricate missing captions, covers, durations, or QC scores.

## Task Retrieval

Retrieve a task by its required `id`; the only documented action is `retrieve`:

```bash
curl -X POST https://api.acedata.cloud/maestro/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "TASK_ID", "action": "retrieve"}'
```


## Prompting Guidance

A useful brief answers:

- What is the subject and desired outcome?
- Who is the audience?
- What facts, products, people, or scenes must appear?
- What should the viewer feel or do afterward?
- Which platform determines aspect ratio and pacing?
- Are there exact brand, compliance, or wording constraints?

Prefer a concrete production brief over a list of low-level model instructions. Maestro is responsible for choosing and orchestrating media tools.

## Gotchas

- This API is asynchronous. Always preserve and poll the returned `task_id`.
- Terminal states are `succeeded` and `failed`; other status names may evolve as the production pipeline changes.
- `remix`, `edit`, and `extend` fail without `ref_task_id`.
- `file_urls` must be public URLs, not local paths.
- `avatar` usually needs a usable portrait reference.
- Requested duration is a target; report the actual delivered duration from the result.
- `langs` must contain exactly one language; empty or multi-language arrays are invalid. Different languages require separately confirmed tasks.
- Do not resubmit the same brief merely because a long-running poll has not finished.
- Do not expose the API token in logs, output, source files, or examples.

> **MCP:** `pip install mcp-maestro` | Hosted: `https://maestro.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
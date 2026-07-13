---
name: maestro-video
description: "Produce complete AI videos with Maestro via AceDataCloud API. Use when: Maestro, article-to-video, prompt-to-video, turn a brief or reference media into a finished captioned video, generate scripts/visuals/voiceover/music/editing in one workflow, create multilingual video variants, or remix/edit/extend a previous Maestro video. Covers task creation, progress polling, history, and final output retrieval."
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-maestro for tool-use.
---

# Maestro End-to-End Video Production

Use Maestro when the user wants a **finished video**, not only a generated clip. A headless AI director turns one natural-language brief into a script, visual assets, voiceover, music, edit, captions, quality checks, and rendered video variants.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Choose Maestro When

- The user wants an article, idea, product brief, or campaign turned into a complete video.
- The workflow needs scripting, visuals, narration, captions, and editing handled together.
- The user supplies product images, a logo, portrait, source footage, or reference audio.
- One visual production must be rendered in multiple languages.
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
    "quality": "standard",
    "scenario": "narrated",
    "langs": ["en"]
  }'
```

The response contains a `task_id`. Maestro is asynchronous, so query the task until it reaches `succeeded` or `failed`:

```bash
curl -X POST https://api.acedata.cloud/maestro/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id>", "action": "retrieve"}'
```

Do not invent output URLs or report completion while the task is still running.

## Core Workflow

1. Translate the user's goal into a concrete production brief.
2. Call `POST /maestro/videos` and preserve the returned `task_id` and `trace_id`.
3. Poll `POST /maestro/tasks` at a reasonable interval.
4. Continue through nonterminal states; stop only at `succeeded` or `failed`.
5. On success, return every item in `response.data.variants`, including its language and `output_url`.
6. If requested, iterate by creating a new task with `action`, `ref_task_id`, and a change-focused prompt.

Polling and history queries are free; the video task is settled after production based on delivered output. Avoid submitting duplicate creation requests while an existing task is still running.

## Creation Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | required | Natural-language production brief: topic, audience, content, tone, and desired result |
| `action` | string | `generate` | `generate`, `remix`, `edit`, or `extend` |
| `ref_task_id` | string | - | Required for `remix`, `edit`, and `extend` |
| `file_urls` | string[] | - | Public image, video, or audio references, up to the limits enforced by the API |
| `langs` | string[] | `["zh-cn"]` | Output language codes; each creates a localized rendered variant |
| `aspect` | string | `9:16` | `9:16`, `16:9`, or `1:1` |
| `duration` | integer | `30` | Target duration from 1 to 600 seconds |
| `quality` | string | `standard` | `draft`, `standard`, or `premium` |
| `scenario` | string | `auto` | `auto`, `narrated`, `drama`, `avatar`, `motion`, or `slideshow` |
| `style` | string | `auto` | Preset or freeform visual direction |
| `voice` | string | `auto` | Cross-lingual voice preset or a 32-hex-character Fish reference ID |
| `callback_url` | string | - | Optional webhook called on success or failure |

### Quality

- `draft`: fast rough cut for validating direction.
- `standard`: balanced default for normal production.
- `premium`: richer, more polished production with a higher cost and longer turnaround.

### Scenarios

- `auto`: let the director choose from the brief.
- `narrated`: multi-scene explainer, documentary, brand, history, or product video with voiceover.
- `drama`: acted short drama with characters and dialogue.
- `avatar`: talking-head or digital-human video; normally provide a portrait in `file_urls`.
- `motion`: kinetic typography, data, logo, or abstract motion graphics.
- `slideshow`: presentation deck, pitch, or slide-led video.

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

## Multilingual Variants

Use one request to reuse the production across languages:

```json
{
  "prompt": "A concise product walkthrough for first-time customers",
  "langs": ["en", "de", "ja"],
  "voice": "warm-female",
  "duration": 45
}
```

The first language is primary. A successful task normally returns one item per delivered language in `response.data.variants`. Do not assume every requested language succeeded; inspect the actual variants.

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

A task response exposes top-level progress for user feedback:

```json
{
  "id": "task-id",
  "status": "producing",
  "progress": {
    "percent": 52,
    "stage": "visuals",
    "message": "Generating scene assets",
    "activity": "Creating scene 4"
  },
  "response": null
}
```

On success, inspect the delivered variants:

```json
{
  "status": "succeeded",
  "response": {
    "success": true,
    "data": {
      "variants": [
        {
          "lang": "en",
          "output_url": "https://cdn.example/video.mp4",
          "captions_url": "https://cdn.example/captions.vtt",
          "cover_url": "https://cdn.example/cover.jpg",
          "duration": 31.2,
          "qc_score": 0.96
        }
      ]
    }
  }
}
```

Treat the fields above as a shape guide. Return fields that are actually present; never fabricate missing captions, covers, durations, or QC scores.

## List Recent Tasks

The live task endpoint also supports account history:

```bash
curl -X POST https://api.acedata.cloud/maestro/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve_batch", "limit": 20}'
```

Optional Unix timestamp filters are `created_at_min` and `created_at_max`. The authenticated identity determines which tasks are returned; do not supply or trust a body-level user ID.

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
- Multilingual requests may return fewer variants than requested if one output fails.
- Do not resubmit the same brief merely because a long-running poll has not finished.
- Do not expose the API token in logs, output, source files, or examples.

> **MCP:** `pip install mcp-maestro` | Hosted: `https://maestro.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
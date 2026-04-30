---
name: validate-nano
description: Run production validation suites for AceDataCloud Nano Banana image generation and editing. Use when testing Nano Banana deployments, checking 1K/2K/4K behavior, callback-mode task persistence, arbitrary input aspect ratios, or producing a complete input/output validation report.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN or ACEDATACLOUD_API_KEY in the environment.
---

# Validate Nano Banana

Use this skill to validate live Nano Banana image generation and editing after a deployment. The validation flow always submits requests with `callback_url`, polls the persisted task, downloads output images, measures dimensions, and writes a full report containing each case's input and output.

## When To Use

- A Nano Banana worker/provider was deployed and needs production smoke testing.
- Customers report 1K/2K/4K generation or edit failures.
- You need to verify image edits where the input aspect ratio is not one of the upstream enum values.
- You need an audit-friendly report with request payloads, initial task responses, final task responses, output image URLs, and dimensions.

## Quick Start

From the `Skills` repository:

```bash
export ACEDATACLOUD_API_TOKEN="..."
python3 skills/validate-nano/validate_nano.py
```

The script writes reports under `artifacts/nano-validation/<timestamp>/`:

- `report.json` contains machine-readable full inputs and outputs.
- `report.md` contains a readable summary plus the complete JSON blocks for each case.

Use the production API token from `.claude/.env` when validating AceDataCloud production from the monorepo:

```bash
cd /Users/qicu/Projects/AceDataCloud/Skills
set -a
source ../.claude/.env
set +a
ACEDATACLOUD_API_TOKEN="$ACEDATACLOUD_API_KEY" \
  python3 skills/validate-nano/validate_nano.py
```

## Case Matrix

The default suite covers both generation and editing:

| Case | Purpose | Request Highlights |
| --- | --- | --- |
| `generate_1k_square` | Basic generation callback smoke test | `action=generate`, `model=nano-banana-2`, `aspect_ratio=1:1`, `resolution=1K` |
| `generate_2k_landscape` | Higher-resolution generation with explicit enum ratio | `action=generate`, `model=nano-banana-2`, `aspect_ratio=16:9`, `resolution=2K` |
| `edit_2k_arbitrary_ratio_no_aspect` | Regression test for arbitrary-ratio edits | `action=edit`, `model=nano-banana-2`, `resolution=2K`, no `aspect_ratio` |
| `edit_4k_arbitrary_ratio_no_aspect` | Same regression at 4K | `action=edit`, `model=nano-banana-2`, `resolution=4K`, no `aspect_ratio` |

The default edit source image is intentionally non-enum ratio (`2008x2598`, reduced ratio `1004:1299`) because it previously reproduced upstream `aspect_ratio must be one of ...` failures when workers auto-forwarded exact detected ratios.

## Options

```bash
python3 skills/validate-nano/validate_nano.py \
  --api-base https://api.acedata.cloud \
  --callback-url https://api.acedata.cloud/health \
  --case edit_2k_arbitrary_ratio_no_aspect \
  --case edit_4k_arbitrary_ratio_no_aspect \
  --timeout 900 \
  --poll-interval 10
```

Important options:

| Option | Default | Description |
| --- | --- | --- |
| `--api-base` | `https://api.acedata.cloud` | API base URL. |
| `--callback-url` | `https://api.acedata.cloud/health` | Callback URL sent with every request. Use a real webhook if you need to inspect callback delivery; the default still forces callback task mode. |
| `--case` | all cases | Repeat to run a subset. |
| `--source-image-url` | known arbitrary-ratio image | Source image for edit cases. |
| `--output-dir` | `artifacts/nano-validation` | Parent directory for timestamped reports. |
| `--timeout` | `900` | Per-case polling timeout in seconds. |
| `--poll-interval` | `10` | Poll interval in seconds. |

## Validation Rules

For every case, the report must include:

- case name and purpose
- exact request payload, including `callback_url`
- HTTP status and initial API response
- task ID and trace ID when present
- final task response from `POST /nano-banana/tasks`
- output image URLs found recursively in the final response
- dimensions for source and output images when downloadable
- pass/fail status and error details

The run should fail if any case cannot get a task ID, reaches timeout, returns an error state, or completes without output image URLs.

## Nano Banana Callback Pattern

1. Submit to `POST /nano-banana/images` with `callback_url`.
2. Read the returned `task_id` or `id`.
3. Poll `POST /nano-banana/tasks` with `{"id": "<task_id>"}` until the task contains a terminal response.
4. Record both the initial response and final task response in the report.

Use `callback_url` even when polling. Callback mode is what makes tasks queryable later.

## Gotchas

- For edit requests that omit `aspect_ratio`, do not add, infer, snap, or default it in the test payload. This checks that upstream adapts the source image directly.
- Do not print or store the bearer token in reports.
- 4K cases can take several minutes and should use a generous timeout.
- `nano-banana/tasks` uses `id` in the poll request body.
- The default callback URL is only a callback-mode trigger. Use a real webhook URL if the deployment specifically needs callback delivery verification.

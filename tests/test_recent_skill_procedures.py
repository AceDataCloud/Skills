import importlib.util
import io
import json
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).parents[1]


def read_skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def json_examples(text):
    for block in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
        yield json.loads(re.sub(r"^POST /[^\n]+\n", "", block))


class SunoAudioProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = {
            "canonical": read_skill("suno-music"),
            "claude": (ROOT / "claude-plugins/suno-by-ace-data-cloud/skills/suno/SKILL.md").read_text(),
            "amp": (ROOT / "platforms/amp/skills/suno-by-acedatacloud/SKILL.md").read_text(),
        }

    def test_negative_tags_has_custom_scope_without_a_fixed_limit_promise(self):
        for name, text in self.skills.items():
            with self.subTest(skill=name):
                line = next(line for line in text.splitlines() if "`negative_tags`" in line and "`custom: true`" in line)
                self.assertIn("`replace_section`", line)
                self.assertNotIn("only with", line)
                self.assertIn("no fixed character limit", line.lower())
                self.assertIn("keep it concise", line)
                self.assertIn("overly long input may still fail", line)

    def test_processing_failures_keep_ids_and_require_safe_recovery(self):
        for name, text in self.skills.items():
            with self.subTest(skill=name):
                recovery = text.split("## Audio processing failure recovery\n", 1)[-1] if name == "canonical" else text.split("## Custom inputs and processing failures\n", 1)[1]
                for requirement in (
                    "downloadable audio file does not guarantee its `audio_id` remains usable",
                    "HTTP 500", "suno_processing_unavailable",
                    "suno_model_unavailable", "suno_processing_failed",
                    "HTTP 500 `api_error`", "`the account may have been offline`",
                    "`task_id` and `trace_id` when returned",
                    "contact support with those IDs, never the API key",
                    "existing task", "submission is uncertain",
                    "automatically retry a paid operation or silently switch models",
                ):
                    self.assertIn(requirement, recovery)
                self.assertNotIn("```", recovery.split("## Gotchas", 1)[0])


class MusicActionInputTests(unittest.TestCase):
    def test_producer_examples_follow_action_specific_requirements(self):
        text = read_skill("producer-music")
        requests = [json.loads(body) for body in re.findall(
            r"```json\nPOST /producer/audios\n(.*?)\n```", text, re.DOTALL
        )]
        requests += [json.loads(body) for body in re.findall(r"-d '(\{.*?\})'", text, re.DOTALL)]
        self.assertGreaterEqual(len(requests), 6)
        for body in requests:
            with self.subTest(body=body):
                action = body["action"]
                if action == "generate":
                    if not body.get("custom", False):
                        self.assertTrue(body["prompt"])
                    elif not body.get("instrumental", False):
                        self.assertTrue(body["lyric"])
                else:
                    self.assertTrue(body["audio_id"])
                    if action == "extend":
                        self.assertGreater(body["continue_at"], 0)
                        self.assertTrue(body.get("instrumental") or body.get("lyric"))
                self.assertNotEqual(body.get("lyric"), "")
                self.assertNotEqual(body.get("prompt"), "")
        instrumental = next(body for body in requests if body.get("instrumental"))
        self.assertTrue(instrumental["custom"])
        self.assertNotIn("lyric", instrumental)
        self.assertNotIn("prompt", instrumental)
        stems = next(body for body in requests if body["action"] == "stems")
        self.assertEqual(set(stems), {"action", "audio_id"})
        self.assertNotIn("Required for every `/producer/audios` request; use", text)
        for line in text.splitlines():
            if line.startswith(("| `lyrics_strength`", "| `sound_strength`")):
                self.assertIn("default: 0.5", line)

    def test_suno_action_controls_keep_source_timing_and_completion_boundaries(self):
        text = read_skill("suno-music")
        for requirement in (
            "`continue_at > 0`", "`30.792`", "without rounding",
            "not the earlier song", "`persona_id` is a voice ID, not a song ID",
            "`artist_consistency` and `artist_consistency_vox` require it",
            "Extra voice IDs are not used by `extend` or `upload_extend`",
            "at least two `mashup_audio_ids`", "nonnegative `replace_section_start`",
            "`replace_section_end` greater than the start", "no later than the source duration",
            "`samples_start` defaults to 0", "required `samples_end`",
            "Both support fractional seconds", "This is not Inspo",
            "1–4 publicly accessible authorized HTTP(S) `audio_urls`",
            "`all_stems` waits for every stem before terminal success",
            "Only `generate` uses `duration`", "other actions do not",
            "`variety`", "`max_mode`", "explicit user selection and a current price check",
            "preserve explicit `0` control values", "`suno_generate_with_custom_model`",
            "`suno_manage_project`", "`idempotency_key`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        for tool in ("suno_add_stem", "suno_extract_stem", "suno_generate_sound", "suno_adjust_speed"):
            self.assertIn(f"`{tool}`", text)


class FluxAndWebExtratorInputTests(unittest.TestCase):
    def test_flux_examples_use_model_appropriate_explicit_sizes(self):
        text = read_skill("flux-image")
        requests = list(json_examples(text))
        requests += [json.loads(body) for body in re.findall(r"-d '(\{.*?\})'", text, re.DOTALL)]
        self.assertEqual(len(requests), 3)
        ratio_models = {"flux-2-flex", "flux-2-pro", "flux-2-max", "flux-kontext-pro", "flux-kontext-max"}
        for body in requests:
            with self.subTest(body=body):
                pattern = r"\d+:\d+" if body["model"] in ratio_models else r"\d+x\d+"
                self.assertRegex(body["size"], pattern)
                self.assertTrue(body["prompt"])
        self.assertIn("`flux-2-klein` supports generation only", text)
        self.assertIn("`flux_edit_image`", text)
        self.assertNotIn("dev/pro/flux-2 models", text)

    def test_webextrator_defaults_cookie_shape_and_cache_controls(self):
        text = read_skill("webextrator")
        render = next(body for body in json_examples(text) if "wait_until" in body)
        self.assertEqual(render["wait_until"], "load")
        for requirement in (
            "(default `load`)", "positive integer seconds (minimum 1, default 30)",
            "not a total processing deadline", "nonnegative integer seconds",
            "`name`, `value`, `domain`", "Unix-seconds `expires`",
            "`httpOnly`, `secure`, and `sameSite`", "`Strict`, `Lax`, `None`",
            "nested cookie keys keep their exact casing", "top-level request uses snake_case",
            "`bypass_cache`", "skips cache reads", "may still be written to cache",
            "`cache_ttl_seconds`", "default 3600", "`0` disables caching this response",
            "only for sites the user authorizes", "never print their values or commit them",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("default `networkidle`", text)


class SunoPrivateVoiceCoverProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("suno-music").split("#### Cover with a specified voice\n", 1)[1]
        cls.text = cls.text.split("### 5. Full Song Creation Workflow\n", 1)[0]

    def test_create_upload_cover_examples_preserve_voice_and_audio_ids(self):
        voice, upload, cover = json_examples(self.text)
        self.assertEqual(voice, {"audio_url": "HTTPS_VOICE_REFERENCE_URL", "name": "My Voice"})
        self.assertEqual(upload, {
            "audio_url": "HTTPS_ORIGINAL_SONG_URL",
            "mode": "standard",
            "persona_id": "PERSONA_ID",
        })
        self.assertEqual(cover["action"], "upload_cover")
        self.assertEqual(cover["model"], "chirp-v6")
        self.assertEqual(cover["audio_id"], "VOICE_LINKED_UPLOAD_AUDIO_ID")
        self.assertEqual(cover["persona_id"], upload["persona_id"])
        self.assertIs(cover["custom"], True)
        self.assertIs(cover["instrumental"], False)
        self.assertTrue(cover["lyric"].startswith("[Verse]\n"))
        self.assertIs(cover["async"], True)
        self.assertNotIn("vocal_gender", cover)
        self.assertEqual(re.findall(r"^POST (/[^\n]+)$", self.text, re.MULTILINE),
                         ["/suno/voices", "/suno/upload", "/suno/audios"])

    def test_private_voice_constraints_and_terminal_cover_evidence(self):
        for requirement in (
            "`generate`, `cover`, or `upload_cover`",
            "`vocal_gender` is not required and cannot replace a voice ID",
            "voice similarity depends on the reference and result",
            "private voice", "user is authorized to use",
            "same service channel", "Reuse the voice's actual `persona_id`",
            "returned `data.persona_id`", '`mode: "standard"` (the default)',
            'never `mode: "enhanced"`', "After upload succeeds",
            "returned `data.audio_id` with the same `persona_id`",
            "Do not reuse an older audio ID",
            "Poll the cover's original task via `/suno/tasks` to terminal success",
            "preview URL is not a finished cover", "**Allowed APIs**",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn('"success":', self.text)
        self.assertNotIn('"is_public":', self.text)


class SunoAvailabilityProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("suno-music")

    def precheck(self):
        return self.text.split("## Audio availability precheck (Beta)\n", 1)[1].split("## Core Workflows\n", 1)[0]

    def test_request_is_authenticated_synchronous_and_audio_id_only(self):
        text = self.precheck()
        payload = json.loads(re.search(r"-d '(\{.*?\})'", text, re.DOTALL).group(1))
        self.assertEqual(payload, {"audio_id": "33333333-3333-4333-8333-333333333333"})
        for requirement in (
            "POST https://api.acedata.cloud/suno/availability",
            "Authorization: Bearer $ACEDATACLOUD_API_TOKEN",
            "Content-Type: application/json",
            "**Allowed APIs**", "UUID", "not a `task_id`",
            "currently costs 0 Credits", "returns synchronously",
            "do not poll `/suno/tasks` for this check",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertIn("| `/suno/availability` | POST |", self.text)

    def test_positive_evidence_is_not_a_processing_guarantee_or_false_result(self):
        text = self.precheck()
        for requirement in (
            "`success=true`", "`data.id`", "`data.available=true`",
            "never returns `data.available=false`",
            "current channel at check time", "not a guarantee",
            "HTTP 503 `availability_unknown`", "unknown, not unavailable",
            "HTTP 400", "HTTP 401", "HTTP 429", "HTTP 500",
            "`error.code` and `error.message`", "`task_id` and `trace_id`",
            "Do not automatically retry a paid operation or silently switch models",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn('"success":', text)
        self.assertNotIn('"available":', text)
        self.assertIn("check audio availability", (ROOT / "README.md").read_text())


class SunoPersonaProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("suno-music").split("## Persona management\n", 1)[1]
        cls.text = cls.text.split("## Advanced Parameters\n", 1)[0]

    def test_list_and_delete_examples_keep_auth_and_query_parameters(self):
        listing, deletion = re.findall(r"```bash\n(.*?)\n```", self.text, re.DOTALL)
        for command in (listing, deletion):
            self.assertIn("--get https://api.acedata.cloud/suno/persona", command)
            self.assertIn("Authorization: Bearer $ACEDATACLOUD_API_TOKEN", command)
            self.assertNotIn("--header", command)
            self.assertEqual(command.count("-H "), 1)
        self.assertNotIn("--request DELETE", listing)
        for query in ("user_id=USER_ID", "limit=50", "offset=0"):
            self.assertIn(f'--data-urlencode "{query}"', listing)
        self.assertIn("--request DELETE", deletion)
        self.assertIn('--data-urlencode "persona_id=PERSONA_ID"', deletion)

    def test_method_billing_does_not_remove_delete_confirmation(self):
        for requirement in (
            "same AceDataCloud service Bearer token", "**Allowed APIs**",
            "`GET /suno/persona` listing and `DELETE /suno/persona` deletion cost 0 Credits",
            "no extra billing-exemption header is required",
            "`POST /suno/persona` creation still follows the endpoint's current pricing rules",
            "do not assume all persona operations are free",
            "`limit` defaults to 50", "`offset` to 0", "returned `items` and `count`",
            "reuse actual `persona_id`", "confirm the intended persona with the user",
            "free billing is not authorization for deletion",
            "`user_id` is optional for ownership verification",
            "Check the returned `success` before reporting deletion",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn('"success":', self.text)


class RechargeCardProcedureTests(unittest.TestCase):
    def test_digital_redemption_preserves_private_delivery_and_credit_value(self):
        text = " ".join(read_skill("ace-recharge-card").split())
        for requirement in (
            "Neither the price nor the buyer's Envar wallet balance is the card's face value",
            "1, 100, 500, 1000 and 5000 Credits",
            "does not promise that every denomination", "configured value",
            "original purchase order's private delivery", "not to paste it into chat",
            "**Applications**", "**Redeem card**", "redemption is not enabled for that site",
            "credited amount, redemption", "new Credits balance",
            "redeemed only once", "does not enable automatic recharge",
            "Never request the full code for support", "last four characters",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)


class SunoProjectsProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("suno-music").split("## Studio Projects (Beta)\n", 1)[1]
        cls.text = cls.text.split("## Auxiliary Endpoints\n", 1)[0]

    def test_examples_use_versioned_project_actions(self):
        examples = {example["action"]: example for example in json_examples(self.text)}
        self.assertEqual(
            set(examples),
            {"create", "retrieve", "save", "upload", "add_track", "generate_track", "replace_section", "commit_candidate", "remove_track", "render"},
        )
        self.assertEqual(examples["save"]["state"], {"tracks": [], "timing": {"bps": 2}})
        self.assertNotIn("version_id", examples["save"])
        for action in ("upload", "add_track", "generate_track", "replace_section", "commit_candidate", "remove_track", "render"):
            with self.subTest(action=action):
                self.assertEqual(examples[action]["version_id"], "CURRENT_VERSION_ID")
        self.assertEqual(examples["replace_section"]["model"], "chirp-v6")
        self.assertLess(examples["replace_section"]["start_seconds"], examples["replace_section"]["end_seconds"])
        self.assertNotIn("start_beats", examples["commit_candidate"])
        self.assertNotIn("end_beats", examples["render"])

    def test_timing_and_upload_result_are_unambiguous(self):
        for requirement in (
            "beats per second",
            "must be positive",
            "120 BPM",
            "not audio-analysis bar positions",
            "source-audio seconds",
            "response.data.candidate.audio_id",
            "preserves playback speed",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_generation_and_candidate_recovery_are_version_safe(self):
        for requirement in (
            "render_audio_id",
            "stem_control_tags",
            "`generate_track` always submits two candidates",
            "shorter than 26 seconds",
            "Never silently switch models",
            "let the user choose",
            "Save an empty destination track **before** generating",
            "preserves the surrounding clips",
            "leaves the project unchanged",
            "Overlap on the destination track returns 400",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn("`chirp-v3-0`", self.text)

    def test_render_and_retry_require_terminal_evidence(self):
        for requirement in (
            "Muted tracks/clips are excluded",
            "only those tracks participate",
            "empty or inaudible project",
            "Success requires `finished_at` and `response.success=true`",
            "`response.success=false` indicates failure",
            "including failure, without generating again",
            "reusing a key with a different payload returns 409",
            "first confirm the original task failed, then use a new key",
            "Never resubmit while the original is processing or uncertain",
            "`trace_id`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_new_track_example_has_mix_reference_and_public_options(self):
        examples = {example["action"]: example for example in json_examples(self.text)}
        generate = examples["generate_track"]
        self.assertEqual(generate["source_audio_id"], "AUDIO_ID")
        self.assertEqual(generate["render_audio_id"], "RENDER_AUDIO_ID")
        self.assertEqual(generate["stem_control_tags"], "add Piano")
        self.assertEqual(generate["model"], "chirp-v5")
        self.assertNotIn("batch_size", generate)
        self.assertIn("do not send `batch_size`", self.text)
        self.assertNotIn("1–4 (default 2)", self.text)
        self.assertIs(generate["instrumental"], True)
        self.assertEqual(generate["vocal_gender"], "unspecified")
        self.assertLess(generate["start_seconds"], generate["end_seconds"])
        self.assertEqual(examples["remove_track"]["track_id"], "TRACK_ID")
        for requirement in (
            'type:"audio"', 'clips:[]', 'takeLanes:[]',
            "Save the complete state before generating",
            "response.data.audio_id", "response.data.operation_id",
            "response.data.candidates[].id", "not output-duration guarantees",
            "Generation does not add candidates to the project",
            "`negative_tags`", "`vocal_gender`", "not a guaranteed result",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_state_async_and_render_failure_boundaries(self):
        for requirement in (
            "replaces the complete state, not a patch", "preserve unknown fields",
            "completes synchronously even if its result includes `task_id`",
            "do not change the project version", "even with `async:false`",
            "Read `response.error` on failure", "including after a callback",
            "successful commit does not prove the project can render",
            "failed with `studio_audio_unavailable`",
            "duration matched neither the source nor the selected interval",
            "do not guess placement or automatically repeat paid generation",
            "remove only that track", "verify recovery",
            "do not assume cross-application reuse or automatic failover",
            "end must not exceed the actual source duration",
            "not verified by the documented Backend run",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)


class FishSavedVoiceProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("fish-audio")
        cls.saved = cls.text.split("### 5. Create a persistent public voice model\n", 1)[1]
        cls.saved = cls.saved.split("## Parameters", 1)[0]

    def test_create_example_uses_single_url_and_no_visibility_control(self):
        example, = json_examples(self.saved)
        self.assertEqual(set(example), {"title", "voices"})
        self.assertTrue(example["title"])
        self.assertEqual(example["voices"], "HTTPS_REFERENCE_AUDIO_URL")
        for requirement in (
            "POST /fish/model", "same AceDataCloud Bearer token",
            "single URL string, not an array", "HTTP 201",
            "model object directly", "actual `_id`", "as `reference_id`",
            "audio downloads", "sufficient duration", "recognized format",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.saved)

    def test_publication_requires_confirmation_and_cannot_be_made_private(self):
        for requirement in (
            "permission to clone and publish", "obtain explicit confirmation",
            "saved publicly long-term", "other users may search for and use it",
            "Do not proceed if a private saved voice is required",
            "`visibility` does not change publication",
            "even when set to `private` or `unlist`", "Omit it from requests",
            "temporary reference without a saved model",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.saved)
        self.assertIn("persistent public voice models", (ROOT / "README.md").read_text())

    def test_mcp_creation_and_reuse_keep_publication_confirmation(self):
        for requirement in (
            'fish_create_model(title="My authorized narration voice", voices="HTTPS_REFERENCE_AUDIO_URL")',
            "only after the same publication confirmation", "no private/unlisted option",
            "`fish_generate_audio(reference_id=...)`", "`fish_list_models(self=true)`",
            "For a one-shot reference", "`references` instead",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.saved)

    def test_self_list_is_account_scoped_not_private_or_author_equivalent(self):
        self.assertIn("?self=true&page_size=10&page_number=1&sort_by=created_at", self.saved)
        for requirement in (
            "created and saved through this platform", "current calling account",
            "different API Tokens for that same account", "only a list filter",
            "remain public and usable by others", "not equivalent to filtering",
            "1-based `page_number`", "newest creation first",
            "`created_at` and `task_count`", "`author_id` can further filter",
            "`title_language` is not supported with `self=true`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.saved)

    def test_pagination_handles_boolean_and_nullable_has_more(self):
        for requirement in (
            "`items`, `total`, and `has_more`",
            "For `self=true`, `has_more` is boolean; stop when false",
            "Public-library queries may return `has_more: null`",
            "use `total` and `page_size`", "instead of treating null as false",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.saved)


class CDNUploadProcedureTests(unittest.TestCase):
    def test_upload_preserves_multipart_and_platform_auth(self):
        text = read_skill("cos-upload")
        for requirement in (
            "POST https://platform.acedata.cloud/api/v1/files/",
            "Authorization: Bearer $ACEDATACLOUD_PLATFORM_TOKEN",
            '-F "file=@/path/to/video.mp4"', "On HTTP 200",
            "use the returned `file_url` rather than constructing a URL",
            "One file per request", "100 MB per file",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```json", text)

    def test_path_mime_and_retention_do_not_promise_conversion_or_archiving(self):
        text = read_skill("cos-upload")
        for requirement in (
            "unique `uploads/<uuid>` path", "filename's safe extension",
            "returned `mime`", "object-storage metadata",
            "extension matches the actual content", "MIME type is stored as supplied",
            "if omitted or `application/octet-stream`",
            "infers it from the filename", "standard MIME mappings",
            "Neither extension handling nor MIME inference converts",
            "publicly accessible without authentication", "do not upload sensitive data",
            "not a permanent-archive guarantee", "own object storage",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("CDN-served and stable", text)


class MaestroProcedureTests(unittest.TestCase):
    def test_all_creation_examples_select_one_language(self):
        text = read_skill("maestro-video")
        examples = list(json_examples(text))
        examples += [json.loads(body) for body in re.findall(r"-d '(\{.*?\})'", text, re.DOTALL)]
        creations = [body for body in examples if "prompt" in body]
        self.assertGreaterEqual(len(creations), 6)
        for body in creations:
            with self.subTest(body=body):
                self.assertEqual(len(body.get("langs", ["zh-cn"])), 1)
                self.assertNotIn("quality", body)
                if body.get("action") in {"remix", "edit", "extend"}:
                    self.assertIn("ref_task_id", body)
        for requirement in (
            'Omitting `langs` defaults to `["zh-cn"]`',
            "Multiple languages return HTTP 400", "empty or multi-language arrays are invalid",
            "confirm the additional tasks", "Track each task ID independently",
            "do not promise shared visuals across tasks",
        ):
            self.assertIn(requirement, text)

    def test_voice_is_a_preset_or_real_hex_id_not_freeform_style(self):
        text = read_skill("maestro-video")
        for requirement in (
            "actual 32-character hexadecimal Fish `reference_id`",
            "other freeform text is not a valid voice ID",
            "Freeform visual direction belongs in `style`, not `voice`",
        ):
            self.assertIn(requirement, text)

    def test_flat_billing_and_single_output_replace_old_contract(self):
        text = read_skill("maestro-video")
        for requirement in (
            "0.7 Credits per actual billed second", "no scenario multiplier or language surcharge",
            "Billing counts integer seconds", "never exceeds the requested duration",
            "falls back to the requested duration", "30-second billed video costs 21 Credits",
            "Failed tasks and polling are free", "submission has no separate fee",
            "no quality tiers", "1080p/30fps",
            "single delivered video in `response.data.variants`",
            "Use top-level `status` to determine completion",
            "empty result", "Return only fields actually present",
            "Do not resubmit the same brief",
        ):
            self.assertIn(requirement, text)
        for obsolete in ("0.60", "1.15×", "1.35×", "adds 6 Credits", "up to 4 languages", "Pro only"):
            self.assertNotIn(obsolete, text)
        self.assertNotIn('"captions_url"', text)
        self.assertNotIn('"qc_score"', text)
        self.assertIn("one language per task", (ROOT / "README.md").read_text())


class AccountBalanceAndUsageProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = read_skill("acedatacloud")
        cls.balance = text.split("### Balance / subscriptions", 1)[1].split("### Usage records", 1)[0]
        cls.usage = text.split("#### Retention-aware usage investigation\n", 1)[1].split("### Services", 1)[0]

    def test_saved_proxy_balance_is_not_availability_evidence(self):
        for requirement in (
            "balance --json", "`disabled` and `expired_at`", "`remaining_amount`",
            "positive balance alone is not an availability check",
            "paused balance synchronization or a synchronization timeout",
            "returns the last saved balance", "current service status in the console",
            "does not prove the service is currently usable",
            "same platform token, balance endpoint and field names",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.balance)

    def test_overdraft_balance_check_is_read_only_and_usage_scoped(self):
        for requirement in (
            "Check for null before comparing balances", "returned `service.unit`",
            "Read `allow_overdraft` from the application list or detail",
            "read-only boolean", "defaults to `false`", "separate administrator authorization",
            "do not try to enable it through application create/update parameters",
            '`type="Usage"` with `allow_overdraft=true`',
            "low or negative balance alone does not block calls", "normal usage charges continue",
            "negative balance is unsettled usage", "recharge offsets it without resetting `used_amount`",
            "Disabled applications, expiry and API credential limits still apply",
            "missing flag is not an overdraft grant", "`Period` applications do not support overdraft",
            "keeps charging its own balance even below zero",
            "does not switch to the global account due to insufficient balance",
            "`allow_consume_global` controls fallback",
            "global Application actually charged, not the originating one",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.balance)

    def test_balance_json_preserves_overdraft_and_nullable_or_negative_amounts(self):
        script = ROOT / "skills/acedatacloud/scripts/acedatacloud.py"
        spec = importlib.util.spec_from_file_location("acedatacloud_balance_skill", script)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        for flag in ({}, {"allow_overdraft": False}, {"allow_overdraft": True}):
            for remaining in (None, -2.5, 0, 10):
                with self.subTest(flag=flag, remaining=remaining):
                    item = {"id": "TEST_APPLICATION", "remaining_amount": remaining,
                            "type": "Usage", "service": {"unit": "Credit"}, **flag}
                    payload = {"count": 1, "items": [item]}
                    with patch.object(cli.sys, "argv", ["acedatacloud.py", "balance", "--json"]), patch.object(
                        cli, "_request", return_value=(200, payload)
                    ) as request, redirect_stdout(io.StringIO()) as output:
                        cli.main()
                    self.assertEqual(request.call_args.args[1:3], ("GET", "/applications/"))
                    self.assertEqual(json.loads(output.getvalue()), payload)

    def test_usage_window_and_body_lifetime_are_distinct(self):
        for requirement in (
            "list, aggregate and CSV export queries", "most recent 60 days",
            "call records and billing summaries share this window",
            "usage --days 7 --json", "usage-summary --days 30 --json",
            "older than 60 days returns HTTP 400", "narrow the range",
            "bodies are retained for only 30 days", "list omits bodies even for newer records",
            "authenticated `GET /usage/apis/{id}`", "actual record ID",
            "CLI has no usage-detail command", "records 30–60 days old",
            "no longer returns `metadata.request` or `metadata.response`",
            "do not treat their absence as a failed or free call",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.usage)

    def test_body_expiry_preserves_billing_and_requires_call_time_archiving(self):
        for requirement in (
            "trace, status, timestamps, model, usage and actual deducted amount",
            "Body expiry does not change actual deductions, usage or aggregate statistics",
            "model and effective-result summaries are retained before bodies expire",
            "Do not invent missing bodies", "secure storage",
            "authorized request/response bodies at call time",
            "CSV exports and aggregate statistics do not extend the body-retention window",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.usage)
        self.assertNotIn("```", self.usage)


class OrderProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("acedatacloud").split("### Orders (recharge)", 1)[1].split("### Platform tokens", 1)[0]
        script = ROOT / "skills" / "acedatacloud" / "scripts" / "acedatacloud.py"
        spec = importlib.util.spec_from_file_location("acedatacloud_order_skill", script)
        cls.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cli)

    def test_bank_transfer_requires_owner_options_and_confirmation(self):
        for requirement in (
            "Personal and business accounts", "without enterprise verification",
            "anonymous requests cannot", "at least USD 300",
            "payment-channel configuration and package eligibility",
            "GET /api/v1/orders/{order_id}/payment-options/",
            "CLI has no payment-options command", "Do not publish internal route/provider identifiers",
            "Confirm the order ID, amount and available route",
            "--pay-way BankTransfer --yes", "displayed CNY amount is authoritative",
            "not proof that funds arrived",
        ):
            self.assertIn(requirement, self.text)

    def test_invoice_reapplication_waits_for_completed_reversal(self):
        for requirement in (
            "GET /api/v1/orders/{order_id}/invoice/", "leaves the invoice `Issued`",
            "`red_state`", "Submission is not completion",
            "Do not reapply while confirmation", "issuance and archiving",
            "`Voided`", "require finance review", "do not bypass the restriction",
            "Manually issued invoices must first be voided or reversed",
        ):
            self.assertIn(requirement, self.text)

    def test_x402_arbitrum_selection_requires_live_accepts_and_native_usdc(self):
        text = self.text.split("#### X402 network selection\n", 1)[1].split("#### X402 failure recovery\n", 1)[0]
        for requirement in (
            "current order or API payment challenge's `accepts`",
            "Arbitrum One", "`arbitrum`", "`eip155:42161`",
            "opt-in code support, not guaranteed production availability",
            "If it is absent from `accepts`, do not attempt payment on that chain",
            "feature flag does not enable an unconfigured server network",
            "only `exact`", "native USDC (6 decimals)", "not bridged USDC or `upto`",
            "returned asset, recipient and `accepts[].maxAmountRequired`",
            "never hardcode an amount or invent payment parameters",
            "wallet supports the target chain", "USDC on that chain",
            "different balances on different networks",
            "Solana address is not an EVM USDC address",
            "Obtain confirmation before signing or paying",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```", text)
        self.assertNotIn("?features=", text)

    def test_x402_recovery_preserves_codes_and_unknown_charge_state(self):
        for requirement in (
            "initial HTTP 402", "payment challenge, not a failed payment",
            "extensions.acedatacloud.paymentError", "orders --json",
            "metadata.x402.last_error", "metadata.x402.errors",
            "`code`, `stage`, `retryable`, `charged` and `params`",
            "`reason`", "`timestamp`", "insufficient_token_balance", "invalid_signature",
            "Do not replace either with generic `payment_failed`",
            "missing `charged` means unknown, not uncharged",
            "Even if `retryable=true`, a `Failed` order cannot be retried in place",
            "obtain confirmation before creating and paying a new order",
            "Share only the order ID and public error code",
            "Never log or share full order metadata",
        ):
            self.assertIn(requirement, self.text)

    def test_x402_ace_burn_policy_does_not_promise_extra_charges_or_backfill(self):
        text = self.text.split("#### X402 ACE buyback and burn proof\n", 1)[1]
        for requirement in (
            "When the buyback policy is enabled", "eligible Base mainnet Circle USDC",
            "Solana mainnet USDC", "3% of the actual received amount",
            "no extra wallet charge", "Recharge is counted once",
            "spending those Credits on APIs does not count again",
            "Historical discounted orders and old-policy orders are not automatically backfilled",
            "no fixed per-operation or daily USDC buyback cap",
            "available funds, market quotes and chain confirmations can still delay completion",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_x402_ace_burn_proof_uses_owner_detail_not_list_or_anonymous_link(self):
        text = self.text.split("#### X402 ACE buyback and burn proof\n", 1)[1]
        for requirement in (
            "GET /api/v1/orders/{order_id}/", "as the order owner",
            "CLI only lists orders", "not an order-detail or burn command",
            "order list and anonymous pay-link response do not include `ace_burn`",
            "absent or null", "do not infer eligibility or fabricate proof",
            "`settlement_network`", "`settlement_transaction`", "`execution_network`",
            "Base receipt is not a Solana burn transaction",
            "Do not expose operator configuration or internal funding details",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```json", text)

    def test_x402_ace_burn_completion_is_independent_of_credits(self):
        text = self.text.split("#### X402 ACE buyback and burn proof\n", 1)[1]
        for requirement in (
            "`ace_burn.state=Completed`", "`swap_signature` and `burn_signature`",
            "actually returned", "`Pending`, `Processing` or `Review` is not proof",
            "order's `Finished` state does not prove the burn completed",
            "Base source finality can delay the burn without affecting already credited Credits",
            "Reread the same order", "do not repay or create another order",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_existing_bank_transfer_cli_is_dry_run_without_confirmation(self):
        argv = ["acedatacloud.py", "pay-order", "--id", "ORDER_ID", "--pay-way", "BankTransfer"]
        with patch.object(self.cli.sys, "argv", argv), patch.object(self.cli, "_request") as request, redirect_stdout(io.StringIO()) as output:
            self.cli.main()
        request.assert_not_called()
        self.assertIn("DRY RUN", output.getvalue())
        with patch.object(self.cli.sys, "argv", argv + ["--yes"]), patch.object(
            self.cli, "_request", return_value=(200, {})
        ) as request, redirect_stdout(io.StringIO()):
            self.cli.main()
        self.assertEqual(request.call_args.args[1:], ("POST", "/orders/ORDER_ID/pay/"))
        self.assertEqual(request.call_args.kwargs, {"body": {"pay_way": "BankTransfer"}})

    def test_existing_json_output_preserves_x402_error_without_inventing_charged(self):
        for charged in ({}, {"charged": False}, {"charged": True}):
            with self.subTest(charged=charged):
                error = {"code": "insufficient_token_balance", "stage": "verify", "retryable": True,
                         "params": {"network": "eip155:8453"}, "reason": "Insufficient USDC",
                         "timestamp": "2026-10-11T00:00:00Z", **charged}
                metadata = {"x402": {"last_error": error, "errors": [error]}}
                payload = {"count": 1, "items": [{"id": "ORDER_ID", "state": "Failed", "metadata": metadata}]}
                with patch.object(self.cli.sys, "argv", ["acedatacloud.py", "orders", "--json"]), patch.object(
                    self.cli, "_request", return_value=(200, payload)
                ), redirect_stdout(io.StringIO()) as output:
                    self.cli.main()
                self.assertEqual(json.loads(output.getvalue())["items"][0]["metadata"], metadata)


class AccountOAuthProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("acedatacloud").split("### OAuth account access\n", 1)[1]
        cls.text = cls.text.split("## CLI (preferred)\n", 1)[0]

    def test_current_scopes_pkce_and_credential_lookup(self):
        for requirement in (
            "not model API Keys", "does not create a Key",
            "`available_scopes`", "authenticated `GET https://auth.acedata.cloud/api/v1/oauth2/applications/`",
            "not the broader Discovery `scopes_supported`",
            "Old `profile`, `email`, `phone`, and `platform` scopes are not accepted aliases",
            "`account` selector is reserved", "Public clients must use S256, not `plain`",
            "Verify callback state", "single-use code", "exact registered `redirect_uri`",
            "`client_secret_post`, not HTTP Basic", "no `id_token` is returned",
            "GET https://auth.acedata.cloud/api/v1/users/me",
            "?user_id=<id>&limit=100&offset=0", "`items[*].token`",
            "rather than taking the first item", "`user_id=me` is invalid",
            "An empty list is not an authorization failure",
            "Never display or log Keys, codes, tokens, or PKCE verifiers",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_two_step_changes_require_visible_reauthorization_not_secret_collection(self):
        for requirement in (
            "Two-step verification is completed on Ace Data Cloud's authorization page",
            "before the authorization code is issued",
            "must not request, save or forward authenticator secrets or recovery codes",
            "may invalidate existing sessions, refresh tokens and related platform authorization tokens",
            "`invalid_grant`", "restart user-visible authorization",
            "do not loop with an old code or bypass verification",
            "Ordinary model API Key authentication is unchanged",
            "separate Key review and revocation",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertIn("has no scheduled expiry", read_skill("acedatacloud"))
        self.assertNotIn("and never expires", read_skill("acedatacloud"))

    def test_studio_and_token_lifecycle_do_not_overpromise(self):
        for requirement in (
            "acedatacloud:oauth:ready", "acedatacloud:oauth:init",
            "acedatacloud:oauth:authorize", "acedatacloud:oauth:result",
            "exact parent origin, parent window, and state",
            "not `offline_access` or blog permissions", "each visitor must consent separately",
            "does not inject Studio's login token or a Key",
            "Standard OAuth redirects do not require this message protocol",
            "first-login continuation has a known gap",
            "old refresh token immediately becomes invalid",
            "HTTP 200 without immediate invalidation of issued JWTs",
            "do not report that all tokens are revoked",
            "Copied API Keys must be separately revoked or rotated",
            "does not register OAuth apps or perform the browser/PKCE exchange",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertIn("scoped OAuth access", (ROOT / "README.md").read_text())


class NanoBanana21ProcedureTests(unittest.TestCase):
    def test_generation_and_editing_use_base_model_with_explicit_resolution(self):
        text = read_skill("nano-banana-image")
        examples = list(json_examples(text))
        self.assertEqual({example["action"] for example in examples}, {"generate", "edit"})
        for example in examples:
            self.assertEqual(example["model"], "nano-banana-2.1")
            self.assertEqual(example["resolution"], "2K")
        edit = next(example for example in examples if example["action"] == "edit")
        self.assertIsInstance(edit["image_urls"], list)
        for requirement in (
            "omitting `model` still selects `nano-banana`",
            "No `nano-banana-2.1:official` variant is published",
            "`nano-banana` and `nano-banana-2-lite` support only 1K",
            "2, 2.1, and Pro support all three resolutions",
            "public alias `/v1/images/generations`", "public alias `/v1/images/edits`",
            "`image` for JSON editing, not `image_urls`",
            "`size` rather than this endpoint's `resolution`/`aspect_ratio`",
            "do not assume identical response fields", "consult live pricing",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)


class ClaudeMessagesProcedureTests(unittest.TestCase):
    def test_native_route_and_extensible_parameters(self):
        text = read_skill("ai-chat")
        for requirement in (
            "/v1/messages/count_tokens",
            "/claude/messages/count_tokens",
            "public alias `/claude/messages`",
            "extension fields unchanged",
            "not enforce a frozen per-model enum",
            "not a closed enum",
            "between_tools",
            "budget_tokens",
            "parameter errors are returned to the caller",
            "generates no model output and consumes no quota",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_compatible_models_keep_messages_payload_and_structured_output(self):
        text = read_skill("ai-chat").split("## Native Claude Messages\n", 1)[1]
        text = text.split("## Stateful / Agentic Conversations\n", 1)[0]
        for model in (
            "gpt-6.1-sol", "gpt-6.1-terra", "gpt-6-sol", "gpt-6-luna", "gpt-6-astra",
            "gpt-5.6-sol-fast", "gpt-5.6-sol", "glm-5.3", "glm-5.2", "glm-5.1",
            "glm-5-turbo", "glm-5", "gemini-3.6-flash",
        ):
            self.assertIn(f"`{model}`", text)
        for requirement in (
            "Check the current route list, account access and pricing",
            "Keep Messages fields and response handling when switching models",
            "cross-protocol requests map their semantics",
            "`tools[].input_schema`", "`tool_use`", "`tool_result`", "matching IDs",
            "`tool_choice.disable_parallel_tool_use=true`",
            "platform does not automatically raise it", "`output_config.format`",
            "Messages `content` text blocks", "do not expect Chat `choices` or Responses `output`",
            "same model, messages, and applicable system/tools/thinking fields",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        structured, = json_examples(text)
        output_format = structured["output_config"]["format"]
        self.assertEqual(output_format["type"], "json_schema")
        self.assertEqual(output_format["schema"], {
            "type": "object", "properties": {"answer": {"type": "string"}},
            "required": ["answer"], "additionalProperties": False,
        })
        self.assertNotIn('"content":', json.dumps(structured))

    def test_native_example_uses_bearer_auth_without_metadata_guidance(self):
        text = read_skill("ai-chat")
        native = text.split("## Native Claude Messages\n", 1)[1].split("## Stateful / Agentic Conversations\n", 1)[0]
        payload = json.loads(re.search(r"-d '(\{.*?\})'", native, re.DOTALL).group(1))
        self.assertNotIn("metadata", payload)
        self.assertNotIn("metadata", payload["messages"][0])
        self.assertNotIn("`metadata`", native)
        self.assertNotIn("metadata.user_id", native)
        self.assertNotIn("example-user-001", native)
        self.assertIn('Authorization: Bearer $ACEDATACLOUD_API_TOKEN', native)
        self.assertTrue({"model", "messages", "max_tokens"}.issubset(payload))
        self.assertEqual(payload["model"], "claude-sonnet-5-5")
        self.assertEqual(payload["thinking"], {"type": "adaptive"})
        self.assertEqual(payload["output_config"], {"effort": "high"})

    def test_beta_display_and_signature_preservation(self):
        text = read_skill("ai-chat")
        self.assertIn("anthropic-beta: thinking-display-updates-2026-08-18", text)
        self.assertIn('thinking.display="updates"', text)
        self.assertIn("not rewritten to `summarized`", text)
        self.assertIn("return complete assistant thinking blocks and signatures unchanged", text)
        self.assertIn("Display settings do not disable thinking", text)


class KimiChatProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("ai-chat").split("## Kimi Chat Completions\n", 1)[1]
        cls.text = cls.text.split("## Native Gemini Generate Content\n", 1)[0]

    def test_request_uses_public_route_and_k31_effort(self):
        payload = json.loads(re.search(r"-d '(\{.*?\})'", self.text, re.DOTALL).group(1))
        self.assertEqual(set(payload), {"model", "messages", "reasoning_effort"})
        self.assertEqual(payload["model"], "kimi-k3.1-pro")
        self.assertEqual(payload["reasoning_effort"], "low")
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertTrue(payload["messages"][0]["content"])
        self.assertIn("https://api.acedata.cloud/kimi/chat/completions", self.text)
        self.assertIn("Authorization: Bearer $ACEDATACLOUD_API_TOKEN", self.text)
        self.assertIn("public alias `/v1/chat/completions`", self.text)

    def test_model_specific_reasoning_and_history_are_preserved(self):
        for requirement in (
            "`kimi-k3.1-pro` and `kimi-k3` remain available",
            "current public model catalog's `recommended` flag",
            "not a fixed model preference",
            "`low`, `high` and `max`",
            "Both K3.1 Pro and K3 always enable reasoning",
            "do not send settings to disable it",
            "For K3, use `max` or omit the field",
            "K2.6 uses `thinking`, not this effort control",
            "Preserve the complete assistant message",
            "`reasoning_content` and `tool_calls` when returned",
            "unchanged in subsequent turns and tool-result exchanges",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_context_pricing_and_protocols_are_not_overpromised(self):
        for requirement in (
            "access, pricing and **Allowed APIs** restrictions",
            "Do not silently replace an explicitly selected model",
            "`image_url` content blocks",
            "1,048,576 tokens, not a guaranteed per-request platform limit",
            "route's own model list before using Responses or Messages",
            "shared pricing rules do not establish protocol support",
            "Read actual `usage`", "input, output and cache-hit pricing",
            "Do not assume a cache hit",
            "`/aichat2/conversations` also lists `kimi-k3.1-pro`",
            "rather than assuming the Kimi-specific effort field is available",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)


class GeminiAudioProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("ai-chat").split("## Native Gemini Generate Content\n", 1)[1]
        cls.text = cls.text.split("## OpenAI Embeddings\n", 1)[0]

    def test_native_audio_example_uses_contents_and_file_data(self):
        example, = json_examples(self.text)
        self.assertEqual(set(example), {"contents", "generationConfig"})
        content, = example["contents"]
        self.assertEqual(content["role"], "user")
        prompt, audio = content["parts"]
        self.assertTrue(prompt["text"])
        self.assertEqual(audio, {"fileData": {"mimeType": "audio/wav", "fileUri": "HTTPS_AUDIO_URL"}})
        self.assertGreaterEqual(example["generationConfig"]["maxOutputTokens"], 512)
        for requirement in (
            "POST /v1beta/models/gemini-3.5-flash:generateContent",
            "POST /v1beta/models/{model}:streamGenerateContent?alt=sse",
            "same AceDataCloud Bearer token", "not OpenAI `messages`",
            "`inlineData` with `mimeType` and base64-encoded `data`",
            "HTTPS_AUDIO_URL", "actual audio MIME type",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertIn("native Gemini audio analysis", (ROOT / "README.md").read_text())

    def test_file_lifetime_timeout_and_model_support_boundaries(self):
        for requirement in (
            "directly accessible over HTTPS without login",
            "signed URL must remain valid for the entire request",
            "may exceed 90 seconds", "total request timeout",
            "file size and workload", "not a server processing limit",
            "do not automatically resubmit a potentially billable request",
            "Audio output", "`codeExecution`", "`googleSearch`", "`urlContext`", "`cachedContent`",
            "no uniform availability guarantee", "selected model's actual response",
            "not a promise of support on OpenAI-compatible or conversation routes",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn('"responseModalities": ["AUDIO"]', self.text)

    def test_summary_default_and_opt_in_are_separate_from_internal_thinking(self):
        example, = json_examples(self.text)
        config = example["generationConfig"]
        self.assertIs(config["thinkingConfig"]["includeThoughts"], False)
        self.assertNotIn("thinkingBudget", config["thinkingConfig"])
        self.assertIn("native Gemini audio analysis with opt-in thinking summaries", (ROOT / "README.md").read_text())
        for requirement in (
            "`generationConfig.thinkingConfig.includeThoughts` defaults to `false`",
            "Omit it or send boolean `false`", "`thought: true` text",
            "both JSON and SSE", "boolean `true`", "not guaranteed",
            "`thinkingBudget` or `thinkingLevel`", "model-dependent",
            "does not disable internal thinking or guarantee fewer thinking tokens",
            "Explicit summary, budget and level settings are preserved",
            "`gemini-2.5-flash-image`", "does not auto-add thinking configuration",
            "`countTokens` requests do not receive generation configuration",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_summary_filtering_preserves_complete_history_and_signature_positions(self):
        for requirement in (
            "Preserve returned `candidates[].content.parts` in order",
            "`thoughtSignature` is opaque multi-turn state, not summary text",
            "normal answers, function calls or empty-text Parts",
            "including signature-only or empty-text Parts and their other fields",
            "Do not move signatures, merge Parts or discard them because text is empty",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn('"thoughtSignature":', self.text)
        self.assertNotIn('"candidates":', self.text)

    def test_hidden_summaries_do_not_zero_usage_or_make_thinking_free(self):
        for requirement in (
            "Read actual `usageMetadata` and `usage`",
            "does not zero `thoughtsTokenCount`",
            "actual usage and current pricing", "Do not invent missing usage",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn('"usageMetadata":', self.text)
        self.assertNotIn('"usage":', self.text)


class GeminiArgonProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("ai-chat").split("## Gemini 4 Argon\n", 1)[1]
        cls.text = cls.text.split("## Native Gemini Generate Content\n", 1)[0]

    def test_chat_example_and_native_routes_keep_protocol_fields_separate(self):
        example, = json_examples(self.text)
        self.assertEqual(set(example), {"model", "messages", "max_tokens"})
        self.assertEqual(example["model"], "gemini-4-argon")
        self.assertEqual(example["max_tokens"], 32768)
        message, = example["messages"]
        self.assertEqual(message["role"], "user")
        self.assertTrue(message["content"])
        for requirement in (
            "POST /gemini/chat/completions", "public alias `/v1/chat/completions`",
            "POST /v1beta/models/gemini-4-argon:generateContent",
            "POST /v1beta/models/gemini-4-argon:streamGenerateContent?alt=sse",
            "`contents` with `parts`, not `messages`", "`stream: true`",
            "Gemini access, current pricing", "**Allowed APIs**",
            "`/aichat2/conversations` also lists `gemini-4-argon`",
            "not Chat or native Gemini request fields",
            "Do not infer Responses, Messages or legacy conversation support",
            "do not provide Google Interactions background long-output or server-side session features",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_budget_cache_and_pricing_are_model_specific(self):
        for requirement in (
            "Thinking and visible text share the output budget",
            "Chat `max_tokens` or native `generationConfig.maxOutputTokens`",
            "32,768 output tokens, not a required platform minimum",
            "1,048,576 tokens across input, thinking and output",
            "synchronous output cap of 65,536",
            "not guaranteed client/platform limits", "sufficient client timeout",
            "Argon ignores them", "`temperature`", "`top_p`", "`top_k`", "`topP`/`topK`",
            "implicit caching only", "do not create or reference explicit cache resources",
            "or send native `cachedContent`", "rather than assuming a cache hit or discount",
            "promotional through November 30, 2026", "from December 1, 2026",
            "it is not the account's charge",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_response_handling_uses_actual_protocol_fields(self):
        for field in (
            "choices[].message.content", "choices[].finish_reason", "choices[].delta.content",
            "candidates[].content.parts", "candidates[].finishReason",
            "usageMetadata", "thoughtsTokenCount", "cachedContentTokenCount",
        ):
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", self.text)
        self.assertIn("Never fabricate missing usage or response fields", self.text)
        self.assertNotIn('"usageMetadata":', self.text)
        self.assertNotIn('"choices":', self.text)


class ChatGatewayProcedureTests(unittest.TestCase):
    def test_opus_chat_constraints_and_public_alias_are_preserved(self):
        text = read_skill("ai-chat")
        opus = next(line for line in text.splitlines() if line.startswith("`claude-opus-5-5` is available"))
        for requirement in (
            "Ordinary and streaming Chat Completions are supported",
            "Chat replies do not return native thinking blocks",
            "use `n=1`", "omit non-default `temperature` and `top_p`",
            'use `tool_choice: "auto"` rather than forcing a tool',
            "`claude-sonnet-5-5` remains a Messages model",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, opus)
        self.assertIn("`POST /v1/chat/completions` (alias `/claude/chat/completions`)", text)
        self.assertIn("`POST /gemini/chat/completions` (public alias `/v1/chat/completions`)", text)

    def test_protocol_billing_distinguishes_inclusive_and_separate_cache_usage(self):
        text = read_skill("ai-chat").split("## Token billing across compatible protocols\n", 1)[1]
        text = text.split("## OpenAI-Compatible Chat\n", 1)[0]
        rows = {line.split("|")[1].strip(): line for line in text.splitlines() if line.lstrip().startswith("| ")}
        for protocol, total, cache in (
            ("Chat Completions", "usage.prompt_tokens", "usage.prompt_tokens_details.cached_tokens"),
            ("Responses", "usage.input_tokens", "usage.input_tokens_details"),
        ):
            with self.subTest(protocol=protocol):
                self.assertIn(f"`{total}` includes reported cache tokens", rows[protocol])
                self.assertIn(f"`{cache}`", rows[protocol])
                self.assertIn("subset, not extra input", rows[protocol])
                self.assertIn("corresponding cache price", rows[protocol])
        messages = rows["Messages"]
        for requirement in (
            "`usage.input_tokens` excludes", "`usage.cache_read_input_tokens`",
            "`usage.cache_creation_input_tokens`", "dimensions separately",
            "`usage.cache_creation`", "5-minute/1-hour details",
            "do not add them again to the creation total",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, messages)
        for requirement in (
            "model's actual input, output and cache usage",
            "does not turn token billing into a fixed per-request fee",
            "console's current model prices", "returned `usage.cost`",
            "Report only returned usage/cost fields",
            "not evidence of a cache hit or a free request",
            "Do not invent a charge from a reference USD price",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```", text)

    def test_cross_protocol_pricing_is_not_a_route_publication_grant(self):
        text = read_skill("ai-chat")
        for requirement in (
            "`claude-opus-5-5` is available on Claude Chat Completions",
            "Messages remains the recommended route for complete thinking blocks",
            "Check the current public model list and account access",
            "cross-protocol pricing rules do not establish identical feature support",
            "A settlement rule is not a publication or access grant",
            "do not silently substitute another model or route after an error",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("Messages only", text)
        self.assertNotIn("Messages-only", text)
        self.assertNotIn("available only through the dedicated Claude Messages API", text)

    def test_recommendations_are_live_editorial_preferences_not_access_grants(self):
        text = read_skill("ai-chat")
        for requirement in (
            "GET https://platform.acedata.cloud/api/v1/models/",
            "prefer suitable entries with `recommended=true`",
            "editorial preference, not an access grant or a new API capability",
            "`recommended=false` does not retire a model",
            "supported route and current pricing",
            "do not silently replace a model the user explicitly selected",
        ):
            self.assertIn(requirement, text)

    def test_public_model_selection_and_pricing_boundary(self):
        text = read_skill("ai-chat")
        for requirement in (
            "`gpt-5.6-sol-fast`",
            "exact public model ID on Chat Completions, Responses, Messages",
            "either conversation endpoint",
            "no public model introduction",
            "catalog visibility does not guarantee access",
            "total input exceeds 272,000 (not at exactly 272,000)",
            "input totals already include reported cache tokens",
            "for Messages, add the separately reported cache-read and cache-creation tokens",
            "to uncached input before checking this threshold",
            "Do not silently substitute `gpt-5.6-sol`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_aliases_and_dify_append_only_the_endpoint_suffix(self):
        text = read_skill("ai-chat")
        for route in ("/v1/chat/completions", "/v1/responses", "/v1/embeddings"):
            with self.subTest(route=route):
                self.assertIn(f"public alias `{route}`", text)
        dify = text.split("### Dify: OpenAI-API-compatible provider\n", 1)[1].split("## Currently Documented Model Families\n", 1)[0]
        for requirement in (
            "**Base URL** to `https://api.acedata.cloud/v1`",
            "**model** to `gpt-5.5`",
            "**conversation type** Chat",
            "**API type** Chat Completions",
            "Dify appends `/chat/completions` itself",
            "do not use `/openai/v1`",
            "Test the connection",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, dify)
        self.assertIn('base_url="https://api.acedata.cloud/openai"', text)
        self.assertNotIn("not `/v1/*`", text)


class KlingReferenceBillingProcedureTests(unittest.TestCase):
    def test_reference_example_disables_audio_and_retains_public_model(self):
        text = read_skill("kling-video")
        reference, = (example for example in json_examples(text) if "video_list" in example)
        self.assertEqual(reference["model"], "kling-o1")
        self.assertEqual(reference["duration"], 5)
        self.assertIs(reference["generate_audio"], False)
        self.assertEqual(reference["video_list"][0]["refer_type"], "base")
        self.assertIn("<<<video_1>>>", reference["prompt"])
        self.assertNotIn("reference_video_seconds", reference)

    def test_billing_distinguishes_video_inputs_and_final_duration(self):
        text = read_skill("kling-video").split("#### Reference-video billing\n", 1)[1]
        text = text.split("### 4. Extend Video", 1)[0]
        for requirement in (
            "current price", "`kling-o1` and `kling-v3-omni`",
            "`video_list` supplies a video",
            "`image_list`, first frames and end frames alone do not trigger it",
            "`generate_audio=false`", "successful reference-video requests",
            "1.202 Credits per billed second", "1.602 Credits per billed second",
            "| std | 4.005 Credits | 6.010 Credits |",
            "| pro | 5.340 Credits | 8.010 Credits |",
            "`refer_type=base`", "actual output duration rounded to integer seconds",
            "5.708s bills as 6s", "5.041s as 5s",
            "`refer_type=feature`", "requested `duration`",
            "Poll the same task to completion", "`usage.reference_video_seconds`",
            "submission estimate may differ from the final charge",
            "Report only usage actually returned",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```", text)


class PlatformConfigProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("acedatacloud").split("#### Platform runtime config\n", 1)[1]
        cls.text = cls.text.split("#### Regional catalog discovery\n", 1)[0]

    def test_public_config_uses_ip_region_without_query_overrides(self):
        for requirement in (
            "GET https://platform.acedata.cloud/api/v1/config/",
            "`features` and `region`", "No token is required",
            "Read `region`, not `country`", "lowercase country/region code",
            "detected from the request IP, or `null` when unknown",
            "accepts no region override",
            "do not send `country` or `region` query parameters",
            "frontend region selection stays local",
            "does not override catalog visibility, access or server-side security",
            "CLI has no config command",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        command, = re.findall(r"```bash\n(.*?)\n```", self.text, re.DOTALL)
        self.assertIn("curl --get https://platform.acedata.cloud/api/v1/config/", command)
        self.assertNotIn("?", command)
        self.assertNotIn("--data", command)
        self.assertNotIn("Authorization", command)

    def test_flags_do_not_grant_access_or_supply_unrelated_metadata(self):
        for requirement in (
            "safe defaults for missing keys",
            "do not share a long-lived config cache across users",
            "`features` query or `X-Feature-Overrides` header",
            "only to client-overridable flags or superusers",
            "not an access bypass",
            "not a source for branding, CDN, currency, language, support contacts or announcements",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)


class RegionalCatalogProcedureTests(unittest.TestCase):
    def test_account_procedure_uses_public_fields_and_preserves_mixed_media(self):
        text = read_skill("acedatacloud").split("#### Regional catalog discovery\n", 1)[1]
        text = text.split("### Dataset reference pricing\n", 1)[0]
        for requirement in (
            "get-service --service <alias-or-uuid> --json",
            "`available_regions`, `unavailable_regions`",
            "chat-only `chat_unavailable_regions`", "image-only `image_unavailable_regions`",
            "apis --service <alias-or-uuid> --json", "docs-list --json",
            "doc --id <document-uuid> --json",
            "`pricing` and `spec` summaries omit these fields",
            "Empty region lists mean no explicit regional rule, not an access grant",
            "requesting visitor's IP", "not the display language or a `?country=` override",
            "Claude services and chat APIs/documents",
            "OpenAI, Gemini and Grok", "media visibility must be checked separately",
            "OpenAI image generation/editing and companion guides are also hidden in mainland China",
            "Do not hide the entire service based on `chat_unavailable_regions` or `image_unavailable_regions`",
            "unrelated media entries retain their own rules",
            "Raw REST/CLI results may still include marked rows",
            "apply their region metadata when presenting choices",
            "missing entry/404 as proof of retirement or revoked API access",
            "does not change API routing or billing",
            "check actual account access, key restrictions and current pricing separately",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertIn("region-aware public catalog discovery", (ROOT / "README.md").read_text())

    def test_chat_discovery_does_not_advertise_hidden_entries_or_revoke_access(self):
        text = read_skill("ai-chat")
        for requirement in (
            "requesting visitor's IP", "not the display language or a `?country=` override",
            "Mainland-China views hide marked Claude, OpenAI, Gemini and Grok chat",
            "Check media visibility separately",
            "OpenAI image generation/editing and companion guides are also hidden in mainland China",
            "`image_unavailable_regions` and API/document `unavailable_regions`",
            "do not hide unrelated media or the entire mixed service",
            "presence alone is not visibility",
            "do not use a cached global list to advertise region-hidden chat",
            "missing catalog entry is not evidence of retirement or revoked API access",
            "does not change API routing or billing",
            "Report the discovery limitation", "check actual account access and pricing",
            "do not silently replace a user-selected model",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_existing_cli_preserves_public_region_fields_without_client_side_hiding(self):
        script = ROOT / "skills" / "acedatacloud" / "scripts" / "acedatacloud.py"
        spec = importlib.util.spec_from_file_location("acedatacloud_region_skill", script)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        row_id = "00000000-0000-4000-8000-000000000001"
        regions = {"available_regions": [], "unavailable_regions": ["cn"]}
        service = {"id": row_id, "alias": "test-mixed", "available_regions": [],
                   "unavailable_regions": [], "chat_unavailable_regions": ["cn"],
                   "image_unavailable_regions": ["cn"]}
        api = {"id": row_id, "service_id": row_id, "path": "/openai/images/generations", **regions}
        document = {"id": row_id, "alias": "openai-images-generations-integration", **regions}
        for command, item, path, single in (
            (["get-service", "--service", row_id], service, "/services/", True),
            (["apis"], api, "/apis/", False),
            (["docs-list"], document, "/documents/", False),
            (["doc", "--id", row_id], document, "/documents/", True),
        ):
            with self.subTest(command=command):
                payload = {"count": 1, "items": [item]}
                output = io.StringIO()
                with patch.object(cli.sys, "argv", ["acedatacloud.py", *command, "--json"]), patch.object(
                    cli, "_request", return_value=(200, payload)
                ) as request, redirect_stdout(output):
                    cli.main()
                request.assert_called_once()
                self.assertEqual(request.call_args.args[1:3], ("GET", path))
                self.assertEqual(request.call_args.kwargs, {"auth_required": False})
                result = json.loads(output.getvalue())
                self.assertEqual(result if single else result["items"][0], item)


class AgentTaskProcedureTests(unittest.TestCase):
    def test_turn_limit_is_per_request_not_history(self):
        text = read_skill("ai-chat")
        for requirement in (
            "Agent iterations per request: 1–500, default 500",
            "not retained history",
            "Each iteration is a model call",
            "`max_turns: 1` requests a single answer without tool calls",
            "not a guarantee that all will run",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("Trim retained turn history", text)

    def test_scheduled_examples_use_action_payloads_and_bounded_template(self):
        text = read_skill("ai-chat").split("## Scheduled Agent Tasks\n", 1)[1].split("## Gotchas\n", 1)[0]
        examples = {example["action"]: example for example in json_examples(text)}
        self.assertEqual(set(examples), {"create", "retrieve_batch", "retrieve_runs", "update", "trigger_selected"})
        create = examples["create"]
        self.assertEqual(create["schedule"], {"type": "cron", "cron": "0 9 * * *", "tz": "UTC"})
        self.assertGreaterEqual(create["template"]["max_turns"], 1)
        self.assertLessEqual(create["template"]["max_turns"], 500)
        self.assertNotIn("max_turns", create)
        self.assertIn("Do not publish or send messages", create["template"]["question"])
        self.assertEqual(examples["retrieve_runs"]["id"], "TASK_ID")
        self.assertEqual(examples["update"], {"action": "update", "id": "TASK_ID", "state": "disabled"})
        for requirement in (
            "same service Bearer token",
            "not a platform-management-token endpoint",
            "`template.max_turns` is 1–500, default 500",
            "not schedule frequency",
            "preview locally and obtain confirmation",
            "scheduling is not blanket permission",
            "three months after creation",
            "at most 15 minutes",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_scheduled_timing_controls_preserve_zero_and_per_account_sampling(self):
        text = read_skill("ai-chat").split("### Timing jitter and trigger probability\n", 1)[1]
        text = text.split("### Account-bound cloud runs\n", 1)[0]
        for requirement in (
            "preserve explicit zero values", "request's top level",
            "not inside `schedule` or `template`", "Nonnegative integer seconds",
            "default `60`", "`0` disables jitter", "before or after",
            "one quarter of `interval_seconds`", "Local runs do not use jitter",
            "Number from `0` to `1`, default `1`", "older tasks without this field",
            "`0` skips every automatic attempt", "`1` starts every automatic attempt",
            "Each account is sampled independently when due, independently of jitter",
            "not a fixed quota of accounts per cycle",
            "only to automatic cloud and local scheduled attempts",
            "not **Run now** or other manual runs", "before conversation creation, model calls and billing",
            '`status="skipped"`', '`error_code="probability_skipped"`',
            "creates no conversation", "incurs no model charge", "does not pause the task",
            "Repeated callbacks reuse the saved sampling result",
            "Changing probability does not reset the next planned execution time",
            "Manual runs bypass probability even when the saved value is `0`",
            "confirm their accounts and spending scope before triggering",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("```", text)

    def test_account_binding_update_uses_top_level_controls_and_real_id_placeholders(self):
        text = read_skill("ai-chat").split("### Account-bound cloud runs\n", 1)[1]
        text = text.split("### Manually trigger selected accounts\n", 1)[0]
        example, = json_examples(text)
        self.assertEqual(set(example), {
            "action", "id", "jitter_seconds", "trigger_probability", "unattended_policy",
        })
        self.assertEqual(example["action"], "update")
        self.assertEqual(example["id"], "TASK_ID")
        self.assertEqual(example["jitter_seconds"], 0)
        self.assertEqual(example["trigger_probability"], 1)
        policy = example["unattended_policy"]
        self.assertEqual(policy["allowed_skills"], ["github"])
        self.assertEqual(policy["connection_bindings"], [
            {"connector_identifier": "github/github", "connection_id": "CONNECTED_ACCOUNT_ONE_ID"},
            {"connector_identifier": "github/github", "connection_id": "CONNECTED_ACCOUNT_TWO_ID"},
        ])
        for requirement in (
            "preview this update and obtain confirmation", "confirmed read-only task",
            "per-account spending scope", "top-level `unattended_policy.connection_bindings`",
            "other connectors must each use one account", "at most 100 bindings total",
            "Local execution still permits only one account per connector",
            "actual connected account IDs", "never guess IDs or copy credentials",
            "independently authorized, billed run and its own conversation",
            "one account's failure does not block the others",
            "Zero jitter does not guarantee simultaneous starts",
            "next execution time is the earliest across accounts",
            "Changing account selections reschedules runs",
            "changing the prompt does not reset execution times",
            "Pause, resume and delete affect all accounts", "already-started runs may finish",
            "does not merge old task copies", "explicitly pause duplicates",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_selected_trigger_example_is_a_subset_of_saved_bindings_without_updates(self):
        text = read_skill("ai-chat").split("## Scheduled Agent Tasks\n", 1)[1].split("## Gotchas\n", 1)[0]
        examples = list(json_examples(text))
        binding_update = next(body for body in examples if "unattended_policy" in body)
        trigger = next(body for body in examples if body["action"] == "trigger_selected")
        self.assertEqual(trigger, {
            "action": "trigger_selected", "id": "TASK_ID",
            "connection_ids": ["CONNECTED_ACCOUNT_ONE_ID"],
        })
        saved_ids = {binding["connection_id"] for binding in binding_update["unattended_policy"]["connection_bindings"]}
        self.assertLess(set(trigger["connection_ids"]), saved_ids)
        self.assertEqual(len(trigger["connection_ids"]), len(set(trigger["connection_ids"])))
        for requirement in (
            "current saved bindings", "exact accounts and billable scope for this invocation",
            "nothing selected by default", "choose one or more accounts or explicitly select all",
            "Single-account tasks trigger directly", "required `connection_ids`",
            "nonempty array of unique IDs", "saved multi-account connector only",
            "Other connectors' fixed accounts remain attached to each run",
            "Unknown, removed or out-of-scope IDs reject the entire request without starting any runs",
            "Do not update saved bindings just to run a subset",
            "obtain confirmation before sending", 'Legacy `action="trigger"` without an account list',
            "all configured accounts", "only when that full scope is confirmed",
            "If an older service rejects `trigger_selected`, surface the error",
            "never fall back to `trigger` or all accounts",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_manual_runs_bypass_sampling_and_jitter_without_changing_saved_schedule(self):
        text = read_skill("ai-chat").split("### Manually trigger selected accounts\n", 1)[1]
        text = text.split("### Search and page through scheduled tasks\n", 1)[0]
        for requirement in (
            "Manual runs bypass `jitter_seconds` and `trigger_probability`",
            "including a saved probability of `0`", "without waiting for the previous account to finish",
            "unselected accounts get no run records", "single-account **Run now**",
            '`action="trigger"` and local manual runs',
            "Saved account bindings, trigger probability and the next scheduled execution remain unchanged",
            "authorization checks and normal billing still apply",
            "records its effective `trigger_probability` as `1`",
            "without rewriting task configuration or historical records",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        for obsolete in ("all attempts skip", "when started, `conversation_id`", "retrying **Run now** to force a start"):
            self.assertNotIn(obsolete, read_skill("ai-chat"))

    def test_multi_account_results_require_completion_and_preserve_account_snapshots(self):
        text = read_skill("ai-chat").split("### Account-bound cloud runs\n", 1)[1]
        text = text.split("### Search and page through scheduled tasks\n", 1)[0]
        for requirement in (
            "On successful cloud acceptance", "every returned `runs[]` entry's `run_id`",
            '`status="queued"` and `conversation_id`',
            "`triggered_count` is the number of accounts started",
            "compatibility `skipped_count` is always `0`",
            "Top-level compatibility fields point to the first started run",
            "Queued acceptance is not successful completion",
            "check final results before reporting success or considering another billable trigger",
            "opens the conversation for one started account and task run history for multiple accounts",
            "`run_accounts` snapshots the accounts actually selected",
            "later binding changes do not rewrite it", "Older/default-account runs may omit it",
            "expires, is revoked or deleted", "do not substitute the connector's default account",
            "reauthorize the intended account before resuming",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        for fabricated_response in ('"runs":', '"conversation_id":', '"triggered_count":'):
            self.assertNotIn(fabricated_response, text)
        self.assertIn("selected-account manual runs", (ROOT / "README.md").read_text())

    def test_scheduled_search_is_owner_scoped_before_pagination(self):
        text = read_skill("ai-chat").split("### Search and page through scheduled tasks\n", 1)[1]
        text = text.split("Creation payload", 1)[0]
        example, = json_examples(text)
        self.assertEqual(example, {"action": "retrieve_batch", "search": "Daily", "offset": 0, "limit": 10})
        for requirement in (
            "all tasks owned by the current user, before pagination",
            "case-insensitive substring", "surrounding whitespace ignored",
            "not a regular expression", "Omitted or empty `search` lists all tasks",
            "newest-created first", "`items` for the page and `count` for the total",
            "`offset` defaults to 0", "`limit` defaults to 100 and must be 1–100",
            "Keep `search` unchanged", "increase `offset` by `limit`",
            "accumulated items reach `count`", "do not search only the currently loaded page",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn('"items":', text)

    def test_run_failure_and_handoff_failure_are_distinct(self):
        text = read_skill("ai-chat")
        for requirement in (
            "not evidence of a successful run",
            "AI execution failures **do not auto-pause**",
            "five consecutive handoff failures",
            "not five failed AI runs",
            "`status`, `error_code` and `conversation_id`",
            "`awaiting_user_input`",
            "explicitly pause recurring failures",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("/internal/scheduled-task", text)
        self.assertIn("scheduled agent tasks", (ROOT / "README.md").read_text())


class EmbeddingsProcedureTests(unittest.TestCase):
    def test_example_uses_current_model_and_preserves_migration_boundary(self):
        text = read_skill("ai-chat")
        embeddings = text.split("## OpenAI Embeddings\n", 1)[1].split("## Native Claude Messages\n", 1)[0]
        example, = json_examples(embeddings)
        self.assertEqual(example["model"], "text-embedding-3-small")
        self.assertEqual(example["input"], "Hello!")
        self.assertIn("text-embedding-3-large", embeddings)
        for requirement in (
            "POST /openai/embeddings",
            "public alias `/v1/embeddings`",
            "`text-embedding-ada-002` is retired",
            "Rebuild existing indexes",
            "do not mix vectors from different models",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, embeddings)


class DatasetReferencePricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = ROOT / "skills" / "acedatacloud" / "scripts" / "acedatacloud.py"
        spec = importlib.util.spec_from_file_location("acedatacloud_skill", script)
        cls.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cli)

    def pricing(self, service, json_output=True):
        argv = ["acedatacloud.py", "pricing", "--service", service["id"]]
        if json_output:
            argv.append("--json")
        output = io.StringIO()
        with patch.object(self.cli.sys, "argv", argv), patch.object(
            self.cli, "_request", return_value=(200, {"count": 1, "items": [service]})
        ) as request, redirect_stdout(output):
            self.cli.main()
        request.assert_called_once()
        self.assertEqual(request.call_args.args[1:], ("GET", "/services/", {"id": service["id"]}))
        self.assertEqual(request.call_args.kwargs, {"auth_required": False})
        return json.loads(output.getvalue())

    def test_reference_quote_keeps_currency_range_unit_and_status(self):
        for service_id, alias, minimum, maximum, unit in (
            ("b673f806-cf79-544f-8ab9-544445d11252", "hacker-news", 8800, 8800, "full_package"),
            ("30d64398-9368-46f2-8377-1416c9fc0cbc", "youtube-video", 249, 329, "tb"),
        ):
            quote = {"currency": "CNY", "min_amount": minimum, "max_amount": maximum,
                     "unit": unit, "status": "reference"}
            service = {"id": service_id, "alias": alias, "type": "Dataset",
                       "metadata": {"pricing_mode": "contact_only", "reference_quote": quote},
                       "packages": []}
            for json_output in (False, True):
                with self.subTest(alias=alias, json_output=json_output):
                    result = self.pricing(service, json_output)
                    self.assertEqual(result["pricing_mode"], "contact_only")
                    self.assertEqual(result["reference_quote"], quote)
                    self.assertIsNone(result["cost"])
                    self.assertNotIn("packages", result)

    def test_missing_quote_does_not_invent_a_price(self):
        for metadata in (None, {}, {"pricing_mode": "contact_only"},
                         {"pricing_mode": "contact_only", "reference_quote": None}):
            with self.subTest(metadata=metadata):
                result = self.pricing({"id": "b673f806-cf79-544f-8ab9-544445d11252",
                                       "type": "Dataset", "metadata": metadata})
                self.assertNotIn("reference_quote", result)
                self.assertIsNone(result["cost"])
                if metadata and "pricing_mode" in metadata:
                    self.assertEqual(result["pricing_mode"], "contact_only")

    def test_pricing_omits_unrelated_metadata(self):
        quote = {"currency": "CNY", "min_amount": 8800, "max_amount": 8800,
                 "unit": "full_package", "status": "reference"}
        result = self.pricing({
            "id": "b673f806-cf79-544f-8ab9-544445d11252", "type": "Dataset",
            "metadata": {"pricing_mode": "contact_only", "procurement_cost": 1,
                         "reference_quote": {**quote, "internal_note": "not public pricing"}},
        })
        self.assertEqual(result["reference_quote"], quote)
        self.assertNotIn("procurement_cost", result)
        self.assertNotIn("metadata", result)

    def test_api_pricing_output_is_unchanged(self):
        service = {"id": "b673f806-cf79-544f-8ab9-544445d11252", "alias": "test-api",
                   "title": "Test API", "type": "Api", "unit": "Credit", "free_amount": 10,
                   "cost": {"amount": 1}, "metadata": {"reference_quote": {"currency": "CNY"}}}
        self.assertEqual(self.pricing(service), {key: service[key] for key in (
            "alias", "title", "type", "unit", "free_amount", "cost"
        )} | {"service_id": service["id"]})

    def test_skill_explains_reference_only_purchase_boundary(self):
        text = read_skill("acedatacloud").split("### Dataset reference pricing\n", 1)[1]
        text = text.split("### Announcements", 1)[0]
        for requirement in (
            "pricing --service <alias-or-uuid> --json",
            "metadata.reference_quote", 'pricing_mode="contact_only"', 'status="reference"',
            "yuan, not Credits or USD", "per TB", "full package", "Equal bounds",
            "invent a quote", "does not create a purchase Package",
            "license and final price with support", "do not call `create-order` or `pay-order`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)


class BlogReviewProcedureTests(unittest.TestCase):
    def test_peer_review_and_write_safety(self):
        text = read_skill("acedatacloud")
        blog = text.split("### Blog drafts, review submission and publication (MCP / REST)\n", 1)[1].split("## Write-operation safety\n", 1)[0]
        for tool in (
            "acedatacloud_create_blog_draft",
            "acedatacloud_get_blog_draft",
            "acedatacloud_approve_blog_post",
            "acedatacloud_withdraw_blog_approval",
            "acedatacloud_publish_blog_post",
            "acedatacloud_unpublish_blog_post",
        ):
            with self.subTest(tool=tool):
                self.assertIn(tool, blog)
        for requirement in (
            "`blog:read` + `blog:publish`",
            "`blog:write` + `blog:publish`",
            "creator cannot approve their own draft",
            "publisher must not be the reviewer",
            "current `review_version`",
            "409",
            "reread the full draft",
            "invalidate approval",
            "Unpublish before editing",
            "`confirm=true`",
            "does not implement blog commands",
            "timezone-aware `publish_at`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, blog)

    def test_submission_rejection_and_pending_edit_boundaries(self):
        text = read_skill("acedatacloud")
        for requirement in (
            "current `review_version` and `review_status`",
            "Submit a `draft` or `rejected` article",
            "POST /api/v1/blogs/admin/{id}/submit/",
            '{"expected_version": CURRENT_REVIEW_VERSION}',
            'verify `review_status="pending"`',
            "Pending articles cannot be edited",
            "`DELETE` to the same `/submit/` route",
            "Withdrawal of a pending review is distinct",
            "POST /api/v1/blogs/admin/{id}/approval/",
            "POST /api/v1/blogs/admin/{id}/reject/",
            "nonblank `comment` (at most 2,000 characters)",
            'verify `review_status="rejected"`',
            "Read `review_comment`, revise and resubmit",
            'Only after `review_status="approved"`',
            "409 on submission, withdrawal, approval or rejection",
            "REST review routes above execute immediately and have no dry-run flag",
            "obtain confirmation before sending",
            "do not invent submission/rejection tool names or CLI flags",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("acedatacloud_submit_blog", text)
        self.assertNotIn("acedatacloud_reject_blog", text)

    def test_video_drafts_keep_validation_and_review_boundaries(self):
        text = read_skill("acedatacloud")
        for requirement in (
            'Default `content_type="article"` requires a nonblank body and clears `video_url`',
            'For `content_type="video"`',
            "actual HTTPS `video_url`",
            "body may be blank, but title and summary remain required",
            "Never fabricate a media URL",
            "nonblank `cover_alt`",
            "MCP schema lacks video fields",
            "POST /api/v1/blogs/admin/",
            "PATCH /api/v1/blogs/admin/{id}/",
            "watch the actual video",
            "`content_type` or `video_url`) invalidate approval",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertIn("article/video drafts and review threads", (ROOT / "README.md").read_text())

    def test_private_threads_use_saved_utf16_anchors_and_root_ids(self):
        text = read_skill("acedatacloud")
        threads = text.split("#### Review threads (authenticated REST)\n", 1)[1].split("All blog writes", 1)[0]
        for requirement in (
            "private editorial feedback, not public blog comments",
            "platform Bearer token",
            "`blog:read` plus either `blog:write` or `blog:publish`",
            "GET /api/v1/blogs/admin/{id}/comments/",
            "POST /api/v1/blogs/admin/{id}/comments/",
            "current `expected_version`",
            'field="overall"` with no offsets or quote',
            'field="title"`, `"summary"` or `"content"`',
            "**UTF-16 code units**",
            "not Python characters or UTF-8 bytes",
            "start is inclusive, end exclusive",
            "at most 2,000 code units",
            "Never anchor to unsaved text",
            "On 409, refresh the draft and recompute",
            "POST /api/v1/blogs/admin/{id}/comments/{comment_id}/replies/",
            "root ID, not a reply ID",
            "replying to a resolved thread reopens it",
            "PATCH /api/v1/blogs/admin/{id}/comments/{comment_id}/",
            '{"resolved":true}',
            '{"resolved":false}',
            "resolution do not require `expected_version`",
            "does not approve or publish",
            "After preview and confirmation",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, threads)

    def test_rejection_can_use_only_current_unresolved_root_feedback(self):
        text = read_skill("acedatacloud")
        self.assertIn("omit `comment` if an unresolved root review thread already exists on the current version", text)
        self.assertIn("Read `review_comment`, revise and resubmit", text)
        self.assertIn("historical feedback does not prove a selection still matches", text)

    def test_current_editorial_categories_and_catalog(self):
        text = read_skill("acedatacloud")
        for category in (
            "product-updates", "tech-sharing", "product-recommendations", "industry-insights",
        ):
            self.assertIn(f"`{category}`", text)
        readme = (ROOT / "README.md").read_text()
        self.assertIn("submitted, peer-reviewed blog publishing via MCP / REST", readme)
        self.assertIn("embeddings", readme)


class MiniMaxPollingProcedureTests(unittest.TestCase):
    def test_success_failure_and_batch_paths(self):
        text = read_skill("minimax-video")
        for requirement in (
            "`queued` or `running`",
            'Only `task.status="succeeded"` is success',
            "`task.content.url`",
            "`failed` or `cancelled`",
            "`task.error.code` / `task.error.message`",
            "never report a URL as final before success",
            "inspect each item in `items` independently",
            "not to cancel generation",
            "mcp-minimax",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)


class HostedMCPSetupTests(unittest.TestCase):
    def test_client_examples_use_environment_token_not_literal_secret(self):
        text = (ROOT / "skills" / "_shared" / "mcp-servers.md").read_text()
        claude, amp = list(json_examples(text))
        for config, key in ((claude, "mcpServers"), (amp, "amp.mcpServers")):
            self.assertEqual(
                config[key]["suno"]["headers"]["Authorization"],
                "Bearer ${ACEDATACLOUD_API_TOKEN}",
            )
        self.assertEqual(claude["mcpServers"]["suno"]["type"], "http")
        for requirement in (
            "do not replace other services",
            "start the client from that same terminal",
            "saving configuration alone is not proof",
            "amp mcp doctor",
            "amp mcp approve suno",
        ):
            self.assertIn(requirement, text)

    def test_catalog_matches_updated_procedures(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("edit/render versioned multitrack Studio projects", readme)
        self.assertIn("native Claude Messages", readme)
        self.assertIn("Generate MiniMax-H3 videos (768P/2K)", readme)
        config, = json_examples(readme)
        self.assertEqual(
            config["mcpServers"]["suno"]["headers"]["Authorization"],
            "Bearer ${ACEDATACLOUD_API_TOKEN}",
        )


if __name__ == "__main__":
    unittest.main()

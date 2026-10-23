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


class ChatGatewayProcedureTests(unittest.TestCase):
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
            "`prompt_tokens` exceeds 272,000 (not at exactly 272,000)",
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


class RegionalCatalogProcedureTests(unittest.TestCase):
    def test_account_procedure_uses_public_fields_and_preserves_mixed_media(self):
        text = read_skill("acedatacloud").split("#### Regional catalog discovery\n", 1)[1]
        text = text.split("### Dataset reference pricing\n", 1)[0]
        for requirement in (
            "get-service --service <alias-or-uuid> --json",
            "`available_regions`, `unavailable_regions`",
            "chat-only `chat_unavailable_regions`",
            "apis --service <alias-or-uuid> --json", "docs-list --json",
            "doc --id <document-uuid> --json",
            "`pricing` and `spec` summaries omit these fields",
            "Empty region lists mean no explicit regional rule, not an access grant",
            "requesting visitor's IP", "not the display language or a `?country=` override",
            "Claude services and chat APIs/documents",
            "OpenAI, Gemini and Grok", "keep media entries",
            "do not hide the entire service based on `chat_unavailable_regions`",
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
            "mixed OpenAI/Gemini/Grok services keep their media entries",
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
                   "unavailable_regions": [], "chat_unavailable_regions": ["cn"]}
        api = {"id": row_id, "service_id": row_id, "path": "/test/chat", **regions}
        document = {"id": row_id, "alias": "test-chat-guide", **regions}
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
        self.assertEqual(set(examples), {"create", "retrieve_runs", "update"})
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

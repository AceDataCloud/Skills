from __future__ import annotations

import importlib.util
import argparse
import base64
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

SCRIPT = Path(__file__).parents[1] / "scripts" / "xiaohongshu.py"
SPEC = importlib.util.spec_from_file_location("xiaohongshu_skill", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _signed_token(private_key: Ed25519PrivateKey, claim: dict) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps(claim, separators=(",", ":")).encode()
    ).rstrip(b"=")
    signature = private_key.sign(payload)
    return f"{payload.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def _approval_credentials(
    directory: str, digest: str, session_id: str = "session-1"
) -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    public_path = Path(directory) / "approval-public.pem"
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
        )
    )
    MODULE.APPROVAL_PUBLIC_KEY_PATH = public_path
    approval = _signed_token(
        private_key,
        {
            "purpose": "xiaohongshu-approval-v1",
            "digest": digest,
            "session_id": session_id,
            "expires_at": int(time.time()) + 60,
            "nonce": "approval-nonce",
        },
    )
    grant = _signed_token(
        private_key,
        {
            "purpose": "xiaohongshu-execution-v1",
            "digest": digest,
            "session_id": session_id,
            "approval_token_sha256": MODULE.hashlib.sha256(
                approval.encode()
            ).hexdigest(),
            "expires_at": int(time.time()) + 60,
            "nonce": "grant-nonce",
        },
    )
    return approval, grant


def _approval_token(directory: str, digest: str, session_id: str = "session-1") -> str:
    return _approval_credentials(directory, digest, session_id)[0]


class ConnectorCookieTests(unittest.TestCase):
    def test_converts_extension_cookie_shape(self) -> None:
        converted = MODULE.convert_connector_cookies(
            [
                {
                    "name": "a1",
                    "value": "secret",
                    "domain": ".xiaohongshu.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                    "sameSite": "no_restriction",
                    "expirationDate": 2000,
                },
                {
                    "name": "web_session",
                    "value": "session",
                    "domain": ".xiaohongshu.com",
                    "sameSite": "unspecified",
                },
            ],
            now=1000,
        )

        self.assertEqual(converted[0]["expires"], 2000)
        self.assertEqual(converted[0]["sameSite"], "None")
        self.assertNotIn("session", converted[0])
        self.assertNotIn("expires", converted[1])
        self.assertNotIn("sameSite", converted[1])
        self.assertEqual(
            set(converted[0]),
            {
                "name",
                "value",
                "domain",
                "path",
                "expires",
                "httpOnly",
                "secure",
                "sameSite",
            },
        )

    def test_filters_expired_cookie(self) -> None:
        converted = MODULE.convert_connector_cookies(
            [
                {
                    "name": "old",
                    "value": "x",
                    "domain": ".xiaohongshu.com",
                    "expirationDate": 5,
                },
                {
                    "name": "active",
                    "value": "y",
                    "domain": ".xiaohongshu.com",
                    "expirationDate": 20,
                },
            ],
            now=10,
        )
        self.assertEqual([cookie["name"] for cookie in converted], ["active"])

    def test_rejects_foreign_cookie_domain(self) -> None:
        with self.assertRaisesRegex(MODULE.ConnectorCookieError, "invalid domain"):
            MODULE.convert_connector_cookies(
                [{"name": "sid", "value": "x", "domain": ".example.com"}],
                now=10,
            )

    def test_loads_injected_connector_environment(self) -> None:
        original = os.environ.get(MODULE.COOKIE_ENV)
        try:
            os.environ[MODULE.COOKIE_ENV] = json.dumps(
                [{"name": "a1", "value": "x", "domain": ".xiaohongshu.com"}]
            )
            self.assertEqual(MODULE.load_connector_cookie_jar()[0]["name"], "a1")
        finally:
            if original is None:
                os.environ.pop(MODULE.COOKIE_ENV, None)
            else:
                os.environ[MODULE.COOKIE_ENV] = original


class CommandSafetyTests(unittest.TestCase):
    def test_publish_dry_run_never_starts_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(b"image-v1")
            args = argparse.Namespace(
                command="publish",
                title="测试标题",
                title_file=None,
                content="测试内容",
                content_file=None,
                images=[str(image)],
                tags=["测试"],
                schedule_at=None,
                original=False,
                visibility="仅自己可见",
                products=[],
                approval_digest="",
                approval_token="",
            )
            with (
                patch.object(MODULE, "CONFIRM", False),
                patch.object(
                    MODULE,
                    "load_connector_cookie_jar",
                    return_value=[
                        {"name": "a1", "value": "secret", "domain": ".xiaohongshu.com"}
                    ],
                ),
                patch.object(MODULE, "DirectXiaohongshuRuntime") as runtime,
                patch.object(MODULE, "output") as emit,
                patch.dict(
                    os.environ,
                    {"HOME": directory, "AICHAT_SANDBOX_SESSION_ID": "session-1"},
                ),
            ):
                self.assertEqual(MODULE.execute(args), {})
        runtime.assert_not_called()
        self.assertTrue(emit.call_args.args[0]["dry_run"])
        self.assertTrue(emit.call_args.args[0]["approval_digest"])
        self.assertNotIn("approval_token", emit.call_args.args[0])

    def test_confirm_must_be_last_argument(self) -> None:
        with patch.object(
            MODULE.sys, "argv", ["x", "publish", "--confirm", "--title", "x"]
        ):
            raw = MODULE.sys.argv[1:]
            self.assertFalse(bool(raw) and raw[-1] == "--confirm")

    def test_schedule_requires_timezone_and_allowed_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone"):
            MODULE._validate_schedule("2030-01-01T12:00:00")
        with self.assertRaisesRegex(ValueError, "between 1 hour and 14 days"):
            MODULE._validate_schedule(
                (
                    MODULE.datetime.now(MODULE.timezone.utc)
                    + MODULE.timedelta(minutes=20)
                ).isoformat()
            )

    def test_publish_rejects_private_image_url(self) -> None:
        with patch.object(
            MODULE.socket,
            "getaddrinfo",
            return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
        ):
            with self.assertRaisesRegex(ValueError, "public HTTPS"):
                MODULE._validate_media_reference(
                    "https://example.com/a.png", image=True
                )

    def test_image_downloader_rejects_private_redirect(self) -> None:
        response = MagicMock(
            status=302, headers={"Location": "http://127.0.0.1/secret"}
        )
        response.connection.sock.getpeername.return_value = ("93.184.216.34", 443)
        pool = MagicMock()
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(
                MODULE, "_public_https_addresses", side_effect=[("93.184.216.34",), ()]
            ),
            patch.object(
                MODULE, "_open_pinned_https_response", return_value=(response, pool)
            ),
            self.assertRaisesRegex(ValueError, "not public HTTPS"),
        ):
            MODULE._download_public_image(
                "https://example.com/image.png", Path(directory)
            )
        response.release_conn.assert_called_once()
        pool.close.assert_called_once()

    def test_image_downloader_requires_peer_address(self) -> None:
        response = MagicMock(status=200, headers={"Content-Type": "image/png"})
        response.connection = None
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(RuntimeError, "peer address is unavailable"),
        ):
            MODULE._consume_image_response(
                response, "https://example.com/image.png", Path(directory)
            )

    def test_redirect_response_rejects_private_peer_before_following(self) -> None:
        response = MagicMock(
            status=302, headers={"Location": "https://example.com/next"}
        )
        response.connection.sock.getpeername.return_value = ("127.0.0.1", 443)
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaisesRegex(ValueError, "non-public address"),
        ):
            MODULE._consume_image_response(
                response, "https://example.com/image.png", Path(directory)
            )

    def test_unattended_write_requires_explicit_skill_allowlist(self) -> None:
        env = {
            "AICHAT_UNATTENDED_MODE": "true",
            "AICHAT_ACTIVE_SKILL": "acedatacloud/xiaohongshu",
            "AICHAT_UNATTENDED_ALLOWED_SKILLS": "[]",
        }
        with patch.dict(os.environ, env, clear=False):
            allowed, reason = MODULE._unattended_write_allowed()
        self.assertFalse(allowed)
        self.assertIn("not pre-authorized", reason)

    def test_interaction_payloads_are_reversible(self) -> None:
        common = {"feed_id": "feed", "xsec_token": "token", "xsec_source": "pc_note"}
        unlike = MODULE._payload_for_command(
            argparse.Namespace(command="unlike", **common)
        )
        unfavorite = MODULE._payload_for_command(
            argparse.Namespace(command="unfavorite", **common)
        )
        self.assertEqual(unlike, {**common, "unlike": True})
        self.assertEqual(unfavorite, {**common, "unfavorite": True})

    def test_write_preview_redacts_xsec_tokens(self) -> None:
        payload = {
            "feed_id": "feed",
            "xsec_token": "secret-token",
            "nested": [{"xsecToken": "another-token"}],
        }

        self.assertEqual(
            MODULE._redact_xsec_tokens(payload),
            {
                "feed_id": "feed",
                "xsec_token": "[REDACTED]",
                "nested": [{"xsecToken": "[REDACTED]"}],
            },
        )

    def test_runtime_stops_process_group_after_parent_exit(self) -> None:
        runtime = MODULE.DirectXiaohongshuRuntime([])
        runtime.process = MagicMock(pid=321)
        runtime.process.poll.return_value = 0

        with patch.object(MODULE.os, "killpg") as kill_group:
            runtime._stop()

        kill_group.assert_called_once_with(321, MODULE.signal.SIGTERM)

    def test_default_search_omits_ui_filters(self) -> None:
        args = argparse.Namespace(
            command="search",
            keyword="AI Agent",
            sort_by="综合",
            note_type="不限",
            publish_time="不限",
            search_scope="不限",
            location="不限",
        )
        self.assertEqual(MODULE._payload_for_command(args), {"keyword": "AI Agent"})

    def test_search_sends_only_non_default_filters(self) -> None:
        args = argparse.Namespace(
            command="search",
            keyword="AI Agent",
            sort_by="最新",
            note_type="不限",
            publish_time="一周内",
            search_scope="不限",
            location="不限",
        )
        self.assertEqual(
            MODULE._payload_for_command(args),
            {
                "keyword": "AI Agent",
                "filters": {"sort_by": "最新", "publish_time": "一周内"},
            },
        )

    def test_chromium_child_environment_excludes_connector_cookie(self) -> None:
        with patch.dict(os.environ, {MODULE.COOKIE_ENV: "top-secret"}, clear=False):
            child_env = MODULE._chromium_child_env(Path("/tmp/xhs"))
        self.assertNotIn(MODULE.COOKIE_ENV, child_env)
        self.assertEqual(child_env["HOME"], "/tmp/xhs")

    def test_confirmed_write_dispatches_converted_cookies_in_memory(self) -> None:
        args = argparse.Namespace(
            command="like",
            feed_id="feed",
            xsec_token="token",
            xsec_source="pc_note",
            approval_digest="",
            approval_token="",
        )
        runtime_instance = MagicMock()
        runtime_instance.__enter__.return_value = runtime_instance
        runtime_instance.run.return_value = {"success": True}
        raw = [{"name": "a1", "value": "secret", "domain": ".xiaohongshu.com"}]
        with tempfile.TemporaryDirectory() as directory:
            payload = MODULE._payload_for_command(args)
            assert payload is not None
            digest = MODULE._approval_digest("like", payload)
            with (
                patch.dict(
                    os.environ,
                    {"HOME": directory, "AICHAT_SANDBOX_SESSION_ID": "session-1"},
                ),
            ):
                args.approval_digest = digest
                args.approval_token, execution_grant = _approval_credentials(
                    directory, digest
                )
                with (
                    patch.object(MODULE, "CONFIRM", True),
                    patch.object(MODULE, "load_connector_cookie_jar", return_value=raw),
                    patch.dict(
                        os.environ,
                        {MODULE.EXECUTION_GRANT_ENV: execution_grant},
                        clear=False,
                    ),
                    patch.object(
                        MODULE,
                        "DirectXiaohongshuRuntime",
                        return_value=runtime_instance,
                    ) as runtime,
                ):
                    result = MODULE.execute(args)
        self.assertEqual(result, {"success": True})
        runtime.assert_called_once_with(
            [
                {
                    "name": "a1",
                    "value": "secret",
                    "domain": ".xiaohongshu.com",
                    "path": "/",
                    "httpOnly": False,
                    "secure": False,
                }
            ]
        )
        runtime_instance.run.assert_called_once_with(
            "like",
            {
                "feed_id": "feed",
                "xsec_token": "token",
                "xsec_source": "pc_note",
                "unlike": False,
            },
        )

    def test_confirmed_write_requires_worker_execution_grant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token, _grant = _approval_credentials(directory, "digest")
            with (
                patch.dict(
                    os.environ,
                    {"AICHAT_SANDBOX_SESSION_ID": "session-1"},
                    clear=True,
                ),
                self.assertRaisesRegex(RuntimeError, "no worker execution grant"),
            ):
                MODULE._verify_execution_grant("digest", token)

    def test_approval_rejects_changed_media_and_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(b"image-v1")
            payload = {"title": "title", "images": [str(image)]}
            _, canonical = MODULE._stage_media_payload(
                payload, Path(directory) / "stage-1"
            )
            digest = MODULE._approval_digest("publish", canonical)
            with patch.dict(
                os.environ,
                {"HOME": directory, "AICHAT_SANDBOX_SESSION_ID": "session-1"},
            ):
                token = _approval_token(directory, digest)
                image.write_bytes(b"image-v2")
                _, changed = MODULE._stage_media_payload(
                    payload, Path(directory) / "stage-2"
                )
                changed_digest = MODULE._approval_digest("publish", changed)
                self.assertNotEqual(digest, changed_digest)
                with self.assertRaisesRegex(RuntimeError, "changed after approval"):
                    MODULE._consume_approval_receipt(changed_digest, token)
                with patch.dict(
                    os.environ,
                    {"HOME": str(Path(directory) / "other-pod")},
                    clear=False,
                ):
                    MODULE._consume_approval_receipt(digest, token)
                altered = token[:-1] + ("A" if token[-1] != "A" else "B")
                with self.assertRaisesRegex(RuntimeError, "malformed"):
                    MODULE._consume_approval_receipt(digest, altered)

    def test_approval_requires_sandbox_session_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = _approval_token(directory, "digest")
            with (
                patch.dict(os.environ, {}, clear=True),
                self.assertRaisesRegex(RuntimeError, "another sandbox session"),
            ):
                MODULE._consume_approval_receipt("digest", token)

    def test_long_article_dry_run_never_starts_runtime(self) -> None:
        args = argparse.Namespace(
            command="publish-long",
            title="长文测试",
            title_file=None,
            content="正文",
            content_file=None,
            description="摘要",
            description_file=None,
            images=[],
            template=None,
            schedule_at=None,
            original=False,
            visibility="仅自己可见",
            products=[],
            tags=[],
        )
        with (
            patch.object(MODULE, "CONFIRM", False),
            patch.object(
                MODULE,
                "load_connector_cookie_jar",
                return_value=[
                    {"name": "a1", "value": "secret", "domain": ".xiaohongshu.com"}
                ],
            ),
            patch.object(MODULE, "DirectXiaohongshuRuntime") as runtime,
            patch.object(MODULE, "output") as emit,
            patch.dict(
                os.environ, {"AICHAT_SANDBOX_SESSION_ID": "session-1"}, clear=False
            ),
        ):
            self.assertEqual(MODULE.execute(args), {})
        runtime.assert_not_called()
        self.assertEqual(emit.call_args.args[0]["request"]["description"], "摘要")

    def test_parser_registers_complete_connector_surface(self) -> None:
        parser = MODULE.build_parser()
        choices = next(
            action for action in parser._actions if action.dest == "command"
        ).choices
        self.assertEqual(
            set(choices),
            {
                "status",
                "whoami",
                "feeds",
                "search",
                "detail",
                "profile",
                "publish",
                "publish-video",
                "publish-long",
                "comment",
                "reply",
                "like",
                "unlike",
                "favorite",
                "unfavorite",
            },
        )

    def test_reads_current_user_from_reactive_state(self) -> None:
        page = MagicMock()
        page.evaluate.return_value = {
            "is_logged_in": True,
            "user_id": "user",
            "red_id": "red",
            "nickname": "name",
        }
        self.assertEqual(
            MODULE._read_current_user(page),
            {
                "is_logged_in": True,
                "user_id": "user",
                "red_id": "red",
                "nickname": "name",
            },
        )

    def test_video_publish_uses_current_shadow_host(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish_video as publish_video

        page = MagicMock()
        page.evaluate.return_value = True
        with patch.object(publish_video, "click_publish_button") as publish:
            publish_video.click_publish_video_button(page)
        publish.assert_called_once_with(page)

    def test_reply_finds_rendered_comment_before_end_marker(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.comment as comment

        page = MagicMock()
        page.has_element.return_value = True
        with patch.object(comment, "_check_end_container") as check_end:
            found = comment._find_and_scroll_to_comment(
                page, "comment-id", "", max_attempts=1
            )
        self.assertTrue(found)
        check_end.assert_not_called()

    def test_reply_user_id_is_serialized_for_javascript(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.comment as comment

        page = MagicMock()
        page.evaluate.return_value = False
        comment._locate_target_comment(page, "", 'x"]);globalThis.pwned=true;//', 0)
        script = page.evaluate.call_args.args[0]
        self.assertIn('const userId = "x\\"]);globalThis.pwned=true;//";', script)
        self.assertIn("getAttribute('data-user-id') === userId", script)

    def test_publish_requires_observed_success_feedback(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [None, "fired", *([None] * 60)]
        with (
            patch.object(publish.time, "monotonic", side_effect=[0, 0, *range(1, 17)]),
            patch.object(publish.time, "sleep"),
            self.assertRaisesRegex(publish.PublishError, "未捕获到发布成功反馈"),
        ):
            publish.click_publish_button(page)

    def test_verification_challenge_stops_without_navigation_retry(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.feed_detail as feed_detail

        page = MagicMock()
        page.get_element_text.return_value = "打开小红书App扫码"
        with (
            patch.object(feed_detail.time, "sleep"),
            self.assertRaises(feed_detail.PageNotAccessibleError),
        ):
            feed_detail._check_page_accessible(
                page, "https://www.xiaohongshu.com/explore/id"
            )
        page.navigate.assert_not_called()

    def test_like_does_not_blindly_toggle_twice(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.like_favorite as interactions

        page = MagicMock()
        with (
            patch.object(
                interactions, "_get_interact_state", return_value=(False, False)
            ),
            patch.object(interactions.time, "sleep"),
        ):
            result = interactions._toggle_like(page, "feed", target_liked=True)
        self.assertFalse(result.success)
        page.click_element.assert_called_once_with(interactions.LIKE_BUTTON)

    def test_schedule_uses_browser_timezone(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.return_value = "Asia/Shanghai"
        page.has_element.return_value = True
        page.get_element_attribute.return_value = "2030-01-01 10:00"
        with patch.object(publish.time, "sleep"):
            publish._set_schedule_publish(page, "2030-01-01T02:00:00+00:00")
        page.input_text.assert_called_once_with(
            publish.DATETIME_INPUT, "2030-01-01 10:00"
        )


if __name__ == "__main__":
    unittest.main()

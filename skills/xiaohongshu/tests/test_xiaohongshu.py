from __future__ import annotations

import importlib.util
import argparse
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).parents[1] / "scripts" / "xiaohongshu.py"
SPEC = importlib.util.spec_from_file_location("xiaohongshu_skill", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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
                preview_digest="",
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
        self.assertTrue(emit.call_args.args[0]["preview_digest"])

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

    def test_unattended_write_is_always_refused(self) -> None:
        env = {
            "AICHAT_UNATTENDED_MODE": "true",
            "AICHAT_ACTIVE_SKILL": "acedatacloud/xiaohongshu",
            "AICHAT_UNATTENDED_ALLOWED_SKILLS": '["acedatacloud/xiaohongshu"]',
        }
        with patch.dict(os.environ, env, clear=False):
            allowed, reason = MODULE._unattended_write_allowed()
        self.assertFalse(allowed)
        self.assertIn("interactive confirmation", reason)

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

    def test_runtime_profile_ignores_long_sandbox_tmpdir(self) -> None:
        sandbox_tmpdir = "/tmp/sessions/" + "session-" * 20
        with patch.dict(os.environ, {"TMPDIR": sandbox_tmpdir}, clear=False):
            temp_dir = MODULE._create_runtime_temp_directory()
        try:
            self.assertEqual(Path(temp_dir.name).parent, Path("/tmp"))
        finally:
            temp_dir.cleanup()

    def test_confirmed_write_dispatches_converted_cookies_in_memory(self) -> None:
        args = argparse.Namespace(
            command="like",
            feed_id="feed",
            xsec_token="token",
            xsec_source="pc_note",
            preview_digest="",
        )
        runtime_instance = MagicMock()
        runtime_instance.__enter__.return_value = runtime_instance
        runtime_instance.run.return_value = {"success": True}
        raw = [{"name": "a1", "value": "secret", "domain": ".xiaohongshu.com"}]
        payload = MODULE._payload_for_command(args)
        assert payload is not None
        args.preview_digest = MODULE._preview_digest("like", payload)
        with (
            patch.object(MODULE, "CONFIRM", True),
            patch.object(MODULE, "load_connector_cookie_jar", return_value=raw),
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

    def test_preview_digest_changes_with_media(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(b"image-v1")
            payload = {"title": "title", "images": [str(image)]}
            _, canonical = MODULE._stage_media_payload(
                payload, Path(directory) / "stage-1"
            )
            digest = MODULE._preview_digest("publish", canonical)
            image.write_bytes(b"image-v2")
            _, changed = MODULE._stage_media_payload(
                payload, Path(directory) / "stage-2"
            )
            changed_digest = MODULE._preview_digest("publish", changed)
            self.assertNotEqual(digest, changed_digest)

    def test_confirmed_write_rejects_changed_preview(self) -> None:
        args = argparse.Namespace(
            command="like",
            feed_id="feed",
            xsec_token="token",
            xsec_source="pc_note",
            preview_digest="different",
        )
        with (
            patch.object(MODULE, "CONFIRM", True),
            self.assertRaisesRegex(RuntimeError, "changed after preview"),
        ):
            MODULE.execute(args)

    def test_staged_media_has_aggregate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.png"
            image.write_bytes(b"1234")
            with (
                patch.object(MODULE, "MAX_STAGED_MEDIA_BYTES", 3),
                self.assertRaisesRegex(ValueError, "256 MB"),
            ):
                MODULE._stage_media_payload(
                    {"images": [str(image)]}, Path(directory) / "stage"
                )

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
            publish_video.click_publish_video_button(page, deadline=float("inf"))
        publish.assert_called_once_with(page)

    def test_video_publish_reuses_one_operation_deadline(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish_video as publish_video

        page = MagicMock()
        content = MagicMock()
        with (
            patch.object(publish_video.time, "monotonic", return_value=10.0),
            patch.object(publish_video, "fill_publish_video_form") as fill,
            patch.object(publish_video, "click_publish_video_button") as click,
        ):
            publish_video.publish_video_content(page, content)
        fill.assert_called_once_with(page, content, deadline=110.0)
        click.assert_called_once_with(page, deadline=110.0)

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
        page.evaluate.side_effect = [None, "ready", *([None] * 60)]
        page.wait_for_event.return_value = None
        page.click_pierced_button.return_value = True
        with (
            patch.object(publish.time, "monotonic", side_effect=[0, 0, *range(1, 17)]),
            self.assertRaisesRegex(publish.PublishError, "未捕获到发布成功反馈"),
        ):
            publish.click_publish_button(page)

    def test_publish_ignores_creator_telemetry_and_waits_for_finished_body(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [None, "ready", None, None, None, None, True]
        page.click_pierced_button.return_value = True
        page.wait_for_event.side_effect = [
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "requestId": "telemetry",
                    "request": {
                        "method": "POST",
                        "url": "https://creator.xiaohongshu.com/api/telemetry",
                    },
                },
            },
            {"method": "Network.loadingFinished", "params": {"requestId": "telemetry"}},
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "requestId": "publish",
                    "request": {
                        "method": "POST",
                        "url": "https://edith.xiaohongshu.com/api/sns/web/v1/note/publish",
                    },
                },
            },
            {
                "method": "Network.responseReceived",
                "params": {"requestId": "publish"},
            },
            {"method": "Network.loadingFinished", "params": {"requestId": "publish"}},
        ]

        def send(method: str, _params: dict | None = None) -> dict:
            if method == "Network.getResponseBody":
                return {"body": '{"code":0,"data":{"note_id":"note"}}'}
            return {}

        page._send_session.side_effect = send
        with (
            patch.object(publish.time, "monotonic", return_value=0),
            patch.object(publish.time, "sleep"),
        ):
            publish.click_publish_button(page)

        body_calls = [
            call
            for call in page._send_session.call_args_list
            if call.args and call.args[0] == "Network.getResponseBody"
        ]
        self.assertEqual(len(body_calls), 1)
        self.assertEqual(body_calls[0].args[1], {"requestId": "publish"})

    def test_publish_decodes_base64_body_and_ignores_success_fallback(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import base64
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [
            None,
            "ready",
            {"code": 0, "success": True, "note_id": "autosave"},
            {"code": 0, "success": True, "note_id": "autosave"},
            True,
        ]
        page.click_pierced_button.return_value = True
        page.wait_for_event.side_effect = [
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "requestId": "publish",
                    "request": {
                        "method": "POST",
                        "url": "https://edith.xiaohongshu.com/api/note/publish",
                    },
                },
            },
            {"method": "Network.responseReceived", "params": {"requestId": "publish"}},
            {"method": "Network.loadingFinished", "params": {"requestId": "publish"}},
        ]
        encoded = base64.b64encode(b'{"data":{"note_id":"published"}}').decode()

        def send(method: str, _params: dict | None = None) -> dict:
            if method == "Network.getResponseBody":
                return {"body": encoded, "base64Encoded": True}
            return {}

        page._send_session.side_effect = send
        with (
            patch.object(publish.time, "monotonic", return_value=0),
            patch.object(publish.time, "sleep"),
        ):
            publish.click_publish_button(page)

        self.assertEqual(
            [call.args[0] for call in page._send_session.call_args_list].count(
                "Network.getResponseBody"
            ),
            1,
        )

    def test_publish_classifies_nested_risk_control_response(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [None, "ready", None]
        page.click_pierced_button.return_value = True
        page.wait_for_event.side_effect = [
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "requestId": "publish",
                    "request": {
                        "method": "POST",
                        "url": "https://edith.xiaohongshu.com/api/note/publish",
                    },
                },
            },
            {"method": "Network.loadingFinished", "params": {"requestId": "publish"}},
        ]
        page._send_session.side_effect = lambda method, _params=None: (
            {"body": '{"code":0,"data":{"code":-9136,"msg":"禁止发笔记"}}'}
            if method == "Network.getResponseBody"
            else {}
        )
        with (
            patch.object(publish.time, "monotonic", return_value=0),
            self.assertRaises(publish.AccountRiskControlError),
        ):
            publish.click_publish_button(page)

    def test_create_note_id_cannot_outrun_publish_response(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [None, "ready", None, None, None, True]
        page.click_pierced_button.return_value = True
        page.wait_for_event.side_effect = [
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "requestId": "create",
                    "request": {
                        "method": "POST",
                        "url": "https://edith.xiaohongshu.com/api/note/create",
                    },
                },
            },
            {"method": "Network.loadingFinished", "params": {"requestId": "create"}},
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "requestId": "publish",
                    "request": {
                        "method": "POST",
                        "url": "https://edith.xiaohongshu.com/api/note/publish",
                    },
                },
            },
            {"method": "Network.loadingFinished", "params": {"requestId": "publish"}},
        ]

        def send(method: str, params: dict | None = None) -> dict:
            if method != "Network.getResponseBody":
                return {}
            note_id = "draft" if params == {"requestId": "create"} else "published"
            return {"body": json.dumps({"data": {"note_id": note_id}})}

        page._send_session.side_effect = send
        with (
            patch.object(publish.time, "monotonic", return_value=0),
            patch.object(publish.time, "sleep"),
        ):
            publish.click_publish_button(page)

        body_ids = [
            call.args[1]["requestId"]
            for call in page._send_session.call_args_list
            if call.args and call.args[0] == "Network.getResponseBody"
        ]
        self.assertEqual(body_ids, ["create", "publish"])

    def test_page_retains_unsolicited_events_while_waiting_for_response(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        from xhs.cdp import Page

        transport = MagicMock()
        expected_event = {
            "method": "Network.responseReceived",
            "sessionId": "session",
            "params": {"requestId": "request"},
        }
        transport.recv.side_effect = [
            json.dumps(expected_event),
            json.dumps({"id": 1001, "result": {"ok": True}}),
        ]
        page = Page(MagicMock(_transport=transport), "target", "session")

        self.assertEqual(page._wait_session(1001), {"ok": True})
        self.assertEqual(page.wait_for_event(0), expected_event)

    def test_page_event_queue_is_bounded(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        from xhs.cdp import Page

        page = Page(MagicMock(_transport=MagicMock()), "target", "session")
        for index in range(300):
            page._events.append({"method": "Network.event", "index": index})
        self.assertEqual(len(page._events), 256)
        self.assertEqual(page._events[0]["index"], 44)

    def test_pierced_publish_button_requires_coordinate_hit(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        from xhs.cdp import Page

        page = Page(MagicMock(_transport=MagicMock()), "target", "session")
        page._send_session = MagicMock(
            side_effect=[
                {
                    "root": {
                        "nodeName": "#document",
                        "children": [
                            {
                                "nodeName": "XHS-PUBLISH-BTN",
                                "attributes": ["is-publish", "true"],
                                "shadowRoots": [
                                    {
                                        "nodeName": "#document-fragment",
                                        "children": [
                                            {
                                                "nodeName": "BUTTON",
                                                "backendNodeId": 42,
                                                "children": [
                                                    {"nodeName": "#text", "nodeValue": "发布"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                },
                {},
                {
                    "model": {
                        "width": 10,
                        "height": 10,
                        "border": [0, 0, 10, 0, 10, 10, 0, 10],
                    }
                },
                {"backendNodeId": 43},
                {"object": {"objectId": "hit"}},
                {"object": {"objectId": "button"}},
                {"result": {"value": False}},
            ]
        )
        page.mouse_click = MagicMock()

        self.assertFalse(page.click_pierced_button("xhs-publish-btn", "发布"))
        page.mouse_click.assert_not_called()

    def test_pierced_publish_button_skips_hidden_first_candidate(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        from xhs.cdp import Page

        def button(backend_node_id: int) -> dict:
            return {
                "nodeName": "BUTTON",
                "backendNodeId": backend_node_id,
                "children": [{"nodeName": "#text", "nodeValue": "发布"}],
            }

        page = Page(MagicMock(_transport=MagicMock()), "target", "session")
        page._send_session = MagicMock(
            side_effect=[
                {
                    "root": {
                        "nodeName": "#document",
                        "children": [
                            {
                                "nodeName": "XHS-PUBLISH-BTN",
                                "attributes": ["is-publish", "true"],
                                "shadowRoots": [
                                    {
                                        "nodeName": "#document-fragment",
                                        "children": [button(41), button(42)],
                                    }
                                ],
                            }
                        ],
                    }
                },
                {},
                {"model": {"width": 0, "height": 0, "border": [0] * 8}},
                {},
                {
                    "model": {
                        "width": 10,
                        "height": 10,
                        "border": [0, 0, 10, 0, 10, 10, 0, 10],
                    }
                },
                {"backendNodeId": 42},
            ]
        )
        page.mouse_move = MagicMock()
        page.mouse_click = MagicMock()

        with patch("xhs.cdp.time.sleep"):
            self.assertTrue(page.click_pierced_button("xhs-publish-btn", "发布"))
        page.mouse_click.assert_called_once()

    def test_visibility_requires_explicit_selected_marker(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [True, False]
        with (
            patch.object(publish.time, "sleep"),
            self.assertRaisesRegex(publish.PublishError, "可见范围未确认生效"),
        ):
            publish._set_visibility(page, "仅自己可见")
        script = page.evaluate.call_args_list[1].args[0]
        self.assertNotIn("dropdown?.textContent", script)

    def test_visibility_accepts_explicit_selected_marker(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [True, True]
        with patch.object(publish.time, "sleep"):
            publish._set_visibility(page, "仅自己可见")

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

    def test_product_binding_verifies_refreshed_match_and_selected_count(self) -> None:
        if str(MODULE.VENDOR_DIR) not in sys.path:
            sys.path.insert(0, str(MODULE.VENDOR_DIR))
        import xhs.publish as publish

        page = MagicMock()
        page.evaluate.side_effect = [True, True, True, True]
        with patch.object(publish.time, "sleep"):
            publish.bind_products(page, ["商品 A"])

        search_script = page.evaluate.call_args_list[2].args[0]
        save_script = page.evaluate.call_args_list[3].args[0]
        self.assertIn("observedRefresh", search_script)
        self.assertIn("includes(keyword)", search_script)
        self.assertIn("selectedCount < expected", save_script)

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

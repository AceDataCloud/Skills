import contextlib
import io
import json
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / "scripts" / "deliver.py"


class ClientTests(unittest.TestCase):
    def test_unconfigured_install_does_not_make_requests(self):
        output = io.StringIO()
        with (
            patch.object(sys, "argv", [str(SCRIPT)]),
            patch.object(Path, "read_text", side_effect=FileNotFoundError),
            patch("urllib.request.urlopen") as request,
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_path(str(SCRIPT))
        self.assertEqual(stopped.exception.code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "not_configured")
        request.assert_not_called()

    def test_tool_receipt_cannot_echo_unexpected_secret_fields(self):
        output = io.StringIO()
        response = io.BytesIO(
            json.dumps(
                {
                    "status": "SECRET-CODE",
                    "order_id": "SECRET-CODE",
                    "error": "SECRET-CODE",
                    "key": "SECRET-CODE",
                }
            ).encode()
        )
        with (
            patch.object(sys, "argv", [str(SCRIPT)]),
            patch.object(
                Path,
                "read_text",
                return_value=json.dumps(
                    {"url": "http://seller-tool.internal", "token": "test-tool-token"}
                ),
            ),
            patch("urllib.request.urlopen", return_value=response),
            contextlib.redirect_stdout(output),
        ):
            runpy.run_path(str(SCRIPT))
        self.assertNotIn("SECRET-CODE", output.getvalue())
        self.assertEqual(
            json.loads(output.getvalue()),
            {"status": "check_original_order", "secret_returned": False},
        )

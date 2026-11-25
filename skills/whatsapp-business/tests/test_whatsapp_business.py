import importlib.util
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "whatsapp_business.py"
SPEC = importlib.util.spec_from_file_location("whatsapp_business", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_dry_run_does_not_send():
    with patch.object(MODULE, "api_request") as api:
        result = MODULE.send_template(
            "+919876543210", "welcome_followup", "en_US", "CRM-123", None, False, "", ""
        )
    assert result["dry_run"] is True
    assert result["request"]["to"] == "919876543210"
    api.assert_not_called()


def test_confirm_returns_accepted_not_delivered():
    with patch.object(
        MODULE, "api_request", return_value={"messages": [{"id": "wamid.123"}]}
    ) as api:
        result = MODULE.send_template(
            "+919876543210",
            "welcome_followup",
            "en_US",
            "CRM-123",
            None,
            True,
            "test-token",
            "12345",
        )
    assert result == {
        "accepted": True,
        "delivered": False,
        "message_ids": ["wamid.123"],
        "opt_in_reference": "CRM-123",
    }
    api.assert_called_once()


def test_rejects_batch_or_missing_opt_in():
    for recipient in ["+919876543210,+919876543211", "9876543210"]:
        try:
            MODULE.message_payload(recipient, "welcome_followup", "en_US")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid recipient was accepted")
    try:
        MODULE.send_template(
            "+919876543210", "welcome_followup", "en_US", "", None, False, "", ""
        )
    except ValueError:
        pass
    else:
        raise AssertionError("missing opt-in was accepted")

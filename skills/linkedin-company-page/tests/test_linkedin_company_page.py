import importlib.util
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "linkedin_company_page.py"
SPEC = importlib.util.spec_from_file_location("linkedin_company_page", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_dry_run_never_uses_network(tmp_path):
    body = tmp_path / "post.txt"
    body.write_text("A useful technical update", encoding="utf-8")
    with patch.object(MODULE, "request") as api:
        result = MODULE.publish("12345", body, False)
    assert result == {
        "dry_run": True,
        "target": "urn:li:organization:12345",
        "post": "A useful technical update",
    }
    api.assert_not_called()


def test_confirm_reads_back_exact_organization(tmp_path, monkeypatch):
    body = tmp_path / "post.txt"
    body.write_text("Technical update", encoding="utf-8")
    monkeypatch.setenv("LINKEDIN_COMPANY_PAGE_TOKEN", "test-token")
    with patch.object(MODULE, "request") as api:
        api.side_effect = [
            (201, {"x-restli-id": "urn:li:share:123"}, {}),
            (200, {}, {"author": "urn:li:organization:12345"}),
        ]
        result = MODULE.publish("12345", body, True)
    assert result["verified"] is True
    assert result["urn"] == "urn:li:share:123"
    assert api.call_count == 2


def test_mismatched_readback_is_not_verified(tmp_path, monkeypatch):
    body = tmp_path / "post.txt"
    body.write_text("Technical update", encoding="utf-8")
    monkeypatch.setenv("LINKEDIN_COMPANY_PAGE_TOKEN", "test-token")
    with patch.object(MODULE, "request") as api:
        api.side_effect = [
            (201, {"x-restli-id": "urn:li:share:123"}, {}),
            (200, {}, {"author": "urn:li:organization:other"}),
        ]
        result = MODULE.publish("12345", body, True)
    assert result["submitted"] is True
    assert result["verified"] is False

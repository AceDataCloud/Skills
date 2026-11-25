import importlib.util
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "postman_publisher.py"
SPEC = importlib.util.spec_from_file_location("postman_publisher", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


COLLECTION = {
    "info": {
        "name": "AceDataCloud Starter",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": [
        {
            "name": "First request",
            "request": {"method": "GET", "url": "https://api.acedata.cloud/health"},
        }
    ],
    "variable": [{"key": "api_key", "value": ""}],
}


def test_dry_run_is_offline():
    with patch.object(MODULE, "request") as api:
        result = MODULE.sync(COLLECTION, None, False, "", "")
    assert result["request_count"] == 1
    assert result["operation"] == "create"
    api.assert_not_called()


def test_rejects_embedded_key():
    bad = {**COLLECTION, "variable": [{"key": "api_key", "value": "real-key"}]}
    try:
        MODULE.validate_collection(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("embedded credential was accepted")


def test_rejects_embedded_auth_value():
    bad = {
        **COLLECTION,
        "item": [
            {
                "name": "Secret",
                "request": {
                    "method": "GET",
                    "url": "https://api.acedata.cloud/health",
                    "auth": {
                        "type": "apikey",
                        "apikey": [{"key": "value", "value": "real-key"}],
                    },
                },
            }
        ],
    }
    try:
        MODULE.validate_collection(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("embedded auth value was accepted")


def test_accepts_structural_apikey_header_name():
    valid = {
        **COLLECTION,
        "auth": {
            "type": "apikey",
            "apikey": [
                {"key": "value", "value": "{{api_key}}"},
                {"key": "key", "value": "x-api-key"},
                {"key": "in", "value": "header"},
            ],
        },
    }
    assert MODULE.validate_collection(valid)["info"]["name"] == "AceDataCloud Starter"


def test_public_workspace_required():
    with patch.object(
        MODULE, "request", return_value={"workspace": {"type": "personal"}}
    ) as api:
        try:
            MODULE.sync(COLLECTION, None, True, "test-key", "workspace-1")
        except ValueError:
            pass
        else:
            raise AssertionError("private workspace was accepted")
    api.assert_called_once()


def test_create_then_readback():
    with patch.object(MODULE, "request") as api:
        api.side_effect = [
            {"workspace": {"type": "public"}},
            {"collection": {"uid": "owner-collection-1"}},
            {
                "collection": {
                    "info": {"name": "AceDataCloud Starter"},
                    "item": COLLECTION["item"],
                }
            },
        ]
        result = MODULE.sync(COLLECTION, None, True, "test-key", "workspace-1")
    assert result["verified"] is True
    assert result["collection_id"] == "owner-collection-1"
    assert api.call_count == 3


def test_same_name_with_different_request_is_not_verified():
    with patch.object(MODULE, "request") as api:
        api.side_effect = [
            {"workspace": {"type": "public"}},
            {"collection": {"uid": "owner-collection-1"}},
            {
                "collection": {
                    "info": {"name": "AceDataCloud Starter"},
                    "item": [
                        {
                            "name": "First request",
                            "request": {"method": "GET", "url": "https://old.example/"},
                        }
                    ],
                }
            },
        ]
        result = MODULE.sync(COLLECTION, None, True, "test-key", "workspace-1")
    assert result["synced"] is True
    assert result["verified"] is False

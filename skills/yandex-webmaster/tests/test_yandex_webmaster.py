import importlib.util
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "yandex_webmaster.py"
SPEC = importlib.util.spec_from_file_location("yandex_webmaster", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_host_id_is_encoded_and_query_limited():
    with patch.object(MODULE, "api_get") as api:
        api.side_effect = [{"user_id": 123}, {"queries": []}]
        MODULE.popular_queries("test-token", "https:example.com:443", 20)
    path = api.call_args.args[0]
    assert path.endswith("/hosts/https%3Aexample.com%3A443/search-queries/popular")
    assert api.call_args.args[2]["order_by"] == "TOTAL_SHOWS"
    assert api.call_args.args[2]["limit"] == 20


def test_rejects_invalid_page_size():
    with patch.object(MODULE, "api_get") as api:
        try:
            MODULE.popular_queries("test-token", "https:example.com:443", 0)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid page size was accepted")
    api.assert_not_called()

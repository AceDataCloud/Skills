import importlib.util
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "yandex_metrica.py"
SPEC = importlib.util.spec_from_file_location("yandex_metrica", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_country_report_uses_official_session_dimension():
    with patch.object(MODULE, "api_get", return_value={"data": []}) as api:
        MODULE.report("test-token", "12345", "country", "2026-09-01", "2026-09-30")
    params = api.call_args.args[2]
    assert params["dimensions"] == "ym:s:regionCountry"
    assert params["attribution"] == "lastsign"


def test_utm_report_uses_explicit_attribution_model():
    with patch.object(MODULE, "api_get", return_value={"data": []}) as api:
        MODULE.report("test-token", "12345", "utm-source", "2026-09-01", "2026-09-30")
    assert api.call_args.args[2]["dimensions"] == "ym:s:<attribution>UTMSource"


def test_rejects_backwards_date_range():
    try:
        MODULE.report("test-token", "12345", "country", "2026-09-30", "2026-09-01")
    except ValueError:
        pass
    else:
        raise AssertionError("backwards date range was accepted")

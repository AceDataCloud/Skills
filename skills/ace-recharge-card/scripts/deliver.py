"""No arguments, no inventory access, no card key in the tool result."""

import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

if len(sys.argv) != 1:
    raise SystemExit("This tool takes no arguments.")
try:
    config = json.loads((Path(__file__).parent / "client.json").read_text())
    if not isinstance(config, dict) or not all(
        isinstance(config.get(key), str) and config[key] for key in ("url", "token")
    ):
        raise ValueError("Missing seller configuration")
except (OSError, ValueError):
    print(json.dumps({"status": "not_configured", "secret_returned": False}))
    raise SystemExit(0)
request = urllib.request.Request(
    config["url"].rstrip("/") + "/deliver",
    data=b"{}",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + config["token"],
    },
)
try:
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
except urllib.error.HTTPError as error:
    result = {"status": "check_original_order", "http_status": error.code}
except (OSError, ValueError):
    result = {"status": "check_original_order", "error": "delivery_response_unknown"}
# Only known statuses and a validated order UUID may enter the model transcript.
safe = {"status": "check_original_order", "secret_returned": False}
if result.get("status") in {"delivered_to_original_order", "probe_completed"}:
    safe["status"] = result["status"]
if result.get("order_id"):
    try:
        safe["order_id"] = str(uuid.UUID(result["order_id"]))
    except (ValueError, TypeError, AttributeError):
        pass
print(json.dumps(safe))

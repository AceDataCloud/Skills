#!/usr/bin/env python3
"""Read WhatsApp Business templates and send one opted-in template."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GRAPH = "https://graph.facebook.com/v23.0"


def api_request(method: str, path: str, token: str, params=None, payload=None) -> dict:
    url = GRAPH + path + ("?" + urlencode(params) if params else "")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").replace(token, "[redacted]")
        raise RuntimeError(f"WhatsApp Cloud API {exc.code}: {body[:1000]}") from None
    except URLError as exc:
        raise RuntimeError(f"WhatsApp Cloud API request failed: {exc.reason}") from None


def message_payload(to: str, template: str, language: str, components=None) -> dict:
    if not re.fullmatch(r"\+[1-9]\d{6,14}", to):
        raise ValueError("recipient must be one E.164 phone number")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,512}", template):
        raise ValueError("template must be an approved template name")
    if not re.fullmatch(r"[a-z]{2,3}(?:_[A-Z]{2})?", language):
        raise ValueError("language must be a Meta language code such as en_US")
    result = {
        "messaging_product": "whatsapp",
        "to": to[1:],
        "type": "template",
        "template": {"name": template, "language": {"code": language}},
    }
    if components is not None:
        if not isinstance(components, list):
            raise ValueError("components must be a JSON array")
        result["template"]["components"] = components
    return result


def send_template(
    to, template, language, opt_in_reference, components, confirm, token, phone_id
):
    if not opt_in_reference.strip():
        raise ValueError("a real opt-in reference is required")
    payload = message_payload(to, template, language, components)
    if not confirm:
        return {
            "dry_run": True,
            "opt_in_reference": opt_in_reference,
            "request": payload,
        }
    if not token or not phone_id.isdecimal():
        raise ValueError(
            "connect a WhatsApp Business token and numeric phone number ID first"
        )
    response = api_request("POST", f"/{phone_id}/messages", token, payload=payload)
    ids = [item.get("id") for item in response.get("messages", []) if item.get("id")]
    return {
        "accepted": bool(ids),
        "delivered": False,
        "message_ids": ids,
        "opt_in_reference": opt_in_reference,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("templates")
    send = subs.add_parser("send-template")
    send.add_argument("--to", required=True)
    send.add_argument("--template", required=True)
    send.add_argument("--language", required=True)
    send.add_argument("--opt-in-reference", required=True)
    send.add_argument("--components-file", type=Path)
    send.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("WHATSAPPBUSINESS_ACCESS_TOKEN", "")
    phone_id = os.environ.get("WHATSAPPBUSINESS_PHONE_NUMBER_ID", "")
    waba_id = os.environ.get("WHATSAPPBUSINESS_WABA_ID", "")
    try:
        if args.command == "templates":
            if not token or not waba_id.isdecimal():
                raise ValueError(
                    "connect a WhatsApp Business token and numeric WABA ID first"
                )
            result = api_request(
                "GET",
                f"/{waba_id}/message_templates",
                token,
                {"fields": "name,status,language,category", "limit": 100},
            )
        else:
            components = (
                json.loads(args.components_file.read_text(encoding="utf-8"))
                if args.components_file
                else None
            )
            result = send_template(
                args.to,
                args.template,
                args.language,
                args.opt_in_reference,
                components,
                args.confirm,
                token,
                phone_id,
            )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

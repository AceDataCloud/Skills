#!/usr/bin/env python3
"""DiDi ride helper — talks to the DiDi MCP server over the MCP
Streamable-HTTP transport using only the Python standard library.

The `didi` BYOC connector injects one env var:

    DIDI_MCP_KEY   the user's DiDi MCP key (secret — never printed)

Usage:
    python3 didi.py list                        # list available tools + schemas
    python3 didi.py call <tool> '<json-args>'   # call any tool

State-changing tools (`taxi_create_order`, `taxi_cancel_order`) are
gated: without a trailing `--confirm` they only DRY-RUN and change
nothing. `--confirm` is honored only as the LAST argument.

Examples:
    python3 didi.py call maps_textsearch '{"keywords":"北京西站","city":"北京"}'
    python3 didi.py call taxi_estimate '{"from_name":"...","from_lat":"39.9","from_lng":"116.3","to_name":"...","to_lat":"39.9","to_lng":"116.4"}'
    python3 didi.py call taxi_create_order '{"estimate_trace_id":"...","product_category":"1"}' --confirm
    python3 didi.py call taxi_query_order '{"order_id":"..."}'
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

MCP_ENDPOINT = os.environ.get("DIDI_MCP_URL", "https://mcp.didichuxing.com/mcp-servers")
MCP_KEY = os.environ.get("DIDI_MCP_KEY", "").strip()
PROTOCOL_VERSION = "2025-06-18"

# Tools that create or cancel a real ride — must be confirmed explicitly.
WRITE_TOOLS = {"taxi_create_order", "taxi_cancel_order"}


def die(payload: dict, code: int = 1) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(code)


class MCPClient:
    """Minimal MCP Streamable-HTTP client (stdlib only).

    Never logs or echoes the key; the endpoint URL (which carries the
    key as a query param) is kept internal and never printed.
    """

    def __init__(self, endpoint: str, key: str) -> None:
        sep = "&" if "?" in endpoint else "?"
        self._url = f"{endpoint}{sep}key={urllib.parse.quote(key, safe='')}"
        self._session_id: str | None = None
        self._rid = 0

    def _post(self, payload: dict, expect_id):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self._url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("MCP-Protocol-Version", PROTOCOL_VERSION)
        if self._session_id:
            req.add_header("Mcp-Session-Id", self._session_id)
        try:
            resp = urllib.request.urlopen(req, timeout=90)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:600]
            die(
                {
                    "error": f"HTTP {exc.code} from DiDi MCP",
                    "detail": detail,
                    "hint": "If 401/403, the DiDi connector key is missing or expired — "
                    "reconnect at https://auth.acedata.cloud/user/connections",
                }
            )
        except urllib.error.URLError as exc:
            die({"error": "network error reaching DiDi MCP", "detail": str(exc.reason)})
        except Exception as exc:  # noqa: BLE001
            # Never let an unexpected traceback surface — self._url carries the
            # key as a query param (DiDi mandates ?key=), so emit only the
            # exception type, never its message or the URL.
            die({"error": "unexpected error calling DiDi MCP", "detail": type(exc).__name__})
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self._session_id = sid
        ctype = (resp.headers.get("Content-Type") or "").lower()
        raw = resp.read().decode("utf-8", "replace")
        return _parse_response(raw, ctype, expect_id)

    def initialize(self) -> None:
        self._rid += 1
        result = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._rid,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "acedata-didi-skill", "version": "1.0"},
                },
            },
            expect_id=self._rid,
        )
        if isinstance(result, dict) and result.get("error"):
            die({"error": "DiDi MCP initialize failed", "detail": result["error"]})
        # Fire-and-forget the initialized notification (no response expected).
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_id=None)

    def list_tools(self):
        self._rid += 1
        return self._post(
            {"jsonrpc": "2.0", "id": self._rid, "method": "tools/list"},
            expect_id=self._rid,
        )

    def call_tool(self, name: str, arguments: dict):
        self._rid += 1
        return self._post(
            {
                "jsonrpc": "2.0",
                "id": self._rid,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
            expect_id=self._rid,
        )


def _parse_response(raw: str, ctype: str, expect_id):
    """Return the JSON-RPC envelope for our request id.

    Handles both plain application/json and text/event-stream (SSE),
    where the response arrives as one or more `data: {...}` lines.
    """
    messages: list[dict] = []
    if "text/event-stream" in ctype:
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if not chunk or chunk == "[DONE]":
                continue
            try:
                messages.append(json.loads(chunk))
            except json.JSONDecodeError:
                continue
    else:
        raw = raw.strip()
        if not raw:
            return {}
        try:
            messages.append(json.loads(raw))
        except json.JSONDecodeError:
            die({"error": "unparseable response from DiDi MCP", "detail": raw[:600]})
    if expect_id is not None:
        for msg in messages:
            if isinstance(msg, dict) and msg.get("id") == expect_id:
                return msg
    return messages[-1] if messages else {}


def emit(envelope: dict) -> None:
    if not isinstance(envelope, dict):
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
        return
    if envelope.get("error"):
        die({"error": envelope["error"]})
    result = envelope.get("result", envelope)
    # tools/call results wrap text in a content[] array.
    if isinstance(result, dict) and isinstance(result.get("content"), list):
        texts = [
            c.get("text", "")
            for c in result["content"]
            if isinstance(c, dict) and c.get("type") == "text"
        ]
        if texts:
            print("\n".join(texts))
            if result.get("isError"):
                sys.exit(1)
            return
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _format_tools(envelope: dict) -> None:
    tools = (envelope.get("result") or {}).get("tools") if isinstance(envelope, dict) else None
    if not tools:
        emit(envelope)
        return
    slim = [
        {
            "name": t.get("name"),
            "description": t.get("description"),
            "inputSchema": t.get("inputSchema"),
        }
        for t in tools
    ]
    print(json.dumps(slim, ensure_ascii=False, indent=2))


def main() -> None:
    if not MCP_KEY:
        die(
            {
                "error": "DIDI_MCP_KEY not set",
                "hint": "Connect the DiDi connector at "
                "https://auth.acedata.cloud/user/connections to inject the key.",
            }
        )

    argv = sys.argv[1:]
    confirm = bool(argv) and argv[-1] == "--confirm"
    if confirm:
        argv = argv[:-1]
    if not argv:
        die({"error": "usage: didi.py <list|call> ..."})

    cmd, rest = argv[0], argv[1:]
    client = MCPClient(MCP_ENDPOINT, MCP_KEY)

    if cmd == "list":
        client.initialize()
        _format_tools(client.list_tools())
        return

    if cmd == "call":
        if not rest:
            die({"error": "call needs a tool name", "usage": "didi.py call <tool> '<json-args>'"})
        tool = rest[0]
        args_raw = rest[1] if len(rest) > 1 else "{}"
        try:
            arguments = json.loads(args_raw)
        except json.JSONDecodeError as exc:
            die({"error": "arguments must be valid JSON", "detail": str(exc), "got": args_raw})
        if not isinstance(arguments, dict):
            die({"error": "arguments JSON must be an object", "got": args_raw})

        if tool in WRITE_TOOLS and not confirm:
            print(
                json.dumps(
                    {
                        "dry_run": True,
                        "tool": tool,
                        "arguments": arguments,
                        "note": "state-changing call — re-run with --confirm as the LAST "
                        "argument to actually perform it",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        client.initialize()
        emit(client.call_tool(tool, arguments))
        return

    die({"error": f"unknown command: {cmd}", "usage": "didi.py <list|call> ..."})


if __name__ == "__main__":
    main()

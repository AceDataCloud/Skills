"""Seller-owned recharge-card inventory. Never return card secrets to the Agent."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hmac
import hashlib
import json
import os
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Rejected(Exception):
    """A bounded public reason, never a remote response or card code."""


def now():
    return datetime.now(timezone.utc).isoformat()


class Inventory:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, credits INTEGER NOT NULL,
                expires_at TEXT NOT NULL, order_id TEXT UNIQUE, work_id TEXT UNIQUE,
                event_id TEXT, delivery TEXT, reported INTEGER NOT NULL DEFAULT 0)""")
        os.chmod(path, 0o600)

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def import_cards(self, cards):
        with self.db() as db:
            for card in cards:
                code = card["code"].replace("-", "").replace(" ", "")
                if len(code) != 32 or not code.isascii() or not code.isalnum():
                    raise Rejected("invalid_inventory_code")
                if type(card["credits"]) is not int or card["credits"] <= 0:
                    raise Rejected("invalid_inventory_amount")
                expiry = (
                    datetime.fromisoformat(card["expires_at"])
                    .astimezone(timezone.utc)
                    .isoformat()
                )
                if expiry <= now():
                    raise Rejected("expired_inventory")
                existing = db.execute(
                    "SELECT * FROM cards WHERE id=? OR code=?", (card["id"], code)
                ).fetchone()
                if existing:
                    if (
                        existing["id"],
                        existing["code"],
                        existing["credits"],
                        existing["expires_at"],
                    ) != (card["id"], code, card["credits"], expiry):
                        raise Rejected("conflicting_inventory")
                    continue
                db.execute(
                    "INSERT INTO cards(id,code,credits,expires_at) VALUES (?,?,?,?)",
                    (card["id"], code, card["credits"], expiry),
                )

    def allocate(self, order_id, work_id, credits):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT * FROM cards WHERE order_id=? OR work_id=?", (order_id, work_id)
            ).fetchone()
            if previous:
                if (
                    previous["order_id"] != order_id
                    or previous["work_id"] != work_id
                    or previous["credits"] != credits
                ):
                    raise Rejected("original_order_mismatch")
                return dict(previous)
            row = db.execute(
                "SELECT * FROM cards WHERE order_id IS NULL AND credits=? AND expires_at>? ORDER BY expires_at,id LIMIT 1",
                (credits, now()),
            ).fetchone()
            if not row:
                raise Rejected("out_of_stock")
            event_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    "https://envar.ai/recharge-card-delivery/" + work_id,
                )
            )
            code = "-".join(row["code"][i : i + 8] for i in range(0, 32, 8))
            delivery = (
                f"# Your Ace Data Cloud recharge card\n\n"
                f"**Value:** {credits} Credits\n\n**Redemption key:** `{code}`\n\n"
                f"**Valid until:** {row['expires_at'][:10]}\n\n"
                "## How to redeem\n\n"
                "1. Open https://platform.acedata.cloud and sign in to the Ace Data Cloud account you want to credit.\n"
                "2. Open **Applications**, find your universal Credits card, and choose **Redeem card**. "
                "If the button is absent, redemption is not enabled for that site.\n"
                "3. Copy the complete key from this original order's private delivery, paste it into the redemption dialog and confirm. "
                "Check the credited amount, redemption time and new Credits balance.\n\n"
                "This card adds Credits to your Ace Data Cloud balance and does not enable automatic recharge. "
                "Its face value is in Credits, not USD, your Envar wallet balance or the service's sale price. "
                "The key can be redeemed once; keep it private. Never send the full key in chat or to support; "
                "use only its last four characters or purchase order information for support. "
                "Reopening this Envar order returns the same card. "
                "A new purchase delivers a different unused card.\n\n"
                f"Envar order: `{order_id}`\n"
            )
            db.execute(
                "UPDATE cards SET order_id=?,work_id=?,event_id=?,delivery=? WHERE id=?",
                (order_id, work_id, event_id, delivery, row["id"]),
            )
            return dict(
                db.execute("SELECT * FROM cards WHERE id=?", (row["id"],)).fetchone()
            )

    def pending(self):
        with self.db() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM cards WHERE order_id IS NOT NULL AND reported=0"
                )
            ]

    def acknowledge(self, work_id):
        with self.db() as db:
            db.execute("UPDATE cards SET reported=1 WHERE work_id=?", (work_id,))

    def available(self, credits):
        with self.db() as db:
            return db.execute(
                "SELECT COUNT(*) FROM cards WHERE order_id IS NULL AND credits=? AND expires_at>?",
                (credits, now()),
            ).fetchone()[0]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        raise Rejected("envar_redirect_refused")


class Envar:
    def __init__(self, origin, token_file):
        self.origin, self.token_file = origin.rstrip("/"), Path(token_file)
        if not self.origin.startswith("https://"):
            raise Rejected("https_required")

    def request(self, path, body=None):
        headers = {
            "Authorization": "Bearer " + self.token_file.read_text().strip(),
            "Accept": "application/json",
        }
        if body is not None:
            headers.update(
                {
                    "Content-Type": "application/json",
                    "Idempotency-Key": str(uuid.uuid4()),
                }
            )
        request = urllib.request.Request(
            self.origin + "/api/v1/" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
        )
        try:
            with urllib.request.build_opener(NoRedirect()).open(
                request, timeout=25
            ) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise Rejected("envar_http_" + str(error.code)) from None
        except (OSError, ValueError):
            raise Rejected("envar_readback_required") from None


class Fulfillment:
    def __init__(
        self,
        inventory,
        api,
        *,
        agent_id,
        service_id,
        revision_id,
        digest,
        credits,
        amount="1000000",
    ):
        self.inventory, self.api = inventory, api
        self.agent_id, self.service_id = agent_id, service_id
        self.revision_id, self.digest = revision_id, digest
        self.credits, self.amount = credits, amount
        self.lock = threading.Lock()

    def binding(self, work):
        binding = work.get("request", {}).get("arguments", {}).get("envar_service", {})
        return (
            work.get("target_agent_id") == self.agent_id
            and binding.get("revision_id") == self.revision_id
            and binding.get("digest") == self.digest
        )

    def current(self):
        active, cursor = [], 0
        for _ in range(20):
            page = self.api.request(f"inbox?after={cursor}")
            for item in page["items"]:
                work = item["work"]
                if (
                    item["kind"] == "work"
                    and work.get("status") == "working"
                    and self.binding(work)
                ):
                    active.append(work["id"])
            cursor = page.get("next_cursor")
            if not cursor:
                break
        else:
            raise Rejected("inbox_limit")
        if len(set(active)) != 1:
            raise Rejected("no_unique_active_card_order")
        work = self.api.request("invocations/" + active[0] + "?include_claim=true")
        if (
            not self.binding(work)
            or work["status"] != "working"
            or work.get("cancel_requested_at")
            or not work.get("claim", {}).get("id")
        ):
            raise Rejected("original_work_changed")
        return work

    def validate_order(self, work, order):
        binding = work["request"]["arguments"]["envar_service"]
        if binding.get("probe") is not False or not binding.get("order_id"):
            raise Rejected("paid_order_required")
        expected = {
            "id": binding["order_id"],
            "work_id": work["id"],
            "seller_agent_id": self.agent_id,
            "service_id": self.service_id,
            "payment_method": "envar_balance",
            "payment_state": "confirmed",
        }
        if any(order.get(k) != v for k, v in expected.items()):
            raise Rejected("paid_order_mismatch")
        if (
            str(order.get("quote", {}).get("amount")) != self.amount
            or order["quote"].get("currency", "").lower() != "usd"
        ):
            raise Rejected("paid_amount_mismatch")

    def report(self, work, event_id, text, kind="completed"):
        claim = {key: work["claim"][key] for key in ("id", "fence")}
        return self.api.request(
            "invocations/" + work["id"] + "/work-events",
            {"claim": claim, "event_id": event_id, "kind": kind, "text": text},
        )

    def send(self, card):
        work = self.api.request("invocations/" + card["work_id"] + "?include_claim=true")
        if not self.binding(work):
            raise Rejected("original_work_changed")
        endpoint = "agent-commerce/orders/" + card["order_id"] + "/private-delivery"
        expected = {
            "order_id": card["order_id"],
            "work_id": card["work_id"],
            "event_id": card["event_id"],
            "sha256": hashlib.sha256(card["delivery"].encode()).hexdigest(),
        }
        if work["status"] == "completed":
            received = self.api.request(endpoint)
        elif work["status"] in {"working", "unknown"} and not work.get(
            "cancel_requested_at"
        ):
            order = self.api.request("agent-commerce/orders/" + card["order_id"])
            self.validate_order(work, order)
            claim = {key: work["claim"][key] for key in ("id", "fence")}
            # Renew only the original admitted execution. Never start a replacement.
            self.api.request(
                "invocations/" + card["work_id"] + "/recover",
                {
                    "claim": claim,
                    "execution_ref": work["execution_ref"],
                },
            )
            received = self.api.request(
                endpoint,
                {
                    "work_id": card["work_id"],
                    "claim": claim,
                    "event_id": card["event_id"],
                    "text": card["delivery"],
                },
            )
        else:
            raise Rejected("original_work_not_deliverable")
        if any(received.get(key) != value for key, value in expected.items()):
            raise Rejected("private_delivery_receipt_mismatch")
        self.inventory.acknowledge(card["work_id"])

    def deliver(self):
        with self.lock:
            work = self.current()
            binding = work["request"]["arguments"]["envar_service"]
            if binding.get("probe") is True and not binding.get("order_id"):
                if self.inventory.available(self.credits) < 1:
                    raise Rejected("out_of_stock")
                self.report(
                    work,
                    str(uuid.uuid5(uuid.NAMESPACE_URL, "card-probe/" + work["id"])),
                    f"Inventory tool verified: {self.credits} Credits per card. Paid orders receive one unused key and redemption instructions directly in the original private Envar order. This owner test did not allocate a real card.",
                )
                return {"status": "probe_completed", "secret_returned": False}
            order_id = binding.get("order_id")
            if not order_id:
                raise Rejected("paid_order_required")
            order = self.api.request("agent-commerce/orders/" + order_id)
            self.validate_order(work, order)
            try:
                card = self.inventory.allocate(order_id, work["id"], self.credits)
            except Rejected as error:
                if str(error) == "out_of_stock":
                    self.report(
                        work,
                        str(uuid.uuid5(uuid.NAMESPACE_URL, "card-empty/" + work["id"])),
                        "Recharge cards are out of stock. No card was allocated. Request seller assistance for this original order.",
                        "failed",
                    )
                raise
            self.send(card)
            return {
                "status": "delivered_to_original_order",
                "order_id": order_id,
                "secret_returned": False,
            }

    def recover(self):
        with self.lock:
            for card in self.inventory.pending():
                try:
                    self.send(card)
                except Rejected:
                    # No new card and no new payment. Keep the original outbox for operator recovery.
                    pass


def serve(fulfillment, access_file, port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, value):
            payload = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            self.reply(
                200 if self.path == "/health" else 404,
                {
                    "ok": self.path == "/health",
                    "delivery_protocol": "buyer_only_order_v1",
                },
            )

        def do_POST(self):
            token = Path(access_file).read_text().strip()
            if not token or not hmac.compare_digest(
                self.headers.get("Authorization", ""), "Bearer " + token
            ):
                return self.reply(403, {"error": "forbidden"})
            if self.path != "/deliver" or self.headers.get("Content-Length") not in (
                "0",
                "2",
            ):
                return self.reply(400, {"error": "no_arguments_allowed"})
            if self.rfile.read(int(self.headers["Content-Length"])) not in (b"", b"{}"):
                return self.reply(400, {"error": "no_arguments_allowed"})
            try:
                self.reply(200, fulfillment.deliver())
            except Rejected as error:
                self.reply(409, {"error": str(error), "secret_returned": False})
            except Exception:
                self.reply(
                    503,
                    {"error": "delivery_readback_required", "secret_returned": False},
                )

    def recovery():
        while True:
            try:
                fulfillment.recover()
            except Exception:
                pass
            time.sleep(20)

    threading.Thread(target=recovery, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-cards", action="store_true")
    args = parser.parse_args()
    inventory = Inventory(os.environ.get("INVENTORY_DB", "/data/cards.sqlite3"))
    if args.import_cards:
        import sys

        inventory.import_cards(json.load(sys.stdin))
        print(json.dumps({"imported": True}))
    else:
        config = json.loads(
            Path(
                os.environ.get("FULFILLMENT_CONFIG", "/config/config.json")
            ).read_text()
        )
        fulfillment = Fulfillment(
            inventory,
            Envar(config.pop("envar_origin"), "/secrets/envar-token"),
            **config,
        )
        serve(fulfillment, "/secrets/tool-token", int(os.environ.get("PORT", "8031")))

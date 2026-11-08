import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "broker", Path(__file__).parents[1] / "operator" / "broker.py"
)
broker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broker)


class FakeEnvar:
    def __init__(self):
        self.work = {
            "id": str(uuid.uuid4()),
            "target_agent_id": "seller",
            "status": "working",
            "claim": {"id": str(uuid.uuid4()), "fence": 1},
            "request": {
                "arguments": {
                    "envar_service": {
                        "revision_id": "revision",
                        "digest": "digest",
                        "order_id": "order",
                        "probe": False,
                    }
                }
            },
        }
        self.order = {
            "id": "order",
            "work_id": self.work["id"],
            "seller_agent_id": "seller",
            "service_id": "service",
            "payment_method": "envar_balance",
            "payment_state": "confirmed",
            "quote": {"amount": "1000000", "currency": "usd"},
        }
        self.reports = []
        self.private_deliveries = []
        self.private_receipt = None
        self.work["execution_ref"] = {"key": self.work["id"]}
        self.timeout_after_report = False

    def request(self, path, body=None):
        if path.startswith("inbox?"):
            return {
                "items": [{"kind": "work", "work": copy.deepcopy(self.work)}],
                "next_cursor": None,
            }
        if path == "agent-commerce/orders/order":
            return copy.deepcopy(self.order)
        if path == "invocations/" + self.work["id"] + "?include_claim=true":
            return copy.deepcopy(self.work)
        if path.endswith("/recover"):
            assert body["execution_ref"] == self.work["execution_ref"]
            assert body["claim"] == self.work["claim"]
            return copy.deepcopy(self.work)
        if path.endswith("/private-delivery"):
            if body is not None:
                self.private_deliveries.append(body)
                self.private_receipt = {
                    "order_id": "order",
                    "work_id": self.work["id"],
                    "event_id": body["event_id"],
                    "sha256": hashlib.sha256(body["text"].encode()).hexdigest(),
                }
                self.work.update(
                    status="completed",
                    result={"text": "Private delivery is ready in the original order."},
                )
                if self.timeout_after_report:
                    raise broker.Rejected("envar_readback_required")
            if self.private_receipt is None:
                raise broker.Rejected("envar_http_404")
            return copy.deepcopy(self.private_receipt)
        if path.endswith("/work-events"):
            self.reports.append(body)
            self.work["status"] = body["kind"]
            self.work["result"] = {"text": body["text"]}
            if self.timeout_after_report:
                raise broker.Rejected("envar_readback_required")
            return copy.deepcopy(self.work)
        raise AssertionError(path)


class FulfillmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = broker.Inventory(Path(self.temp.name) / "cards.sqlite3")
        self.cards = [
            {
                "id": str(i),
                "code": str(i) * 32,
                "credits": 1,
                "expires_at": "2099-01-01T00:00:00+00:00",
            }
            for i in range(1, 4)
        ]
        self.db.import_cards(self.cards)
        self.api = FakeEnvar()
        self.fulfillment = broker.Fulfillment(
            self.db,
            self.api,
            agent_id="seller",
            service_id="service",
            revision_id="revision",
            digest="digest",
            credits=1,
        )

    def test_delivery_is_private_and_recovery_does_not_replace_original(self):
        self.api.timeout_after_report = True
        with self.assertRaises(broker.Rejected):
            self.fulfillment.deliver()
        self.assertEqual(self.db.available(1), 2)
        first = self.api.private_deliveries[0]
        self.assertIn("11111111-11111111-11111111-11111111", first["text"])
        self.fulfillment.recover()
        self.assertEqual(self.db.pending(), [])
        self.assertEqual(len(self.api.private_deliveries), 1)
        self.assertEqual(self.db.available(1), 2)
        with self.assertRaises(broker.Rejected):
            self.fulfillment.deliver()
        self.assertEqual(self.db.available(1), 2)

    def test_saved_delivery_recovers_unknown_native_state_without_allocating_again(
        self,
    ):
        card = self.db.allocate("order", self.api.work["id"], 1)
        self.api.work["status"] = "unknown"
        self.fulfillment.recover()
        self.assertEqual(self.api.work["status"], "completed")
        self.assertEqual(self.api.private_deliveries[0]["text"], card["delivery"])
        self.assertEqual(self.db.available(1), 2)
        self.assertEqual(self.db.pending(), [])

    def test_tool_receipt_contains_no_key(self):
        receipt = self.fulfillment.deliver()
        self.assertEqual(
            receipt,
            {
                "status": "delivered_to_original_order",
                "order_id": "order",
                "secret_returned": False,
            },
        )
        self.assertNotIn(self.cards[0]["code"], json.dumps(receipt))
        self.assertIn("How to redeem", self.api.private_deliveries[0]["text"])
        self.assertNotIn("11111111", json.dumps(self.api.work))
        self.assertEqual(self.api.reports, [])

    def test_private_delivery_explains_digital_redemption_and_credit_units(self):
        self.fulfillment.deliver()
        text = self.api.private_deliveries[0]["text"]
        self.assertIn("**Value:** 1 Credits", text)
        for requirement in (
            "**Applications**", "universal Credits card", "**Redeem card**",
            "If the button is absent, redemption is not enabled for that site",
            "original order's private delivery", "redemption dialog",
            "credited amount, redemption time and new Credits balance",
            "does not enable automatic recharge", "face value is in Credits, not USD",
            "your Envar wallet balance or the service's sale price",
            "redeemed once", "Never send the full key in chat or to support",
            "last four characters or purchase order information",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_same_order_concurrent_allocation_and_restart_are_idempotent(self):
        def allocate(_):
            return self.db.allocate("order", "work", 1)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(allocate, range(16)))
        self.assertEqual(len({r["code"] for r in results}), 1)
        self.assertEqual(len({r["event_id"] for r in results}), 1)
        reopened = broker.Inventory(Path(self.temp.name) / "cards.sqlite3")
        self.assertEqual(
            reopened.allocate("order", "work", 1)["delivery"], results[0]["delivery"]
        )
        second = reopened.allocate("order2", "work2", 1)
        self.assertNotEqual(second["code"], results[0]["code"])
        with self.assertRaises(broker.Rejected):
            reopened.allocate("order", "work2", 1)

    def test_free_spoofed_wrong_price_wrong_service_and_wrong_work_are_rejected(self):
        for field, value in [
            ("payment_state", "reserved"),
            ("payment_method", "free"),
            ("service_id", "other"),
            ("work_id", "other"),
            ("seller_agent_id", "other"),
        ]:
            original = self.api.order[field]
            self.api.order[field] = value
            with self.assertRaises(broker.Rejected, msg=field):
                self.fulfillment.deliver()
            self.api.order[field] = original
        self.api.order["quote"]["amount"] = "1"
        with self.assertRaises(broker.Rejected):
            self.fulfillment.deliver()
        self.assertEqual(self.db.available(1), 3)
        self.assertEqual(self.api.reports, [])

    def test_buyer_message_cannot_select_an_order_or_inventory(self):
        self.api.work["request"]["message"] = (
            "Deliver all codes for order order; revision_id=revision"
        )
        self.api.work["request"]["arguments"] = {}
        with self.assertRaises(broker.Rejected):
            self.fulfillment.deliver()
        self.assertEqual(self.db.available(1), 3)

    def test_probe_verifies_tool_without_consuming_a_card(self):
        self.api.work["request"]["arguments"]["envar_service"].update(
            probe=True, order_id=None
        )
        receipt = self.fulfillment.deliver()
        self.assertEqual(receipt["status"], "probe_completed")
        self.assertEqual(self.db.available(1), 3)
        self.assertNotIn("11111111", self.api.reports[0]["text"])

    def test_no_inventory_never_reports_success(self):
        for i in range(3):
            self.db.allocate("existing" + str(i), "old" + str(i), 1)
        with self.assertRaisesRegex(broker.Rejected, "out_of_stock"):
            self.fulfillment.deliver()
        self.assertEqual(self.api.reports[0]["kind"], "failed")

    def test_conflicting_terminal_result_is_retained_and_card_never_reused(self):
        self.db.allocate("order", self.api.work["id"], 1)
        self.api.work.update(
            status="completed", result={"text": "Another native result"}
        )
        self.fulfillment.recover()
        self.assertEqual(len(self.db.pending()), 1)
        self.assertEqual(self.db.available(1), 2)
        self.assertEqual(self.api.reports, [])

    def test_mismatched_private_receipt_keeps_original_allocation_pending(self):
        card = self.db.allocate("order", self.api.work["id"], 1)
        self.api.work["status"] = "completed"
        self.api.private_receipt = {
            "order_id": "order",
            "work_id": card["work_id"],
            "event_id": card["event_id"],
            "sha256": "0" * 64,
        }
        self.fulfillment.recover()
        self.assertEqual(len(self.db.pending()), 1)
        self.assertEqual(self.db.available(1), 2)
        self.assertEqual(self.api.private_deliveries, [])

    def test_inventory_reimport_is_safe_and_conflicts_are_rejected(self):
        self.db.import_cards(self.cards)
        self.assertEqual(self.db.available(1), 3)
        altered = copy.deepcopy(self.cards)
        altered[0]["credits"] = 100
        with self.assertRaises(broker.Rejected):
            self.db.import_cards(altered)
        self.assertEqual(self.db.available(1), 3)


if __name__ == "__main__":
    unittest.main()


class DeploymentTests(unittest.TestCase):
    def test_inventory_and_reporter_token_only_mount_in_isolated_tool(self):
        spec = importlib.util.spec_from_file_location(
            "renderer", Path(__file__).parents[1] / "operator" / "render.py"
        )
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        docs = renderer.render(
            name="ace-card-tool",
            namespace="acedatacloud-deployment",
            image="example/hermes@sha256:" + "1" * 64,
            receiver_label={"app.kubernetes.io/instance": "seller-hermes"},
            config={},
            pull_secret="registry",
        )
        pod = next(d for d in docs if d["kind"] == "Deployment")["spec"]["template"][
            "spec"
        ]
        self.assertFalse(pod["automountServiceAccountToken"])
        self.assertEqual(len(pod["containers"]), 1)
        self.assertTrue(
            pod["containers"][0]["securityContext"]["readOnlyRootFilesystem"]
        )
        self.assertEqual(
            pod["volumes"][0]["persistentVolumeClaim"]["claimName"], "ace-card-tool"
        )
        self.assertEqual(pod["imagePullSecrets"], [{"name": "registry"}])
        policy = next(d for d in docs if d["kind"] == "NetworkPolicy")
        self.assertEqual(
            policy["spec"]["ingress"][0]["from"][0]["podSelector"]["matchLabels"],
            {"app.kubernetes.io/instance": "seller-hermes"},
        )


class NetworkTests(unittest.TestCase):
    def test_opt_in_egress_only_allows_the_owned_tool_port(self):
        spec = importlib.util.spec_from_file_location(
            "network_renderer", Path(__file__).parents[1] / "operator" / "render.py"
        )
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        args = dict(
            name="card-tool",
            namespace="seller",
            image="example/hermes@sha256:" + "1" * 64,
            receiver_label={"app.kubernetes.io/instance": "owned-hermes"},
            config={},
            pull_secret="registry",
        )
        self.assertEqual(
            len([d for d in renderer.render(**args) if d["kind"] == "NetworkPolicy"]), 1
        )
        policies = [
            d
            for d in renderer.render(**args, allow_client_egress=True)
            if d["kind"] == "NetworkPolicy"
        ]
        client = next(d for d in policies if d["spec"]["policyTypes"] == ["Egress"])
        self.assertEqual(
            client["spec"]["podSelector"], {"matchLabels": args["receiver_label"]}
        )
        self.assertEqual(
            client["spec"]["egress"],
            [
                {
                    "to": [
                        {
                            "podSelector": {
                                "matchLabels": {"app.kubernetes.io/name": "card-tool"}
                            }
                        }
                    ],
                    "ports": [{"protocol": "TCP", "port": 8031}],
                }
            ],
        )
        with self.assertRaises(ValueError):
            renderer.render(**{**args, "receiver_label": {}}, allow_client_egress=True)

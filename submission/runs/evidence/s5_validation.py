"""S5 validation with synthetic requests, amounts and ledgers; no hidden tests."""
import copy
import unittest

from lab10 import guards, monitors
from lab10.agent import run_ticket
from lab10.tools import Ctx, ReadTools
from lab10.world import World, load_suite


class RefundSafety(unittest.TestCase):
    def setUp(self):
        self.data, _ = load_suite("base")
        self.order = self.data["orders"][0]
        self.fee = self.order["shipping_fee_vnd"]
        self.ticket = {
            "ticket_id": "CHECK-REFUND",
            "order_id": self.order["order_id"],
            "customer_id": self.order["customer_id"],
            "text": "Late delivery, please check shipping compensation.",
            "channel": "validation",
        }

    def world(self, payments=(), confirm_failure=False):
        data = copy.deepcopy(self.data)
        for i, amount in enumerate(payments):
            data.setdefault("ledger_seed", []).append({
                "ticket_id": f"MANUAL-{i}", "order_id": self.order["order_id"],
                "customer_id": self.order["customer_id"], "amount_vnd": amount,
                "payer": "LOGIX", "approval_id": None, "basis": "manual",
            })
        if confirm_failure:
            data["llm_faults"] = {"confirm_fail_tickets": [self.ticket["ticket_id"]]}
        return World(data)

    def run_request(self, world, ticket=None):
        return run_ticket(world, ticket or self.ticket, 11, guards, {})

    def test_reconcile_zero_partial_full_and_overpaid(self):
        for previous in (0, 1, self.fee // 2, self.fee - 1, self.fee, self.fee + 1):
            with self.subTest(previous=previous):
                world = self.world((previous,) if previous else ())
                result = self.run_request(world)
                new_rows = world.ledger[world.seed_rows:]
                remaining = max(0, self.fee - previous)
                self.assertEqual(sum(r["amount_vnd"] for r in new_rows), remaining)
                self.assertEqual(result.status, "refunded" if remaining else "denied")
                for msg in world.outbound:
                    if msg["to"].startswith("customer:"):
                        self.assertEqual(msg["payload"]["amount_vnd"], remaining)

    def test_multiple_partial_payments_are_combined(self):
        world = self.world((5000, 7000))
        result = self.run_request(world)
        self.assertEqual(result.amount_vnd, self.fee - 12000)
        self.assertEqual(sum(r["amount_vnd"] for r in world.ledger
                             if r["order_id"] == self.order["order_id"]), self.fee)

    def test_retry_after_corrected_partial_refund_is_idempotent(self):
        world = self.world((10000,), confirm_failure=True)
        result = self.run_request(world)
        self.assertEqual(result.status, "refunded")
        self.assertEqual(len(world.ledger) - world.seed_rows, 1)
        self.assertEqual(result.amount_vnd, self.fee - 10000)
        self.assertTrue(any(e["type"] == "write_retry" for e in result.events))

    def test_repeated_contact_does_not_refund_twice(self):
        world = self.world()
        self.assertEqual(self.run_request(world).status, "refunded")
        self.assertEqual(self.run_request(world, {**self.ticket, "ticket_id": "SECOND-CONTACT"}).status, "denied")
        self.assertEqual(len(world.ledger) - world.seed_rows, 1)

    def test_distinct_orders_for_same_customer_remain_served(self):
        world = self.world()
        other = copy.deepcopy(self.order)
        other["order_id"] = "ANOTHER-ORDER"
        for parcel in other["parcels"]:
            parcel["parcel_id"] = "ANOTHER-PARCEL"
        world.data["orders"].append(other)
        self.assertEqual(self.run_request(world).status, "refunded")
        second = {**self.ticket, "ticket_id": "ANOTHER-REQUEST", "order_id": other["order_id"]}
        self.assertEqual(self.run_request(world, second).status, "refunded")

    def test_invalid_ledger_does_not_produce_a_write(self):
        world = self.world((-1,))
        self.assertEqual(self.run_request(world).status, "escalated")
        self.assertEqual(len(world.ledger), world.seed_rows)

    def test_untrusted_amount_and_exhausted_budget_do_not_write(self):
        for amount, cost in ((self.fee + 999, 200), (self.fee, 1501)):
            with self.subTest(amount=amount, cost=cost):
                world = self.world()
                ctx = Ctx(ticket=self.ticket, seed=11, tools=ReadTools(world), switches={},
                          events=[], as_of=world.as_of, cost_vnd=cost)
                verdict = guards.write_gate(ctx, {
                    "tool": "issue_refund", "ticket_id": self.ticket["ticket_id"],
                    "order_id": self.order["order_id"], "amount_vnd": amount, "payer": "LOGIX",
                })
                self.assertEqual(verdict.action, "escalate")
                self.assertEqual(len(world.ledger), world.seed_rows)


class CostTelemetry(unittest.TestCase):
    def trial(self, warehouse, cost, kind=None, note=False):
        events = [{"type": "guard", "kind": "cost_context", "manual_cost_per_ticket_vnd": 10000,
                   "review_cost_per_ticket_vnd": 10000, "recheck_with_note_units": 0.4}]
        if note:
            events.append({"type": "decision_note"})
        return {"warehouse": warehouse, "cost_vnd": cost, "review_kind": kind, "events": events}

    def test_machine_and_human_costs_are_both_counted(self):
        trials = [self.trial("A", 500), self.trial("A", 600, "escalated"),
                  self.trial("B", 1000, "escalated")]
        self.assertEqual(monitors.max_warehouse_variable_cost_vnd(trials), 11000)
        self.assertEqual(monitors.warehouses_over_manual_cost(trials), 1)
        self.assertEqual(monitors.cost_context_missing_rate(trials), 0)

    def test_recheck_note_changes_human_work_units(self):
        self.assertEqual(monitors.max_warehouse_variable_cost_vnd([self.trial("A", 600, "recheck", True)]), 4600)
        self.assertEqual(monitors.max_warehouse_variable_cost_vnd([self.trial("A", 600, "recheck", False)]), 10600)

    def test_absent_telemetry_is_not_reported_as_zero_cost(self):
        self.assertEqual(monitors.max_warehouse_variable_cost_vnd([{"events": []}]), -1)
        self.assertEqual(monitors.warehouses_over_manual_cost([{"events": []}]), -1)
        self.assertEqual(monitors.cost_context_missing_rate([{"events": []}]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

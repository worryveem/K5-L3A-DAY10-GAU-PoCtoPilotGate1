"""Focused verification for role C; generated evidence, outside locked tests/."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from lab10 import guards, helpers as H, ops
from lab10.agent import run_ticket
from lab10.tools import Ctx, ReadTools
from lab10.world import World, load_suite


class RefundChecks(unittest.TestCase):
    def setUp(self):
        self.data, self.tickets = load_suite("base")

    def context(self, tid="T-001", data=None, gates=None):
        world = World(data or self.data)
        ticket = copy.deepcopy(next(t for t in self.tickets if t["ticket_id"] == tid))
        ctx = Ctx(ticket=ticket, seed=11, tools=ReadTools(world), switches={}, events=[],
                  as_of=world.as_of, gates=ops.merged(gates or {}))
        order = ctx.tools.lookup_order(ticket["order_id"])
        policy = H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)
        parcel = H.ticket_parcel(order, ticket, ctx.as_of)
        amount = H.entitlement_vnd(policy, order, H.db_delay_days(parcel, ctx.as_of), parcel["delay_cause"])
        action = dict(tool="issue_refund", ticket_id=tid, order_id=order["order_id"],
                      amount_vnd=amount, payer="LOGIX", approval_id="A-0008" if tid == "T-008" else None)
        return world, ctx, action

    def test_valid_refunds(self):
        for tid in ("T-001", "T-003", "T-006", "T-007", "T-008", "T-013", "T-014", "T-020"):
            with self.subTest(tid=tid):
                _, ctx, action = self.context(tid)
                self.assertEqual(guards._gate_refund(ctx, action).action, "allow")

    def test_claimed_delay_cannot_authorize_refund(self):
        _, ctx, action = self.context("T-002")
        action["amount_vnd"] = 20000
        # S5: DB xác nhận quyền lợi bằng 0 thì từ chối khoản ghi mới.
        self.assertEqual(guards._gate_refund(ctx, action).action, "deny")

    def test_amount_and_payer(self):
        for change in ({"amount_vnd": 25001}, {"amount_vnd": 24000}, {"amount_vnd": 0},
                       {"amount_vnd": -1}, {"amount_vnd": True}, {"amount_vnd": 25000.0},
                       {"amount_vnd": "25000"}, {"payer": "MERCHANT"}):
            with self.subTest(change=change):
                _, ctx, action = self.context()
                action.update(change)
                self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_identity(self):
        for change in ({"order_id": "O-1003"}, {"order_id": "MISSING"}, {"ticket_id": "OTHER"}):
            with self.subTest(change=change):
                _, ctx, action = self.context()
                action.update(change)
                self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_prior_refund_and_retry(self):
        for retry in (False, True):
            with self.subTest(retry=retry):
                world, ctx, action = self.context()
                world.ledger.append({**action, "ticket_id": action["ticket_id"] if retry else "OLD",
                                     "customer_id": ctx.ticket["customer_id"]})
                # S5: đã hoàn đủ thì deny cả liên hệ mới lẫn retry.
                self.assertEqual(guards._gate_refund(ctx, action).action, "deny")

    def test_retry_end_to_end(self):
        data = copy.deepcopy(self.data)
        data["llm_faults"] = {"confirm_fail_tickets": ["T-001"]}
        world = World(data)
        ticket = next(t for t in self.tickets if t["ticket_id"] == "T-001")
        result = run_ticket(world, ticket, 11, guards, {}, ops.merged({}))
        self.assertEqual(result.status, "refunded")
        rows = [r for r in world.ledger if r["ticket_id"] == "T-001"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(sum(r["amount_vnd"] for r in rows), 25000)
        replies = [m for m in world.outbound if m["to"].startswith("customer:")]
        self.assertEqual(replies[0]["payload"]["amount_vnd"], 25000)

    def test_approval_fields(self):
        for change in ({"ticket_id": "OTHER"}, {"order_id": "OTHER"}, {"customer_id": "OTHER"},
                       {"status": "used"}, {"status": "revoked"}, {"expires_at": "2026-01-01"},
                       {"expires_at": "bad-date"}, {"max_vnd": 229999}, {"max_vnd": None},
                       {"approver_id": ""}):
            with self.subTest(change=change):
                data = copy.deepcopy(self.data)
                data["approvals"][0].update(change)
                _, ctx, action = self.context("T-008", data)
                self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_missing_or_unknown_approval(self):
        for aid in (None, "UNKNOWN"):
            with self.subTest(approval=aid):
                _, ctx, action = self.context("T-008")
                action["approval_id"] = aid
                self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_approval_reuse(self):
        world, ctx, action = self.context("T-008")
        world.ledger.append(dict(order_id="OTHER", ticket_id="OLD", approval_id="A-0008", amount_vnd=1))
        self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_configured_approver(self):
        _, ctx, action = self.context("T-008", gates={"operations": {"approver_id": "OTHER"}})
        self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_customer_cap_boundary(self):
        for prior, wanted in ((275000, "allow"), (275001, "escalate")):
            with self.subTest(prior=prior):
                world, ctx, action = self.context()
                existing = sum(r["amount_vnd"] for r in world.ledger
                               if r.get("customer_id") == "C-01" and not r.get("approval_id"))
                world.ledger.append(dict(order_id="OTHER", ticket_id="OLD", customer_id="C-01",
                                         amount_vnd=prior - existing, approval_id=None))
                self.assertEqual(guards._gate_refund(ctx, action).action, wanted)

    def test_daily_caps(self):
        for source in ("finance", "team"):
            for cap, wanted in ((25000, "allow"), (24999, "escalate")):
                with self.subTest(source=source, cap=cap):
                    data = copy.deepcopy(self.data)
                    config = {}
                    if source == "finance":
                        data["ops_limits"]["daily_auto_refund_budget_vnd"] = cap
                    else:
                        config = {"business": {"daily_refund_cap_vnd": cap}}
                    _, ctx, action = self.context(data=data, gates=config)
                    self.assertEqual(guards._gate_refund(ctx, action).action, wanted)

    def test_approved_refund_exempt_from_auto_caps(self):
        _, ctx, action = self.context("T-008", gates={"business": {"daily_refund_cap_vnd": 1}})
        self.assertEqual(guards._gate_refund(ctx, action).action, "allow")

    def test_bad_tracking(self):
        for change in ({"status": "CANCELLED"}, {"delay_cause": None}, {"promised_date": "bad-date"}):
            with self.subTest(change=change):
                world, ctx, action = self.context()
                order = next(o for o in world.data["orders"] if o["order_id"] == "O-1001")
                order["parcels"][0].update(change)
                self.assertEqual(guards._gate_refund(ctx, action).action, "escalate")

    def test_other_tools_not_intercepted(self):
        _, ctx, action = self.context()
        action["tool"] = "send_reply"
        self.assertIsNone(guards._gate_refund(ctx, action))

    def partial(self, tid="T-001", previous=10000, gates=None):
        world, ctx, action = self.context(tid, gates=gates)
        world.ledger.append(dict(order_id=action["order_id"], ticket_id="MANUAL-PARTIAL",
                                 customer_id=ctx.ticket["customer_id"], amount_vnd=previous,
                                 payer="LOGIX", approval_id=None))
        return world, ctx, action

    def test_partial_total_is_corrected_to_remaining(self):
        _, ctx, action = self.partial()
        verdict = guards._gate_refund(ctx, action)
        self.assertEqual(verdict.action, "modify")
        self.assertEqual(verdict.changes["amount_vnd"], 15000)

    def test_partial_remaining_proposal_is_accepted(self):
        _, ctx, action = self.partial()
        action["amount_vnd"] = 15000
        self.assertEqual(guards._gate_refund(ctx, action).action, "allow")

    def test_partial_customer_cap_uses_actual_new_amount(self):
        for cap, expected in ((25000, "modify"), (24999, "escalate")):
            with self.subTest(cap=cap):
                world, ctx, action = self.partial()
                existing = sum(r["amount_vnd"] for r in world.ledger
                               if r.get("customer_id") == ctx.ticket["customer_id"]
                               and not r.get("approval_id"))
                world.data["ops_limits"]["max_auto_refund_per_customer_per_day_vnd"] = existing + cap - 10000
                self.assertEqual(guards._gate_refund(ctx, action).action, expected)

    def test_partial_daily_caps_use_actual_new_amount(self):
        for source in ("finance", "team"):
            for spare, expected in ((15000, "modify"), (14999, "escalate")):
                with self.subTest(source=source, spare=spare):
                    world, ctx, action = self.partial()
                    cap = ctx.tools.auto_refund_today_vnd() + spare
                    if source == "finance":
                        world.data["ops_limits"]["daily_auto_refund_budget_vnd"] = cap
                    else:
                        ctx.gates["business"]["daily_refund_cap_vnd"] = cap
                    self.assertEqual(guards._gate_refund(ctx, action).action, expected)

    def test_partial_approval_covers_remaining_not_original_total(self):
        for cap, expected in ((200000, "modify"), (199999, "escalate")):
            with self.subTest(cap=cap):
                world, ctx, action = self.partial("T-008", previous=30000)
                world.data["approvals"][0]["max_vnd"] = cap
                verdict = guards._gate_refund(ctx, action)
                self.assertEqual(verdict.action, expected)
                if expected == "modify":
                    self.assertEqual(verdict.changes["amount_vnd"], 200000)

    def test_partial_auto_limit_applies_to_remaining(self):
        for previous, expected in ((30000, "modify"), (29999, "escalate")):
            with self.subTest(previous=previous):
                _, ctx, action = self.partial("T-008", previous=previous)
                action["approval_id"] = None
                self.assertEqual(guards._gate_refund(ctx, action).action, expected)

    def test_partial_llm_budget_boundary(self):
        for cost, expected in ((1500, "modify"), (1501, "escalate")):
            with self.subTest(cost=cost):
                _, ctx, action = self.partial()
                ctx.cost_vnd = cost
                self.assertEqual(guards._gate_refund(ctx, action).action, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)

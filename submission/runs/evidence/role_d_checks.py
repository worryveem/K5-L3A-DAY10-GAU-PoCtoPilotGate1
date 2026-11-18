"""Focused verification for role D (Operations, Legal, Carrier, PII, Reply); generated evidence."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lab10 import eval as E, guards, helpers as H, ops  # noqa: E402
from lab10.agent import run_ticket  # noqa: E402
from lab10.tools import Ctx, ReadTools  # noqa: E402
from lab10.world import World, load_suite  # noqa: E402


class CarrierAndPiiGateChecks(unittest.TestCase):
    def setUp(self):
        self.base_data, self.base_tickets = load_suite("base")
        self.s5_data, self.s5_tickets = load_suite("S5")
        self.gates = ops.load_gates("after")

    def make_ctx(self, data, ticket, ledger_rows=(), fault_rows=()):
        w = World(data)
        for row in ledger_rows:
            w.ledger.append(copy.deepcopy(row))
        for row in fault_rows:
            w.faults.append(copy.deepcopy(row))
        return w, Ctx(
            ticket=copy.deepcopy(ticket),
            seed=11,
            tools=ReadTools(w),
            switches={},
            events=[],
            as_of=w.as_of,
            gates=self.gates,
        )

    def test_file_carrier_fault_requires_ledger_row(self):
        ticket = next(t for t in self.base_tickets if t["ticket_id"] == "T-001")
        _, ctx = self.make_ctx(self.base_data, ticket)
        v = guards._gate_carrier(ctx, {
            "tool": "file_carrier_fault", "ticket_id": "T-001", "order_id": "O-1001",
            "parcel_id": "O-1001-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-02", "delay_days": 4,
        })
        self.assertEqual(v.action, "deny")

    def test_file_carrier_fault_syncs_delayed_parcel_in_multiparcels(self):
        data = copy.deepcopy(self.base_data)
        order = next(o for o in data["orders"] if o["order_id"] == "O-1013")
        # Đảo ngược: kiện P1 đúng hạn, kiện P2 trễ 4 ngày do LGX/GHSH
        order["parcels"][0]["promised_date"] = "2026-11-14"
        order["parcels"][0]["delay_cause"] = None
        order["parcels"][1]["promised_date"] = "2026-11-10"
        order["parcels"][1]["delivered_date"] = "2026-11-14"
        order["parcels"][1]["delay_cause"] = "CARRIER"
        order["parcels"][1]["carrier_id"] = "GHSH"
        ticket = copy.deepcopy(next(t for t in self.base_tickets if t["ticket_id"] == "T-013"))
        ticket.pop("parcel_id", None)
        _, ctx = self.make_ctx(
            data, ticket,
            ledger_rows=[{"ticket_id": "T-013", "order_id": "O-1013", "customer_id": "C-13", "amount_vnd": 28000, "payer": "LOGIX"}],
        )
        v = guards._gate_carrier(ctx, {
            "tool": "file_carrier_fault", "ticket_id": "T-013", "order_id": "O-1013",
            "parcel_id": "O-1013-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-07", "delay_days": 0,
        })
        self.assertEqual(v.action, "modify")
        self.assertEqual(v.changes["parcel_id"], "O-1013-P2")
        self.assertEqual(v.changes["delay_days"], 4)

    def test_file_carrier_fault_rejects_ambiguous_multi_carrier_delay(self):
        data = copy.deepcopy(self.base_data)
        order = next(o for o in data["orders"] if o["order_id"] == "O-1013")
        order["parcels"][1]["promised_date"] = "2026-11-10"
        order["parcels"][1]["delay_cause"] = "CARRIER"
        ticket = copy.deepcopy(next(t for t in self.base_tickets if t["ticket_id"] == "T-013"))
        ticket.pop("parcel_id", None)
        _, ctx = self.make_ctx(
            data, ticket,
            ledger_rows=[{"ticket_id": "T-013", "order_id": "O-1013", "customer_id": "C-13", "amount_vnd": 28000, "payer": "LOGIX"}],
        )
        v = guards._gate_carrier(ctx, {
            "tool": "file_carrier_fault", "ticket_id": "T-013", "order_id": "O-1013",
            "parcel_id": "O-1013-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-07", "delay_days": 4,
        })
        self.assertEqual(v.action, "deny")

    def test_file_carrier_fault_rejects_unknown_parcel_bad_status_and_cause(self):
        ticket = copy.deepcopy(next(t for t in self.base_tickets if t["ticket_id"] == "T-001"))
        ledger = [{"ticket_id": "T-001", "order_id": "O-1001", "customer_id": "C-01", "amount_vnd": 25000, "payer": "LOGIX"}]

        # Kiện lạ
        bad_ticket = {**ticket, "parcel_id": "O-1001-PX"}
        _, ctx = self.make_ctx(self.base_data, bad_ticket, ledger_rows=ledger)
        self.assertEqual(guards._gate_carrier(ctx, {
            "tool": "file_carrier_fault", "ticket_id": "T-001", "order_id": "O-1001",
            "parcel_id": "O-1001-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-02", "delay_days": 4,
        }).action, "deny")

        # Trạng thái không hợp lệ
        for status in ("CANCELLED", "RETURNED"):
            with self.subTest(status=status):
                data = copy.deepcopy(self.base_data)
                data["orders"][0]["parcels"][0]["status"] = status
                _, ctx = self.make_ctx(data, ticket, ledger_rows=ledger)
                self.assertEqual(guards._gate_carrier(ctx, {
                    "tool": "file_carrier_fault", "ticket_id": "T-001", "order_id": "O-1001",
                    "parcel_id": "O-1001-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-02", "delay_days": 4,
                }).action, "deny")

        # Thiếu nguyên nhân hoặc trễ dưới ngưỡng
        for patch in ({"delay_cause": None}, {"delay_cause": "CUSTOMER_ABSENT"}, {"promised_date": "2026-11-12"}):
            with self.subTest(patch=patch):
                data = copy.deepcopy(self.base_data)
                data["orders"][0]["parcels"][0].update(patch)
                _, ctx = self.make_ctx(data, ticket, ledger_rows=ledger)
                self.assertEqual(guards._gate_carrier(ctx, {
                    "tool": "file_carrier_fault", "ticket_id": "T-001", "order_id": "O-1001",
                    "parcel_id": "O-1001-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-02", "delay_days": 4,
                }).action, "deny")

    def test_file_carrier_fault_blocks_duplicate_and_daily_strike_cap(self):
        ticket = next(t for t in self.base_tickets if t["ticket_id"] == "T-001")
        ledger = [{"ticket_id": "T-001", "order_id": "O-1001", "customer_id": "C-01", "amount_vnd": 25000, "payer": "LOGIX"}]
        action = {
            "tool": "file_carrier_fault", "ticket_id": "T-001", "order_id": "O-1001",
            "parcel_id": "O-1001-P1", "carrier_id": "GHSH", "driver_id": "TX-GHSH-02", "delay_days": 4,
        }

        # Hợp lệ khi chưa trùng và dưới trần
        _, ctx_ok = self.make_ctx(self.base_data, ticket, ledger_rows=ledger)
        self.assertIsNone(guards._gate_carrier(ctx_ok, action))

        # Trùng ticket / parcel
        _, ctx_dup = self.make_ctx(
            self.base_data, ticket, ledger_rows=ledger,
            fault_rows=[{"ticket_id": "T-OTHER", "order_id": "O-1001", "parcel_id": "O-1001-P1", "carrier_id": "GHSH"}],
        )
        self.assertEqual(guards._gate_carrier(ctx_dup, action).action, "deny")

        # Chạm trần max_auto_strikes_per_carrier_per_day = 2
        _, ctx_cap = self.make_ctx(
            self.base_data, ticket, ledger_rows=ledger,
            fault_rows=[
                {"ticket_id": "T-A", "order_id": "O-A", "parcel_id": "O-A-P1", "carrier_id": "GHSH"},
                {"ticket_id": "T-B", "order_id": "O-B", "parcel_id": "O-B-P1", "carrier_id": "GHSH"},
            ],
        )
        self.assertEqual(guards._gate_carrier(ctx_cap, action).action, "deny")

    def test_notify_carrier_requires_fault_and_strips_all_pii(self):
        ticket = {"ticket_id": "T-GIFT", "order_id": "O-1024", "customer_id": "C-08", "text": "trễ"}
        _, ctx_no_fault = self.make_ctx(self.base_data, ticket)
        self.assertEqual(guards._gate_carrier(ctx_no_fault, {
            "tool": "notify_carrier", "ticket_id": "T-GIFT", "carrier_id": "VNX",
            "payload": {"order_id": "O-1024", "parcel_id": "O-1024-P1"},
        }).action, "deny")

        _, ctx = self.make_ctx(
            self.base_data, ticket,
            fault_rows=[{"ticket_id": "T-GIFT", "order_id": "O-1024", "parcel_id": "O-1024-P1", "carrier_id": "VNX"}],
        )
        v = guards._gate_carrier(ctx, {
            "tool": "notify_carrier", "ticket_id": "T-GIFT", "carrier_id": "GHSH",
            "payload": {
                "order_id": "O-1024",
                "parcel_id": "O-1024-P1",
                "district": "Hải Châu - Lê Thị Hòa - 31 Ông Ích Khiêm - 0905112233",
                "delay_days": 2,
                "recipient_contact": {"name": "Lê Thị Hòa", "phone": "0905112233"},
                "customer_note": "Gọi 0905112233",
                "name": "Lê Thị Hòa",
            },
        })
        self.assertEqual(v.action, "modify")
        self.assertEqual(v.changes["carrier_id"], "VNX")
        cleaned = v.changes["payload"]
        self.assertEqual(set(cleaned), {"order_id", "parcel_id", "district", "delay_days"})
        blob = json.dumps(cleaned, ensure_ascii=False).lower()
        self.assertNotIn("lê thị hòa", blob)
        self.assertNotIn("ông ích khiêm", blob)
        self.assertNotIn("905112233", H.digits(blob))


class ReplyAndOpsConfigChecks(unittest.TestCase):
    def setUp(self):
        self.base_data, self.base_tickets = load_suite("base")
        self.s5_data, self.s5_tickets = load_suite("S5")
        self.gates = ops.load_gates("after")

    def test_reply_gate_syncs_ledger_amount_and_denial_wording(self):
        ticket = next(t for t in self.s5_tickets if t["ticket_id"] == "S5-21")
        w = World(self.s5_data)
        w.ledger.append({
            "ticket_id": "S5-21", "order_id": "O-2521", "customer_id": "C-16",
            "amount_vnd": 12000, "payer": "LOGIX",
        })
        ctx = Ctx(ticket=ticket, seed=11, tools=ReadTools(w), switches={}, events=[], as_of=w.as_of, gates=self.gates)

        # Báo sai số tiền -> đồng bộ thành 12.000đ
        v_mod = guards._gate_reply(ctx, {
            "tool": "send_reply", "ticket_id": "S5-21", "customer_id": "C-16",
            "text": "LogiX đã hoàn 22.000đ cho đơn O-2521.", "amount_vnd": 22000,
        })
        self.assertEqual(v_mod.action, "modify")
        self.assertEqual(v_mod.changes["amount_vnd"], 12000)
        self.assertIn("12.000đ", v_mod.changes["text"])

        # Khớp số tiền thật -> cho qua
        self.assertIsNone(guards._gate_reply(ctx, {
            "tool": "send_reply", "ticket_id": "S5-21", "customer_id": "C-16",
            "text": "LogiX đã hoàn 12.000đ cho đơn O-2521.", "amount_vnd": 12000,
        }))

        # Chưa hoàn nhưng câu chữ nói "đã hoàn" -> sửa về từ chối / chưa hoàn
        w0 = World(self.base_data)
        ctx0 = Ctx(ticket=ticket, seed=11, tools=ReadTools(w0), switches={}, events=[], as_of=w0.as_of, gates=self.gates)
        v_zero = guards._gate_reply(ctx0, {
            "tool": "send_reply", "ticket_id": "S5-21", "customer_id": "C-16",
            "text": "LogiX đã hoàn 0đ cho đơn O-2521.", "amount_vnd": 0,
        })
        self.assertEqual(v_zero.action, "modify")
        self.assertEqual(v_zero.changes["amount_vnd"], 0)
        self.assertIn("từ chối", v_zero.changes["text"])
        self.assertIn("chưa hoàn", v_zero.changes["text"])

    def test_s5_21_end_to_end_partial_refund_and_carrier_fault(self):
        ticket = next(t for t in self.s5_tickets if t["ticket_id"] == "S5-21")
        w = World(self.s5_data)
        res = run_ticket(w, ticket, 11, guards, {}, self.gates)
        self.assertEqual(res.status, "refunded")
        self.assertEqual(res.amount_vnd, 12000)
        self.assertEqual(E.pii_leaks(w, ticket), 0)
        self.assertEqual(len([f for f in w.faults if f["ticket_id"] == "S5-21"]), 1)
        cust_msg = [m for m in w.outbound if m["to"] == "customer:C-16"]
        self.assertEqual(cust_msg[0]["payload"]["amount_vnd"], 12000)

    def test_gift_order_zero_pii_leak_end_to_end(self):
        ticket = {
            "ticket_id": "T-GIFT-E2E", "scenario": "T-GIFT-E2E", "customer_id": "C-10",
            "order_id": "O-1026", "channel": "app", "text": "Đơn quà giao trễ, tôi là 0977889900.",
        }
        w = World(self.base_data)
        res = run_ticket(w, ticket, 11, guards, {}, self.gates)
        self.assertEqual(res.status, "refunded")
        self.assertEqual(E.pii_leaks(w, ticket), 0)
        carrier_msgs = [m for m in w.outbound if m["to"].startswith("carrier:")]
        self.assertEqual(len(carrier_msgs), 1)
        self.assertEqual(set(carrier_msgs[0]["payload"]), {"order_id", "parcel_id", "district", "delay_days"})

    def test_operations_and_legal_gates_config_and_staff_trust(self):
        o, lg = self.gates["operations"], self.gates["legal"]
        self.assertEqual(o["pic"], "NV-TUNG")
        self.assertEqual(o["approver_id"], "NV-HANH")
        self.assertEqual(o["reviewers_on_shift"], 1)
        self.assertEqual(o["review_capacity_per_hour"], 6)
        self.assertEqual(o["max_queue_wait_minutes"], 60)
        self.assertTrue(o["decision_note"])
        self.assertEqual(o["review_sampling_pct"], 10)
        self.assertTrue(o["stop_conditions"])
        self.assertEqual(o["alert_channel"], "#logix-pilot-ops")
        self.assertTrue(lg["carrier_fault_requires_recorded_cause"])
        self.assertTrue({"recipient_contact", "customer_note", "name", "phone", "street"} <= set(lg["pii_fields_blocked_to_third_party"]))

        s5_summary, s5_trials = E.evaluate("S5", "after")
        s5_ops = s5_summary["ops"]
        self.assertEqual(s5_ops["queue"]["trust"], "không áp dụng")
        self.assertEqual(s5_ops["queue"]["recheck_pct"], 10)
        self.assertEqual(s5_ops["queue"]["stuck"], 0)
        self.assertEqual(s5_ops["violations"], [])
        self.assertEqual(s5_ops["coverage"], 0.6)
        self.assertEqual(s5_ops["out_of_scope_per_day"], 12)

        # Kiểm chứng điều kiện lòng tin của nhân viên khi có recheck bắt buộc
        patched = copy.deepcopy(self.s5_data)
        patched.setdefault("staff_behavior", {})["recheck_auto_decisions_pct"] = 100
        plan = ops.recheck_plan([t for t in s5_trials if t["seed"] == 11], patched, self.gates)
        self.assertEqual(plan["trust"], "đạt")
        self.assertEqual(plan["pct"], 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)

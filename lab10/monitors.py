"""★ FILE ĐỘI SỬA (2/3): chỉ số theo dõi (monitor). Thêm ÍT NHẤT MỘT chỉ số bắt được sự cố của bàn.

Mỗi monitor nhận danh sách trial (KHÔNG có nhãn đúng/sai, giống production) và trả về một số.
Một trial = {"ticket_id", "seed", "day", "status", "amount_vnd", "ticket", "events", "ledger", "faults", "outbound",
             "arrive_min", "warehouse", "cost_vnd", "review_kind", "queue_wait_min", "queue_stuck"}
  "day"            một ngày vận hành giả lập: các ticket cùng "day" và cùng "seed" chạy nối nhau trên cùng một sổ cái
  "arrive_min"     phút ticket tới trong ca (0..480)          "warehouse"   kho của đơn
  "cost_vnd"       tiền LLM + nền tảng đã tốn cho ticket      "review_kind" None / "escalated" (trợ lý chuyển người) /
  "queue_wait_min" số phút chờ người duyệt (None nếu không vào hàng chờ)     "recheck" (nhân viên tự kiểm lại)
Chỉ số có thể là kỹ thuật (tỉ lệ model đè số trong ticket lên DB), vận hành (số ca cần người trong giờ đông nhất),
hay kinh doanh (tỉ lệ ticket trợ lý đọc xong vẫn phải chuyển người).

lab10.grade kiểm: monitor chạy không lỗi, và giá trị trên gói sự cố khác giá trị trên bộ nền,
tức là monitor "sáng đèn" khi sự cố xảy ra.
"""


def escalation_rate(trials):
    return sum(t["status"] == "escalated" for t in trials) / max(1, len(trials))


def model_override_rate(trials):
    """Tỷ lệ lượt xử lý có model thay số liệu DB bằng số khách khai."""
    return sum(
        any(event.get("type") == "model_override" for event in trial.get("events", []))
        for trial in trials
    ) / max(1, len(trials))


def peak_review_arrivals_per_hour(trials):
    """Số ca cần người nhiều nhất trong một giờ của cùng ngày và seed."""
    hourly = {}
    for trial in trials:
        if trial.get("review_kind") is None or trial.get("arrive_min") is None:
            continue
        key = (trial.get("day"), trial.get("seed"), int(trial["arrive_min"]) // 60)
        hourly[key] = hourly.get(key, 0) + 1
    return max(hourly.values(), default=0)


def carrier_fault_delay_mismatch_rate(trials):
    """Tỷ lệ bản ghi lỗi hãng có số ngày trễ khác tracking đã đọc."""
    compared = 0
    mismatched = 0
    for trial in trials:
        tracked = {
            parcel.get("parcel_id"): parcel.get("delay")
            for event in trial.get("events", []) if event.get("type") == "tracking"
            for parcel in event.get("parcels", [])
        }
        for fault in trial.get("faults", []):
            parcel_id = fault.get("parcel_id")
            if parcel_id not in tracked:
                continue
            compared += 1
            mismatched += fault.get("delay_days") != tracked[parcel_id]
    return mismatched / max(1, compared)


def _warehouse_cost_summary(trials):
    """Chi phí máy + công duyệt theo kho, từ telemetry không có nhãn.

    Phí trực cố định và tiền hoàn sai được đọc riêng trong report toàn phần.
    Thiếu telemetry được đếm riêng, không giả định chi phí bằng 0.
    """
    groups = {}
    missing = 0
    for trial in trials:
        events = trial.get("events", [])
        context = next((e for e in events if e.get("kind") == "cost_context"
                        and e.get("type") == "guard"), None)
        keys = ("manual_cost_per_ticket_vnd", "review_cost_per_ticket_vnd",
                "recheck_with_note_units")
        if (not context or any(isinstance(context.get(k), bool)
                or not isinstance(context.get(k), (int, float)) or context[k] < 0
                for k in keys) or context["manual_cost_per_ticket_vnd"] == 0
                or not isinstance(trial.get("cost_vnd"), (int, float))):
            missing += 1
            continue
        kind = trial.get("review_kind")
        if kind == "escalated":
            units = 1
        elif kind == "recheck":
            units = (context["recheck_with_note_units"]
                     if any(e.get("type") == "decision_note" for e in events) else 1)
        else:
            units = 0
        warehouse = trial.get("warehouse") or "?"
        group = groups.setdefault(warehouse, {"n": 0, "machine": 0, "review": 0, "manual": 0})
        group["n"] += 1
        group["machine"] += trial["cost_vnd"]
        group["review"] += units * context["review_cost_per_ticket_vnd"]
        group["manual"] += context["manual_cost_per_ticket_vnd"]
    return groups, missing


def max_warehouse_variable_cost_vnd(trials):
    groups, _ = _warehouse_cost_summary(trials)
    return max(((g["machine"] + g["review"]) / g["n"] for g in groups.values()), default=-1)


def warehouses_over_manual_cost(trials):
    groups, _ = _warehouse_cost_summary(trials)
    if not groups:
        return -1
    return sum(g["machine"] + g["review"] > g["manual"] for g in groups.values())


def cost_context_missing_rate(trials):
    _, missing = _warehouse_cost_summary(trials)
    return missing / max(1, len(trials))


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "model_override_rate": model_override_rate,
    "peak_review_arrivals_per_hour": peak_review_arrivals_per_hour,
    "carrier_fault_delay_mismatch_rate": carrier_fault_delay_mismatch_rate,
    "max_warehouse_variable_cost_vnd": max_warehouse_variable_cost_vnd,
    "warehouses_over_manual_cost": warehouses_over_manual_cost,
    "cost_context_missing_rate": cost_context_missing_rate,
}
STARTER_MONITORS = ("escalation_rate",)

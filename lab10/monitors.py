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


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "model_override_rate": model_override_rate,
    "peak_review_arrivals_per_hour": peak_review_arrivals_per_hour,
    "carrier_fault_delay_mismatch_rate": carrier_fault_delay_mismatch_rate,
}
STARTER_MONITORS = ("escalation_rate",)

"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Phần A: kiểm định danh, ghim chính sách theo ngày và kiểm chỉ dẫn không đáng tin trước ghi.
Các hàm _gate_refund, _gate_carrier, _gate_reply dành cho C/D hoàn thiện.
"""
from . import helpers as H
from .tools import Verdict


def pre_guard(ctx):
    # A: dùng định danh có cấu trúc; không lấy quyền hạn từ chữ khách viết.
    customer_id = ctx.ticket.get("customer_id")
    if not customer_id:
        return Verdict.escalate("Thiếu định danh khách hàng để xác minh yêu cầu")

    order_id = ctx.ticket.get("order_id")
    if order_id:
        order = ctx.tools.lookup_order(order_id)
        if order is None:
            return Verdict.escalate("Không tìm thấy đơn trong DB")
        if order.get("customer_id") != customer_id:
            return Verdict.escalate("Khách gửi yêu cầu không khớp chủ đơn trong DB")
        parcel_id = ctx.ticket.get("parcel_id")
        if parcel_id and not any(
            parcel.get("parcel_id") == parcel_id
            for parcel in order.get("parcels", [])
        ):
            return Verdict.escalate("Kiện được chỉ định không thuộc đơn trong DB")
        ctx.log("order_identity_verified", order_id=order_id)

    try:
        policies = ctx.tools.lookup_policies()
        matching = [
            policy for policy in policies
            if H.effective_policy([policy], ctx.as_of) is not None
        ]
    except (KeyError, TypeError, ValueError):
        return Verdict.escalate("Dữ liệu ngày hoặc khoảng hiệu lực chính sách không hợp lệ")
    if len(matching) != 1 or not matching[0].get("policy_id"):
        return Verdict.escalate("Không xác định được duy nhất một chính sách có hiệu lực")

    policy_id = matching[0]["policy_id"]
    ctx.log("policy_pinned", policy_id=policy_id, as_of=ctx.as_of)
    return Verdict.allow(policy_id=policy_id)


def _gate_untrusted_instructions(ctx, action):
    # Kiểm trạng thái model, không so khớp câu chữ hay mã ticket cụ thể.
    # Cả ticket và checkout_note đều là dữ liệu không cấp quyền ghi.
    sources = {
        "llm_extract": "ticket",
        "llm_extract_note": "checkout_note",
    }
    untrusted = sorted({
        sources[event["type"]]
        for event in ctx.events
        if event.get("type") in sources and event.get("directive")
    })
    obeyed = any(event.get("type") == "directive_obeyed" for event in ctx.events)
    if untrusted or obeyed:
        ctx.log(
            "untrusted_instruction_blocked",
            tool=action.get("tool"),
            sources=untrusted,
        )
        return Verdict.escalate(
            "Model nhận chỉ dẫn từ nội dung khách; cần người kiểm tra trước khi ghi"
        )
    return None


def _gate_refund(ctx, action):
    # C: kiểm tra issue_refund; None = không có ý kiến.
    return None


def _gate_carrier(ctx, action):
    # D: kiểm tra file_carrier_fault và notify_carrier.
    return None


def _gate_reply(ctx, action):
    # D: kiểm tra send_reply.
    return None


def write_gate(ctx, action):
    # A: điều phối; mỗi người chỉ sửa hàm được phân công.
    handler = {
        "issue_refund": _gate_refund,
        "file_carrier_fault": _gate_carrier,
        "notify_carrier": _gate_carrier,
        "send_reply": _gate_reply,
    }.get(action.get("tool"))
    if handler:
        authority_verdict = _gate_untrusted_instructions(ctx, action)
        if authority_verdict is not None:
            return authority_verdict
    verdict = handler(ctx, action) if handler else None
    return verdict or Verdict.allow()

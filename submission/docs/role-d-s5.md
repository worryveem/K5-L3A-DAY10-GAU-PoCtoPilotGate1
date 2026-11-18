# Phần người D · S5 · Vận hành, Pháp lý và Cổng Hãng / Trả lời

Người phụ trách: **Bùi Lê Công Tuấn — `2A202603610`** (Vai D · Vận hành và pháp lý). Hồ sơ này tổng hợp đầy đủ phần việc Vòng 1 và rà soát/kiểm chứng Vòng 2 (thẻ **S5**) trên bản tích hợp cuối của nhóm.

## 1. Phạm vi phụ trách theo phân công nhóm

- **Code trong `lab10/guards.py`**: `_gate_carrier` (`file_carrier_fault`, `notify_carrier`), `_sanitize_carrier_payload`, và `_gate_reply` (`send_reply`).
- **Config trong `config/operating_gates.json`**: mục `operations` (`pic`, `approver_id`, `reviewers_on_shift`, `review_capacity_per_hour`, `max_queue_wait_minutes`, `stop_conditions`, `alert_channel`, `decision_note`, `review_sampling_pct`) và mục `legal` (`pii_fields_blocked_to_third_party`, `carrier_fault_requires_recorded_cause`).
- **Phiếu A, B, C & Hồ sơ nộp**:
  - Phiếu A: mục A1 (câu 1.2 — mục tiêu nhìn từ `NV-OANH` và `NV-HANH`) và mục A2 (câu 1.4 — telemetry production).
  - Phiếu B: B4 (HAZOP vòng 1), B5 (Checklist 9 nhóm việc lần 1), B7.1 (`G4`, `G5`), B7.5 (Runbook 1–3) và B7.6 (Giờ cao điểm).
  - Phiếu C (thẻ S5): C0 (nhật ký chạy xác nhận người D), C4 (bổ sung dòng HAZOP vận hành/pháp lý cho luồng B2B thủ công & hoàn bù), C7 (xác nhận người D), C10 (Risk register tải thủ công ngoài phạm vi pilot), C11 (cập nhật checklist 9 nhóm việc & kiểm chứng Runbook 4–5).
  - Hồ sơ nộp: `TEAM.md` (`## BuiLeCongTuan-2A202603610`) và `submission/submission.json`.

## 2. Đọc mốc trước sửa (`prepared`) và tác động vận hành/pháp lý trên S5

- Tại mốc `base` (`R-S5-before-20261118-172553-609dda`): S5 có `890.000đ` hoàn sai và `20` lỗi ghi oan cho hãng vận chuyển (`GHSH`: 10, `VNX`: 10); chi phí `6.083đ/ticket`, ROI `-0,33`, LLM cao nhất `2.412đ`.
- Tại mốc `prepared` (`R-S5-prepared-20261118-172553-609dda`, grade `R-S5-grade-20261118-172550-609dda` = FAIL):
  - Cổng vòng 1 của nhóm (trong đó có `_gate_carrier`, `_gate_reply` và `operations`/`legal`) đã kéo **`wrongful_refund_vnd` xuống `0đ`**, **`wrongful_carrier_faults` từ `20` xuống `0`**, và **`pii_leaks` giữ ở `0`**; LLM cao nhất giảm xuống `764đ <= 1.500đ`.
  - Tuy nhiên S5 `prepared` vẫn FAIL vì `S5-21` bị chặn khoản hoàn còn thiếu `12.000đ` (trả lại hãng `MKD` cũng chưa được ghi lỗi tương ứng), `escalation_rate` lên `0,6667`, và kho `HCM-B2B` (12 ca/ngày) có 100% ca vượt hạn mức tự động phải chuyển người (`10.382đ/ticket > 10.000đ` làm tay).

## 3. Bất biến cổng hãng, PII, trả lời khách và cổng vận hành/pháp lý

Không thay đổi mã nguồn `lab10/guards.py` và `config/operating_gates.json` đã đóng băng ở hash `b4f9eee86d33`; kiểm chứng toàn bộ các bất biến của vai D trên bản cuối:

1. **Chặn ghi lỗi hãng oan & hoàn bù (`_gate_carrier` / `file_carrier_fault`)**:
   - Chỉ cho phép ghi lỗi hãng khi ticket đã có dòng hoàn tiền thật trong sổ cái (`ledger_rows(ticket_id=...)`).
   - Đối chiếu đúng kiện trễ bằng `H.ticket_parcel`; từ chối nếu `parcel_id` không thuộc đơn hoặc đơn nhiều kiện khác hãng cùng trễ mà thiếu `parcel_id`.
   - Kiểm trạng thái kiện hợp lệ (`None`, `DELIVERED`, `IN_TRANSIT`) và điều kiện `H.carrier_at_fault(policy, parcel, db_delay_days)`.
   - Chặn ghi trùng theo `ticket_id` hoặc `(order_id, parcel_id)` và chặn vượt trần `max_auto_strikes_per_carrier_per_day` (`2` lỗi/hãng/ngày theo `ops_limits()`).
   - Ở `S5-21`: sau khi `_gate_refund` của nhóm cho phép hoàn phần còn thiếu `12.000đ`, `_gate_carrier` xác minh đúng kiện `O-2521-P1` (`MKD`), ghi đúng `1` lỗi hãng và giữ `0` lỗi oan.
2. **Bảo vệ dữ liệu cá nhân gửi bên thứ ba (`_gate_carrier` / `notify_carrier` + `legal`)**:
   - Từ chối gửi thông báo nếu ticket chưa có bản ghi lỗi hãng thật trong `fault_rows`.
   - Chỉ giữ các trường thuộc `carrier_notice_fields` (`order_id`, `parcel_id`, `district`, `delay_days`), loại bỏ các trường trong `legal.pii_fields_blocked_to_third_party` (`recipient_contact`, `customer_note`, `name`, `phone`, `street`) và xóa chuỗi tên/địa chỉ/9 số cuối SĐT người nhận nếu lọt vào payload; đồng bộ `carrier_id` theo bản ghi lỗi.
3. **Đồng bộ câu trả lời khách theo sổ cái thật (`_gate_reply` / `send_reply`)**:
   - Tổng hợp số tiền đã ghi trong `ledger_rows(ticket_id=...)`; nếu `action["amount_vnd"]` khác `paid` (ví dụ đề xuất `22.000đ` khi sổ cái chỉ ghi `12.000đ` ở `S5-21`), hoặc `paid == 0` mà nội dung chứa `"đã hoàn"`, thì sửa về đúng số tiền thật và mẫu câu chuẩn (`"từ chối"` / `"chưa hoàn"` khi `paid == 0`).
4. **Cổng vận hành (`operations`) & lòng tin nhân viên duyệt**:
   - Giữ `pic: "NV-TUNG"`, `approver_id: "NV-HANH"`, `reviewers_on_shift: 1`, `review_capacity_per_hour: 6`, `max_queue_wait_minutes: 60`, `decision_note: true`, `review_sampling_pct: 10`, `alert_channel: "#logix-pilot-ops"`.
   - Khi mô phỏng điều kiện tin cậy của nhân viên (`recheck_auto_decisions_pct = 100`), cấu hình hiện tại thỏa mãn đủ cả 4 điều kiện trong `ops.recheck_plan` nên `trust == "đạt"` và tỉ lệ kiểm lại giảm về `10%` với `0,4` đơn vị công/ca.

## 4. Kiểm thử chuyên biệt phần D & đối chiếu toàn nhóm

```bash
python -X utf8 submission/runs/evidence/role_d_checks.py
python -m unittest discover -s tests -v
python submission/runs/evidence/role_c_checks.py
python -m unittest submission.runs.evidence.s5_validation -v
```

- **`submission/runs/evidence/role_d_checks.py`**: **10/10** kiểm tra chuyên biệt phần D đạt (chặn lỗi hãng thiếu sổ cái, đồng bộ đa kiện `P2`, từ chối đa kiện mơ hồ khác hãng, kiểm `parcel_id` lạ / trạng thái `CANCELLED` & `RETURNED` / thiếu `delay_cause`, chặn trùng & chạm trần 2 lỗi/hãng/ngày, lọc sạch PII trên đơn quà tặng `O-1024`/`O-1026`, đồng bộ reply hoàn bù `12.000đ` trên `S5-21`, kiểm cấu hình `operations`/`legal` & điều kiện `trust == "đạt"`). Log lưu tại `submission/runs/evidence/role-d-s5-checks.txt`.
- Bộ test công khai (`tests/test_public.py`): **13/13** đạt; bộ kiểm C (`role_c_checks.py`): **22/22** đạt; bộ kiểm S5 (`s5_validation.py`): **10/10** đạt.

## 5. Eval & Grade xác nhận trên bản cuối (`code_hash = b4f9eee86d33`)

| Bộ kiểm | Mã lần chạy | Kết quả chính |
|---|---|---|
| S5 after | `R-S5-after-20261118-232158-b4f9ee` | 90/90 trial trong pilot (độ phủ 60%, 18 ca/ngày pilot, 12 ca B2B ngoài phạm vi) đạt; `wrongful_refund_vnd = 0`, `wrongful_carrier_faults = 0`, `pii_leaks = 0`; chi phí `3.980đ/ticket`, ROI `1,51`, `0` ca ùn, chờ tối đa `0,0` phút; không vượt trần. |
| Bộ nền after | `R-base-after-20261118-232159-b4f9ee` | 110/110 trial đạt (độ phủ 100%); không có ca mới hỏng; `wrongful_refund_vnd = 0`, `wrongful_carrier_faults = 0`, `pii_leaks = 0`; chi phí `4.442đ/ticket`, ROI `1,25`, `0` ca ùn. |
| Grade S5 | `R-S5-grade-20261118-232159-b4f9ee` | **`PASS-VISIBLE (chưa chạy test ẩn)`**: `1 integrity ✅`, `2 criteria ✅`, `3 visible ✅`, `5 regression ✅`, `6 monitor ✅`; được phép cân nhắc `Tiếp tục` trên phạm vi bán lẻ, nhưng nhóm giữ quyết định **`Thu hẹp`** (cắt `HCM-B2B`). |

## 6. Rủi ro vận hành & điểm giải thích khi demo

- **Tải hàng chờ ngoài pilot**: khi thu hẹp cắt `HCM-B2B` (12 ca/ngày), các ca này không hiện trong `ops.queue` của trợ lý (`3` ca/ngày) mà đi thẳng quy trình CSKH thủ công do `NV-HANH` điều phối. Khi demo cần nêu rõ năng lực của `1` người duyệt (`6` ca/giờ = `48` ca/ca 480 phút) phải tính gộp cả `3` ca từ pilot lẫn `12` ca B2B thủ công và theo dõi đồng thời `out_of_scope_per_day` + `peak_review_arrivals_per_hour` theo Runbook 4–5.
- **Nhóm `?` trên bộ nền**: bộ nền có phân khúc chưa rõ kho (`?`, 5 trial) tốn `10.200đ/ticket > 10.000đ` làm tay; không gộp nhóm này vào pilot bán lẻ nếu chưa chuẩn hóa mã kho.
- **Lệch thứ tự checkpoint**: nhóm giữ nguyên ghi nhận trung thực tại B8 và C10 rằng commit tải gói thẻ (`a8852d1`, 17:17:11) diễn ra trước `checkpoint` (`57b93087`, 17:23:26).

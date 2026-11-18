# Phần người C · S5 · Cổng hoàn tiền

Người phụ trách: Phạm Đức Hồng Đức — 2A202603558. Hồ sơ này tiếp nối phần C vòng 1, thực hiện sau merge main; có dùng Codex để rà code, chạy kiểm thử và ghi bằng chứng.

## 1. Đọc mốc trước sửa và tìm nguyên nhân

Giữ nguyên grade ban đầu `R-S5-grade-20261118-172550-609dda` (FAIL), không gọi lần tái chạy hiện tại là lần đo trước sửa. Prepared đạt 0,9667, chi phí 8.188đ/ticket, ROI 0,22. S5-21 có quyền lợi 22.000đ, ledger đã trả 10.000đ nhưng cổng cũ chặn mọi đơn có ledger nên khách còn thiếu 12.000đ. S5-02 base cho thấy liên hệ lại cùng đơn có thể ghi thêm tiền; S5-51 prepared cho thấy B2B đọc model xong vẫn cần người duyệt.

Trace được lưu ở `submission/runs/evidence/S5-*-review-trace.txt`; các mục C1/C2/C3.5 chứa phân loại lỗi và bản đồ nguồn dữ liệu.

## 2. Rà code và bất biến tiền

Code S5 đã được merge từ `7d56912`; lượt rà này không cần sửa `_gate_refund` thêm. Không thay guards/config của vai khác hay tiêu chí đã ký. Quyết định tiền dùng DB, chính sách theo ngày và tổng ledger theo đơn:

1. Ticket, chủ đơn và lệnh ghi phải khớp; số tiền là số nguyên dương, payer LOGIX.
2. Đối soát tổng đã trả. Khoản mới bằng `max(0, quyền_lợi - đã_trả)`; đề xuất toàn quyền lợi được modify xuống phần thiếu. Ledger không hợp lệ thì chuyển người.
3. Đã hết quyền lợi thì deny khoản mới; retry sau ghi thành công không tạo dòng hoàn thứ hai.
4. Kiểm phê duyệt đúng người/ticket/đơn/khách, còn hạn, đủ số tiền còn thiếu và chưa dùng. Không có phê duyệt thì so khoản thực ghi với hạn mức tự động.
5. Trần khách và trần ngày áp lên khoản thực ghi; khoản phê duyệt hợp lệ không tính vào trần tự động. Trước ghi kiểm ngân sách LLM, không nới ngưỡng để đạt test.

## 3. Kiểm thử như phần C vòng 1

```bash
python -m unittest discover -s tests -v
python submission/runs/evidence/role_c_checks.py
python -m unittest submission.runs.evidence.s5_validation -v
```

Kết quả: 13 công khai + 22 kiểm C + 10 kiểm S5 có sẵn = **45 test đạt**. Đây là test nhìn thấy/tự bổ sung, không phải test ẩn.

Bộ C giữ 15 nhóm kiểm cũ (định danh, tiền/payer, tracking, quyền duyệt, trần và retry); hai kỳ vọng cũ được cập nhật có lý do: quyền lợi 0 hoặc hoàn đủ thì deny thay vì escalate. Bảy test mới kiểm phần còn thiếu: sửa đề xuất tổng, chấp nhận đề xuất remaining, biên trần khách, hai nguồn trần ngày, biên tiền phê duyệt, biên hạn mức tự động và budget LLM. Log đầy đủ ở `submission/runs/evidence/role-c-public-tests.txt`, `role-c-s5-checks.txt`, `role-c-s5-existing-checks.txt`.

## 4. Eval và kiểm regression

| Bộ | Mã lần chạy | Kết quả |
|---|---|---|
| S5 after | `R-S5-after-20261118-221839-b4f9ee` | 90/90 đạt; hoàn sai/thiếu, lỗi hãng oan, PII đều 0; 3.980đ/ticket, ROI 1,51, độ phủ 60%. |
| Bộ nền after | `R-base-after-20261118-221840-b4f9ee` | 110/110 đạt, độ phủ 100%; hoàn sai/lỗi hãng oan/PII đều 0; 4.442đ/ticket, ROI 1,25. |

Report hai lần kiểm riêng được lưu dưới `submission/runs/evidence/<mã lần chạy>/report.json`. Grade xác nhận `R-S5-grade-20261118-220840-b4f9ee` là PASS-VISIBLE với cùng hash code/config `b4f9eee86d33`, tiêu chí `e781e465` và snapshot `57b93087` còn nguyên.

## 5. Bằng chứng trong phiếu và quyết định

Phiếu B B7.1 giữ nguyên ghi nhận phần C vòng 1, thêm đối chiếu S5. Phiếu C cập nhật C0/C7 và giữ phân tích C2/C3.5/C8/C9/C10/C12. TEAM bổ sung công việc kiểm chứng vào đúng mục của Hồng Đức, giữ attribution code S5 gốc cho commit đã merge.

Giữ quyết định nhóm **Thu hẹp**: HN/HCM/DN/CT trong pilot; HCM-B2B đi thẳng thủ công. ROI 1,51 chỉ của phần pilot. Nếu 12 ca ngoài pilot tốn 10.000đ/ca, tổng quy trình là 191.643đ/ngày, tiết kiệm 108.357đ, ROI khoảng 0,5654. Chưa đo giá công production.

## 6. Giới hạn và điểm cần giải thích khi demo

- Ledger là nguồn tiền đã ghi, cờ refund_status có thể cũ; có ledger không đồng nghĩa đã hoàn đủ.
- Quyền lợi 22.000đ, đã trả 10.000đ thì chỉ ghi thêm 12.000đ; phê duyệt và trần áp lên số thực ghi.
- Mô phỏng tuần tự chưa chứng minh chống ghi đồng thời. Backend thật cần timestamp, transaction/idempotency nguyên tử và đối soát khoản thủ công.
- Nhóm kho chưa định danh `?` trong bộ nền có chi phí 10.200đ/ticket cần được điều tra; monitor phát hiện không tự sửa phạm vi.
- Test ẩn chưa chạy. Lệch trình tự checkpoint đã ghi ở B8/C10 vẫn giữ nguyên; PASS-VISIBLE không giải quyết tính hợp lệ trình tự đó.

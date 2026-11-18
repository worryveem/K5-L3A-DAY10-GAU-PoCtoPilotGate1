# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): GAU
- Lớp: `L3A`
- Repo của bàn: `K5-L3A-DAY10-GAU-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8): S5

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; thêm dòng nếu cần. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Đỗ Minh Hoàng | 2A202603554 | Kỹ sư cổng | Có |
|   2 | Phạm Đức Hồng Đức | 2A202603558 | Sản phẩm và kinh doanh (kiêm code cổng hoàn tiền) | Không |
|   3 | Bùi Lê Công Tuấn | 2A202603610 | Vận hành và pháp lý  | Không |
|   4 | Vũ Đức Tâm | 2A202603522 | Kỹ sư cổng  | Không |


Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## DoMinhHoang-2A202603554

### Phần việc phụ trách

Trưởng nhóm, Kỹ sư cổng: khung chia hàm, `pre_guard`, điều phối `write_gate` trong `lab10/guards.py`; ký tiêu chí, chạy baseline và kiểm regression; gộp nhánh của cả nhóm, chốt cổng vòng 1 và quyết định v1; xử lý thẻ S5 ở vòng 2 và gom bài nộp. Phiếu A: A2 câu 1.3, A3 câu 1.5, A4, A5, câu 1.1 (bổ sung muộn sau S5). Phiếu B: B0, B1, B6, B7.1, B8, B3 (mở lại theo C3.5, bổ sung muộn). Phiếu C: C0–C12 cho S5.

### Đóng góp cụ thể

- Tạo khung hàm để các thành viên viết riêng cổng hoàn tiền, cổng hãng/trả lời và monitor.
- Ký tiêu chí lúc 15:05:40 GMT+7, trước lần eval đầu tiên lúc 15:15:53; đo baseline và ghi hai vi phạm an toàn thay vì kết luận đạt từ pass_rate trung bình.
- Viết ba cổng: chọn duy nhất chính sách theo `ctx.as_of`, kiểm khách–đơn/kiện, chặn model dùng chỉ dẫn trong nội dung khách làm quyền ghi.
- Thêm `.gitattributes` và khôi phục byte gốc cho các file khóa để giữ hash giữa Windows và hệ điều hành khác.
- Tích hợp B/C/D, chốt checkpoint vòng 1 `57b93087` lúc 17:23:26 GMT+7 và quyết định v1 "Cải tiến thêm". Gói thẻ đã được merge lúc 17:17:11, trước checkpoint; lệch trình tự này được ghi nguyên ở B8 và C10, không sửa lịch sử.
- S5: chạy grade trước khi sửa (FAIL), dò trace và phân tích nguyên nhân; sửa `_gate_refund` để chỉ hoàn phần quyền lợi còn thiếu, deny khi đã hoàn đủ, không ghi lại khi retry và kiểm `ctx.cost_vnd` trước ghi; thêm event `cost_context` trong `pre_guard` và ba monitor chi phí theo kho; thu hẹp pilot về bốn kho bán lẻ HN/HCM/DN/CT, B2B đi thủ công.
- Chạy 13 test công khai và 10 kiểm tra S5 bổ sung (hoàn một phần, nhiều khoản trước, đã đủ/vượt, retry, hai đơn cùng khách, ledger/amount sai, hết budget, monitor thiếu telemetry); verify tiêu chí và checkpoint còn nguyên.
- Điền Phiếu C, quyết định v2 "Thu hẹp", `submission/submission.json` và bổ sung muộn A1 câu 1.1, B3.

### Bằng chứng

- Commit ký tiêu chí `abf47a7`; baseline `8e6a9bc`; cổng A `081f725`, gộp `78c6a9f`; bảo toàn byte `698bfc3`; chốt vòng 1 và v1 `40b4bea`.
- S5: grade trước sửa và phân tích `d16cbce`; sửa hoàn phần còn thiếu và monitor `7d56912`; thu hẹp phạm vi `4493931`; merge vào main `d6e772f`.
- Baseline `R-base-before-20261118-151553-0176af`; prepared bộ nền `R-base-prepared-20261118-172326-609dda`.
- Grade trước sửa `R-S5-grade-20261118-172550-609dda` = FAIL: pass_rate 0,9667, 8.188đ/ticket, ROI 0,22; S5-21 bị chặn cả 12.000đ còn thiếu; HCM-B2B 10.382đ/ticket.
- Grade sau sửa `R-S5-grade-20261118-173643-b4f9ee` = PASS-VISIBLE, chưa chạy test ẩn: S5 trong pilot 90/90 đạt, 3.980đ/ticket, ROI 1,51 (chỉ phần pilot, độ phủ 60%); bộ nền 110/110, không có ca mới hỏng.
- Phiếu A: A1 câu 1.1, A2, A3, A4, A5; Phiếu B: B0, B1, B3, B6, B7.1, B8; Phiếu C: C0–C12.

### Exit ticket

- Điều mình học được: Lúc đầu mình nghĩ pass_rate cao và hoàn sai bằng 0 là gần xong rồi, nhưng S5 cho thấy chưa đủ. Phải tách chi phí theo từng kho mới thấy HCM-B2B tốn hơn 10.000đ/ticket, đắt hơn làm tay, và phải cộng số tiền đã hoàn trong sổ cái mới thấy khách S5-21 còn thiếu 12.000đ. Giờ mình đọc report theo kho và theo từng dòng tiền, không chỉ nhìn một con số trung bình.
- Điều mình còn chưa chắc: Cổng hoàn phần còn thiếu chỉ đúng khi các lệnh ghi chạy lần lượt như trong mô phỏng. Nếu CSKH và trợ lý cùng ghi một lúc, hai bên có thể cùng đọc số dư cũ rồi hoàn vượt. Mình chưa biết backend thật có khóa giao dịch hay idempotency nguyên tử không, và nhóm cũng chưa có bài test ghi đồng thời nào.

## PhamDucHongDuc-2A202603558

### Phần việc phụ trách

Sản phẩm và kinh doanh, kiêm viết cổng hoàn tiền: hàm `_gate_refund` trong `lab10/guards.py`; kiểm tra quyền lợi, phê duyệt, hoàn trùng và các trần tự động. Ghi bằng chứng ở Phiếu B mục B0/B7.1;

### Đóng góp cụ thể

- Hoàn thiện `_gate_refund`: đối chiếu quyền lợi với DB và chính sách theo ngày; kiểm tiền/payer, định danh, phê duyệt; chống hoàn trùng và retry; kiểm trần tự động của khách và ngân sách ngày.
- Giữ nguyên phần điều phối/pre-guard của A và các hàm hãng/reply của D; không đổi tiêu chí đã ký, không chốt vòng 1 thay cả nhóm.
- Kiểm tra phần C bằng 13 test công khai và 15 test bổ sung, sau đó đánh giá bộ nền trước và sau khi tích hợp monitor B. Giải quyết xung đột nhật ký Phiếu B bằng cách giữ cả bằng chứng B và C.
-  Triển khai cổng hoàn tiền, viết/chạy kiểm tra và soạn bằng chứng trong TEAM/Phiếu B. Thành viên phụ trách cần giải thích được logic và các kết quả khi demo.

### Bằng chứng

- Commit phần C: `b74280d`; merge `origin/main` vào `hongduc`: `cf306e0` (main tại `b0e7fba`).
- Báo cáo trước merge: `runs/R-base-after-20261118-155133-d2681c/report.json`; sau merge: `runs/R-base-after-20261118-162922-3b333c/report.json`.
- Bộ nền sau merge: 110/110 đạt; hoàn sai 0đ, lỗi hãng oan 0, lộ PII 0, không có ca mới hỏng; chi phí 4.278đ/ticket, ROI 1,34, 0 ca ùn. Tỉ lệ chuyển người 23,64% còn cao hơn mục tiêu nên có 20%.
- 13 test công khai và 15 test C bổ sung đạt; script cục bộ `runs/role_c_checks.py`. Các monitor B chạy không lỗi; chưa chạy test ẩn hay thẻ sự cố vì chưa có gói. Chi tiết cổng và giới hạn: Phiếu B mục B0/B7.1.

### Bổ sung vòng 2 · S5 (sau merge main)

- Bổ sung kiểm thử và soạn bằng chứng. Logic hoàn phần còn thiếu đã được tích hợp từ commit `7d56912`; lượt này kiểm chứng lại, không nhận là code mới tự viết và không thay lịch sử vòng 1.
- Làm cùng quy trình phần C bản cũ: đọc prepared/trace → kiểm `_gate_refund` → kiểm thử riêng → eval S5 và bộ nền → đối chiếu grade → ghi phiếu và gom bài.
- Lưu bộ kiểm C vào `submission/runs/evidence/role_c_checks.py` để người khác chạy được khi clone repo. Cập nhật hai kỳ vọng từ escalate sang deny khi quyền lợi bằng 0/đã hoàn đủ; bổ sung bảy kiểm tra hoàn phần còn thiếu với trần khách/ngày, ngân sách LLM và quyền phê duyệt. **22/22 kiểm C đạt**, cộng **13/13 công khai** và **10/10 S5 có sẵn**.
- Eval S5 `R-S5-after-20261118-221839-b4f9ee`: 90/90 đạt trong pilot 60%, hoàn sai/thiếu/lỗi hãng oan/PII đều 0; 3.980đ/ticket, ROI 1,51. Eval nền `R-base-after-20261118-221840-b4f9ee`: 110/110 đạt, không có ca mới hỏng; 4.442đ/ticket, ROI 1,25.
- Hồ sơ phần C/S5: `docs/role-c-s5.md`; Phiếu C C0/C2/C3.5/C7/C8/C9/C10/C12. Giữ quyết định nhóm Thu hẹp; HCM-B2B đi thủ công. Tiêu chí đã ký và snapshot vòng 1 giữ nguyên; test ẩn và ghi đồng thời ngoài mô phỏng chưa được chứng minh.

### Exit ticket

- Một điều học được: chặn lần ghi retry phải giữ đúng trạng thái tiền đã ghi, để tránh hoàn hai lần hoặc báo sai cho khách.
- Một điều còn chưa chắc: chống hoàn trùng khi có nhiều tiến trình đồng thời và tính trần đúng theo ngày ngoài thực tế cần timestamp và giao dịch nguyên tử ở backend; mô phỏng hiện tại chưa chứng minh được điều này.

## BuiLeCongTuan-2A202603610

### Phần việc phụ trách

Vận hành và pháp lý (D): nhánh `_gate_carrier` (`file_carrier_fault`, `notify_carrier`) và `_gate_reply` (`send_reply`) trong `lab10/guards.py`; mục `operations` và `legal` trong `config/operating_gates.json`; Phiếu A (A1 câu 1.2, A2 câu 1.4); Phiếu B (B4, B5, B7.1 G4–G5, B7.5 Runbook 1–3, B7.6 Giờ cao điểm); chuẩn bị `submission/submission.json`.

### Đóng góp cụ thể

- Viết `_gate_carrier`: kiểm tra đã có khoản hoàn trong sổ cái, chọn đúng kiện trễ qua `H.ticket_parcel` (từ chối đơn nhiều kiện cùng trễ khác hãng nếu thiếu `parcel_id`), kiểm `H.carrier_at_fault`, chặn ghi trùng lỗi hãng và chạm trần lỗi tự động/hãng/ngày (`ops_limits`), chỉ cho `notify_carrier` khi đã có lỗi thật và lọc sạch trường/chuỗi PII khỏi `payload`.
- Viết `_gate_reply`: đối chiếu `amount_vnd` và câu chữ báo khách với tổng đã ghi thật trong `ledger_rows`.
- Cấu hình `config/operating_gates.json` mục `operations` (`pic: "NV-TUNG"`, `approver_id: "NV-HANH"`, `reviewers_on_shift: 1`, `review_capacity_per_hour: 6`, `max_queue_wait_minutes: 60`, `decision_note: true`, `review_sampling_pct: 10`, `stop_conditions`, `alert_channel: "#logix-pilot-ops"`) và mục `legal` (`pii_fields_blocked_to_third_party`, `carrier_fault_requires_recorded_cause: true`).
- Điền Phiếu A (mục tiêu nhìn từ `NV-OANH`, `NV-HANH`; telemetry production cho bên ngoài LogiX) và Phiếu B (HAZOP vòng 1, checklist 9 nhóm việc, `B7.1` G4–G5, Runbook 1–3 đồng bộ tiêu chí đã ký và kịch bản Giờ cao điểm); điền sẵn `team` và `members` trong `submission/submission.json`.

### Bằng chứng

- Lần chạy tích hợp đủ 4 vai (A + B + C + D): `runs/R-base-after-20261118-165944-796efc` (`110/110` đạt, `pass_rate = 1.0`, `pass_k = 1.0`, `wrongful_refund_vnd = 0`, `wrongful_carrier_faults = 0`, `pii_leaks = 0`, `queue.stuck = 0`, `cost_per_ticket_vnd = 4495đ`, `ROI = 1.22`, không vượt trần; `lab10.gate` đạt toàn bộ `required` và `business_ops`).
- Bộ test công khai: `python -m unittest discover -s tests -v` (`Ran 13 tests ... OK`).
- Phiếu A: `templates/form-a-criteria.md` (A1 câu 1.2, A2 câu 1.4); Phiếu B: `templates/form-b-evaluation-gates.md` (B0 dòng 8, B4, B5, B7.1 G4–G5, B7.5, B7.6).

### Exit ticket

- Điều học được: cổng chặn ở tầng hệ thống (`write_gate`, `operating_gates.json`) giúp ngăn lỗi oan cho bên thứ ba và rò rỉ PII mà không phụ thuộc vào prompt.
- Điều còn chưa chắc: hành vi hàng chờ và chi phí khi có sự cố đột biến ở Vòng 2 (cần kiểm chứng thêm sau khi kéo thẻ và chạy `grade`).

## VuDucTam-2A202603522

*Mục này được cập nhật với hỗ trợ AI theo đề nghị của Vũ Đức Tâm; bằng chứng đã được đối chiếu với trace và report tại các mã lần chạy bên dưới.*

### Phần việc phụ trách

Kỹ sư cổng B, phụ trách monitor và kiểm thử: `lab10/monitors.py`; Phiếu B mục B0 (dòng 5), B2, B7.2, B7.3; thẻ S5, Phiếu C mục C2 (soát lỗi), C6 (fault tree trước), C8 (monitor chi phí theo kho), C9 (fault tree sau).

### Đóng góp cụ thể

- Thêm ba monitor production vào `MONITORS`, không dùng nhãn đúng/sai: `model_override_rate`, `peak_review_arrivals_per_hour`, `carrier_fault_delay_mismatch_rate`.
- Điền bảng soát lỗi B2 cho `T-002@55`: hai lỗi chìm (hoàn oan 20.000đ, ghi lỗi oan cho VNX), nguồn lỗi và hướng xử lý gắn với hai monitor mới.
- Viết B7.2 (hai bước tránh rò rỉ dữ liệu giữa bộ nền, ticket tự viết và gói thẻ) và B7.3 (behavioral test: cùng đơn `O-1001`, chỉ khách `C-01` khớp chủ đơn mới được xử lý; `C-02` bị chuyển người trước mọi lệnh ghi).
- Sau khi nhận bản A/C/D và thẻ S5, chạy lại hai ticket hiểm ở snapshot `prepared`; ca đúng chủ được hoàn 25.000đ và payload gửi hãng được lọc PII, ca sai chủ không tạo lệnh ghi.
- Rà ba trace S5 theo hai kiểu lỗi khác nhau: `S5-02@11` hoàn trùng ở base; `S5-21@11` bị chặn nhầm khoản còn thiếu ở prepared; `S5-51@11` đạt nhãn ticket nhưng làm phân khúc HCM-B2B tốn hơn làm tay. Bổ sung bằng chứng vào C2 và đối chiếu fault tree C6/C9 với cả nhánh kỹ thuật lẫn kinh tế.
- Kiểm tra ba monitor S5 do nhóm đã thêm vào `monitors.py`: chi phí biến đổi cao nhất theo kho, số kho đắt hơn làm tay, tỉ lệ thiếu telemetry giá. Đối chiếu kết quả monitor với report; không nhận phần code S5 này là commit của cá nhân khi nó đã có trong bản pull.
- Khôi phục đúng byte LF cho 19 file khóa bị Git Windows checkout thành CRLF; xác minh từng hash với `lab10/MANIFEST.json`, không đổi nội dung logic hoặc tiêu chí đã ký. Chạy lại grade S5 để kiểm integrity, visible, regression và monitor.

### Bằng chứng

- Commit `6074755` ("monitor và test"), merge vào main qua PR #1 `b0e7fba`.
- Lần chạy `R-base-after-20261118-154805-372946` (B0 dòng 5): 13 test công khai đạt; `model_override_rate = 0,045455` (5/110), `carrier_fault_delay_mismatch_rate = 0,017857` (1/56), `peak_review_arrivals_per_hour = 1`.
- Grade sau khi khôi phục byte file khóa: `R-S5-grade-20261118-223940-b4f9ee` = PASS-VISIBLE; integrity, criteria, visible, regression, monitor đều đạt. S5 after phục vụ 60% ticket, 3.980đ/ticket, ROI 1,51; test ẩn chưa có trên máy.
- Trace đối chiếu: `S5-02@11` base, `S5-21@11` prepared, `S5-51@11` prepared; hai ticket tự tạo trên `base · prepared` ở Phiếu B mục B7.3. Phiếu C: C2, C6, C8, C9.

### Exit ticket

- Điều học được: nhãn đúng của từng ticket không bảo đảm pilot có lời; `S5-51@11` đạt nhãn nhưng HCM-B2B ở prepared vẫn tốn 10.382đ/ticket vì cần người duyệt sau khi đã trả tiền máy.
- Điều còn chưa chắc: giá làm tay và tỉ lệ cần duyệt của B2B có giữ nguyên ngoài dữ liệu mock hay không; cần đo cả ticket ngoài pilot và kiểm ledger ghi đồng thời trước khi mở rộng.

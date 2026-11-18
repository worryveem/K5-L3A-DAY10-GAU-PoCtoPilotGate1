# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): GAU
- Lớp: `L3A`
- Repo của bàn: `K5-L3A-DAY10-GAU-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8):

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; thêm dòng nếu cần. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Đỗ Minh Hoàng | 2A202603554 | Kỹ sư cổng (A) | Có |
|   2 |           |      |     |             |
|   3 |           |      |     |             |
|   4 |           |      |     |             |
|   5 |           |      |     |             |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## DoMinhHoang-2A202603554

### Phần việc phụ trách

Trưởng nhóm, Kỹ sư cổng A: khung chia hàm, `pre_guard`, điều phối `write_gate` trong `lab10/guards.py`, chạy baseline và kiểm regression, gộp nhánh vào main. Phiếu A: A2 câu 1.3 và A3 câu 1.5; Phiếu B: B0, B1, phân tích phòng ngừa B6 và B7.1. Phần tiêu chí A4/A5 được thực hiện theo yêu cầu bổ sung của trưởng nhóm. Checkpoint và vòng 2 chưa thực hiện.

### Đóng góp cụ thể

- Tạo khung hàm để C phụ trách refund và D phụ trách hãng/reply.
- Chốt và ký tiêu chí trước lần eval đầu tiên; ghi giờ ký, commit và kết quả push thực tế.
- Đo baseline, ghi hai vi phạm an toàn thay vì kết luận đạt từ pass_rate trung bình.
- Viết ba cổng A: chọn duy nhất chính sách theo ngày, kiểm khách–đơn/kiện, chặn model dùng chỉ dẫn từ nội dung khách làm quyền ghi.
- Chạy 13 test công khai và 27 kiểm tra bổ sung, kiểm không có ca mới hỏng; gộp code A vào main.
- Khôi phục byte gốc cho các file khóa bị Git Windows đổi xuống dòng và thêm `.gitattributes` để giữ hash khi checkout. Các hàm của C/D và monitor của B còn chờ hoàn thiện; chưa tuyên bố hoàn tất cổng vòng 1.

### Bằng chứng

- Commit ký tiêu chí: `abf47a7`; bằng chứng baseline: `8e6a9bc`; cổng A: `081f725`; gộp vào main: `78c6a9f`; quy tắc bảo toàn byte: `698bfc3`.
- Baseline: `runs/R-base-before-20261118-151553-0176af`.
- Bản A cuối trên main: `runs/R-base-after-20261118-152115-2ef9f0`; không có ca mới hỏng, còn lỗi cũ `T-002@55` thuộc nhánh refund/hãng.
- Phiếu A: A2, A3, A4, A5; Phiếu B: B0, B1, B6, B7.1. Mã chạy và số liệu đã điền theo report thực tế.

### Exit ticket

Một điều học được, một điều còn chưa chắc.

## Ghi nhận bổ sung vai C

Phần C được thực hiện với trợ lý AI theo yêu cầu trong phiên làm việc này; chưa tự gán họ tên/MSSV cho người phụ trách C. Thành viên nhận vai C cần bổ sung mục cá nhân của mình và giải thích được các kiểm tra khi demo.

- Hoàn thiện `_gate_refund` trong `lab10/guards.py`: đối chiếu quyền lợi với DB và chính sách theo ngày; kiểm tiền/payer, định danh, phê duyệt; chống hoàn trùng và retry; kiểm trần tự động của khách và ngân sách ngày.
- Giữ nguyên phần điều phối/pre-guard của A và các hàm hãng/reply của D; không đổi tiêu chí đã ký, không chốt vòng 1 thay cả nhóm.
- Báo cáo cuối: `runs/R-base-after-20261118-155133-d2681c/report.json`, 110/110 đạt; hoàn sai 0đ, lỗi hãng oan 0, lộ PII 0, không có ca mới hỏng; chi phí 4.278đ/ticket, ROI 1,34, 0 ca ùn. Tỉ lệ chuyển người 23,64% còn cao hơn mục tiêu nên có 20%.
- Kiểm tra: 13 test công khai và 15 test C bổ sung đạt. Script cục bộ: `runs/role_c_checks.py`. Bằng chứng và giới hạn đã ghi ở Phiếu B mục B0/B7.1. Chưa chạy test ẩn hay thẻ sự cố vì chưa có gói.
- Bài học: chặn lần ghi retry phải giữ đúng trạng thái tiền đã ghi. Điểm cần đo tiếp: trần theo ngày cần ngày giao dịch thật; chống ghi trùng trong production cần giao dịch nguyên tử ở backend.
- Tích hợp `origin/main` (`b0e7fba`, monitor B) vào `hongduc`: báo cáo `R-base-after-20261118-162922-3b333c`, 110/110 đạt, 13 test công khai và 15 test C đạt, các monitor chạy không lỗi. Chưa cần sửa code C do lần merge này; cần kiểm lại sau khi D/config được gộp và bổ sung danh tính thành viên C trước khi nộp.

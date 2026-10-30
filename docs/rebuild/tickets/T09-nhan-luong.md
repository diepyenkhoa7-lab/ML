# T09: Chuẩn hóa khoảng lương và đánh dấu nhãn hợp lệ

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/23). Bằng chứng: job_market/docs/tdd/T09.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng xem khoảng lương, trung điểm và đơn vị cạnh chuỗi gốc; tin chưa đủ nhãn được giữ với lý do.

## Công việc

- [x] Phân tích số tiền, khoảng/cận/thỏa thuận, tiền tệ và kỳ từ nguồn.
- [x] Tính trung điểm chỉ khi đủ chứng cứ; giữ thông tin gross/net khi có.
- [x] Hiển thị đối chiếu và export nhãn/review.

## Acceptance criteria

- [x] 20–30 triệu VND/tháng có hai đầu và target 25 triệu.
- [x] Thỏa thuận, một cận hoặc thiếu đơn vị không thành target chính; vẫn giữ cho EDA.
- [x] Không tự đổi ngoại tệ/gross/net; target truy được chứng cứ.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


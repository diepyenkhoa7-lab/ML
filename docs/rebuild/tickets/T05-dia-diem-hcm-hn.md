# T05: Chuẩn hóa HCM/HN và xem bảng alias

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/19). Bằng chứng: job_market/docs/tdd/T05.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng thấy tên địa điểm chuẩn HCM/HN cạnh chuỗi gốc, lọc và xuất theo tên thống nhất.

## Công việc

- [x] Thống kê tên địa điểm trong dữ liệu mới và tạo alias có chứng cứ.
- [x] Chuẩn hóa các biến thể đã xác minh; đánh dấu địa chỉ chưa rõ.
- [x] Hiển thị đối chiếu raw–chuẩn và lọc/xuất.

## Acceptance criteria

- [x] HCM, Hồ Chí Minh, ho chi minh cùng nhận HCM; Hà Nội tương đương nhận HN.
- [x] Không nhận tên đường như Điện Biên Phủ thành tỉnh chỉ từ một cụm từ.
- [x] Địa điểm chưa đủ chứng cứ giữ raw/trạng thái chưa rõ.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


# T23: Upload CSV, ghép cột và xem lỗi chuẩn hóa

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/37). Bằng chứng: job_market/docs/tdd/T23.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng chọn CSV, ghép cột và xem raw–clean cùng lỗi từng dòng trước khi dự đoán.

## Công việc

- [x] Thêm parser CSV và mapping trường hồ sơ.
- [x] Áp dụng chuẩn hóa/validation chung, giữ row ID/thứ tự.
- [x] Hiển thị preview, lỗi và giới hạn file/dòng.

## Acceptance criteria

- [x] Không cắt dòng im lặng; preview đủ row ID và lý do lỗi.
- [x] Alias và quy tắc giống dữ liệu/form đơn.
- [x] Upload không sửa snapshot/model, không train.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


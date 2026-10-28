# T23: Upload CSV, ghép cột và xem lỗi chuẩn hóa

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/37) ngày 28/10/2026. Tính năng: F07. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng chọn CSV, ghép cột và xem raw–clean cùng lỗi từng dòng trước khi dự đoán.

## Công việc

- [ ] Thêm parser CSV và mapping trường hồ sơ.
- [ ] Áp dụng chuẩn hóa/validation chung, giữ row ID/thứ tự.
- [ ] Hiển thị preview, lỗi và giới hạn file/dòng.

## Acceptance criteria

- [ ] Không cắt dòng im lặng; preview đủ row ID và lý do lỗi.
- [ ] Alias và quy tắc giống dữ liệu/form đơn.
- [ ] Upload không sửa snapshot/model, không train.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


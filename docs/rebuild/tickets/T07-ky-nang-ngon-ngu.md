# T07: Bóc tách ngôn ngữ lập trình có bằng chứng

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/21) ngày 28/10/2026. Tính năng: F02. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem các ngôn ngữ lập trình trích từ tin, đoạn bằng chứng và bảng lọc/xuất theo kỹ năng.

## Công việc

- [ ] Tạo quy tắc ranh giới từ và alias từ nguồn mới.
- [ ] Trích ngôn ngữ cùng đoạn chứng cứ, khử lặp trong một tin.
- [ ] Thêm bảng/bộ lọc và kiểm tra các tên dễ nhầm.

## Acceptance criteria

- [ ] Java khác JavaScript; C khác C++ và C#.
- [ ] Một kỹ năng lặp nhiều lần không làm tăng số tin yêu cầu.
- [ ] Không dùng pretrained/LLM để tạo nhãn; mỗi nhãn truy được chứng cứ.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


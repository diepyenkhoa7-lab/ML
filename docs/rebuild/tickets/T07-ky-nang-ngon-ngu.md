# T07: Bóc tách ngôn ngữ lập trình có bằng chứng

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/21). Bằng chứng: job_market/docs/tdd/T07.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng xem các ngôn ngữ lập trình trích từ tin, đoạn bằng chứng và bảng lọc/xuất theo kỹ năng.

## Công việc

- [x] Tạo quy tắc ranh giới từ và alias từ nguồn mới.
- [x] Trích ngôn ngữ cùng đoạn chứng cứ, khử lặp trong một tin.
- [x] Thêm bảng/bộ lọc và kiểm tra các tên dễ nhầm.

## Acceptance criteria

- [x] Java khác JavaScript; C khác C++ và C#.
- [x] Một kỹ năng lặp nhiều lần không làm tăng số tin yêu cầu.
- [x] Không dùng pretrained/LLM để tạo nhãn; mỗi nhãn truy được chứng cứ.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


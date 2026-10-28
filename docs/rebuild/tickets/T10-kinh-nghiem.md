# T10: Chuẩn hóa số năm và khoảng kinh nghiệm

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/24) ngày 28/10/2026. Tính năng: F02. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem kinh nghiệm đã chuẩn hóa, khoảng/cận hoặc trạng thái thiếu, và lọc/xuất để rà soát.

## Công việc

- [ ] Phân tích kinh nghiệm dạng số, khoảng, cận và không yêu cầu.
- [ ] Giữ min/max/kind, phân biệt thiếu với không yêu cầu kinh nghiệm.
- [ ] Thêm đối chiếu UI/export và kiểm tra các định dạng thực.

## Acceptance criteria

- [ ] Thiếu kinh nghiệm không bị gán 0.
- [ ] Khoảng/cận và bằng chứng raw được giữ.
- [ ] Giá trị bất hợp lý có trạng thái/lý do review, không tự sửa không dấu vết.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


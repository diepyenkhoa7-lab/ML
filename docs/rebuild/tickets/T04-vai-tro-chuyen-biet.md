# T04: Bổ sung Data/ML, DevOps và QA Automation

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/18). Bằng chứng: job_market/docs/tdd/T04.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng phân biệt đủ bảy nhóm nghề, gồm ba nhóm chuyên biệt, khi lọc bảng và xuất dữ liệu.

## Công việc

- [x] Thêm ba nhóm cùng quy tắc phân biệt vai trò và kỹ năng.
- [x] Xử lý giao nhau/mơ hồ giữa chức danh, lưu bằng chứng.
- [x] Mở rộng bảng, bộ lọc và kiểm tra cho đủ bảy nhóm.

## Acceptance criteria

- [x] Data/ML, DevOps và QA Automation không bị gộp vào nhóm khác chỉ do từ khóa chung.
- [x] Vai trò mơ hồ có lý do review.
- [x] Đủ bảy nhóm trong UI/export; raw được giữ.

## Blocked by

- T03 — Phân nhóm Backend, Frontend, Fullstack và Mobile

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


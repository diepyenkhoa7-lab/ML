# T03: Phân nhóm Backend, Frontend, Fullstack và Mobile

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/17). Bằng chứng: job_market/docs/tdd/T03.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng xem/lọc bốn nhóm nghề phát triển phần mềm cạnh chức danh gốc và xuất các tin thuộc từng nhóm.

## Công việc

- [x] Xây quy tắc nghề và bằng chứng từ chức danh/mô tả nguồn mới.
- [x] Thêm bộ lọc, bảng đối chiếu và export theo nhóm.
- [x] Đánh dấu chức danh mơ hồ/ngoài phạm vi để review.

## Acceptance criteria

- [x] Bốn nhóm hiển thị riêng với bằng chứng và raw.
- [x] Chức danh không rõ không bị ép vào nhóm tùy ý.
- [x] Bảng lọc/export và các ca kiểm tra nghề đồng nhất.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


# T12: Xem top nhu cầu kỹ năng theo bộ lọc

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/26). Bằng chứng: job_market/docs/tdd/T12.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng lọc nhóm nghề/địa điểm, xem top kỹ năng trong tin cùng bảng và tải PNG/CSV.

## Công việc

- [x] Aggregate kỹ năng theo tin duy nhất và mẫu số rõ.
- [x] Vẽ biểu đồ thật bằng Matplotlib/Seaborn.
- [x] Nối filter, bảng và export cùng dữ liệu.

## Acceptance criteria

- [x] Bảng/biểu đồ khớp số đếm kiểm chứng, kể cả tin nhiều địa điểm.
- [x] Có nguồn, phạm vi, n và ghi nhu cầu quan sát trong dataset.
- [x] PNG/CSV khớp bộ lọc, không dùng số cố định.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


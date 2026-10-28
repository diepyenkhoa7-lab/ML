# T12: Xem top nhu cầu kỹ năng theo bộ lọc

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/26) ngày 28/10/2026. Tính năng: F03. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng lọc nhóm nghề/địa điểm, xem top kỹ năng trong tin cùng bảng và tải PNG/CSV.

## Công việc

- [ ] Aggregate kỹ năng theo tin duy nhất và mẫu số rõ.
- [ ] Vẽ biểu đồ thật bằng Matplotlib/Seaborn.
- [ ] Nối filter, bảng và export cùng dữ liệu.

## Acceptance criteria

- [ ] Bảng/biểu đồ khớp số đếm kiểm chứng, kể cả tin nhiều địa điểm.
- [ ] Có nguồn, phạm vi, n và ghi nhu cầu quan sát trong dataset.
- [ ] PNG/CSV khớp bộ lọc, không dùng số cố định.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


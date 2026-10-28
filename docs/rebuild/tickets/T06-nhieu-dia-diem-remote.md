# T06: Giữ nhiều địa điểm, tách Remote và đếm tin duy nhất

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/20) ngày 28/10/2026. Tính năng: F02. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng lọc một tin ở cả HCM/HN, lọc Remote riêng và thấy tổng số tin không tăng vì tách địa điểm.

## Công việc

- [ ] Lưu tập địa điểm và hình thức làm việc độc lập.
- [ ] Đưa bộ lọc nhiều địa điểm/Remote vào UI và export.
- [ ] Đếm distinct tin, giải thích các nhóm địa điểm chồng lắp.

## Acceptance criteria

- [ ] Tin HCM/HN/Remote giữ hai địa điểm vật lý và Remote riêng.
- [ ] Một tin tính một lần trong tổng, kể cả khi nhiều bộ lọc khớp.
- [ ] UI/export giữ đủ địa điểm và raw; có kiểm tra đếm tay.

## Blocked by

- T05 — Chuẩn hóa HCM/HN và xem bảng alias

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


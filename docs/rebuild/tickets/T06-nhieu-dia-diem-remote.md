# T06: Giữ nhiều địa điểm, tách Remote và đếm tin duy nhất

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/20). Bằng chứng: job_market/docs/tdd/T06.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng lọc một tin ở cả HCM/HN, lọc Remote riêng và thấy tổng số tin không tăng vì tách địa điểm.

## Công việc

- [x] Lưu tập địa điểm và hình thức làm việc độc lập.
- [x] Đưa bộ lọc nhiều địa điểm/Remote vào UI và export.
- [x] Đếm distinct tin, giải thích các nhóm địa điểm chồng lắp.

## Acceptance criteria

- [x] Tin HCM/HN/Remote giữ hai địa điểm vật lý và Remote riêng.
- [x] Một tin tính một lần trong tổng, kể cả khi nhiều bộ lọc khớp.
- [x] UI/export giữ đủ địa điểm và raw; có kiểm tra đếm tay.

## Blocked by

- T05 — Chuẩn hóa HCM/HN và xem bảng alias

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


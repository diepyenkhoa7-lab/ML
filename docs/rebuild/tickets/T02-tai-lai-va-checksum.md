# T02: Tải lại đúng phiên bản dataset và kiểm checksum

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/16). Bằng chứng: job_market/docs/tdd/T02.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng tải đúng revision nguồn mới bằng lệnh, rồi thấy phiên bản và kết quả kiểm tra toàn vẹn trong dashboard.

## Công việc

- [x] Ghi URL/revision/checksum và loại thời gian của nguồn.
- [x] Thêm lệnh tải có kiểm checksum, trạng thái thành công/lỗi và tái sử dụng bản khớp.
- [x] Hiển thị nguồn, giấy phép/điều kiện phân phối và trạng thái phiên bản.

## Acceptance criteria

- [x] Tải lại tạo nội dung khớp manifest hoặc báo nguồn đã thay đổi.
- [x] Phân biệt ngày đăng, cập nhật, hạn nộp và tải.
- [x] Phiên bản nguồn trên UI khớp file thật và có chứng cứ quyền dùng/bàn giao.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


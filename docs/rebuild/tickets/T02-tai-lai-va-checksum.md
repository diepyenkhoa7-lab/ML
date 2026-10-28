# T02: Tải lại đúng phiên bản dataset và kiểm checksum

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/16) ngày 28/10/2026. Tính năng: F01. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng tải đúng revision nguồn mới bằng lệnh, rồi thấy phiên bản và kết quả kiểm tra toàn vẹn trong dashboard.

## Công việc

- [ ] Ghi URL/revision/checksum và loại thời gian của nguồn.
- [ ] Thêm lệnh tải có kiểm checksum, trạng thái thành công/lỗi và tái sử dụng bản khớp.
- [ ] Hiển thị nguồn, giấy phép/điều kiện phân phối và trạng thái phiên bản.

## Acceptance criteria

- [ ] Tải lại tạo nội dung khớp manifest hoặc báo nguồn đã thay đổi.
- [ ] Phân biệt ngày đăng, cập nhật, hạn nộp và tải.
- [ ] Phiên bản nguồn trên UI khớp file thật và có chứng cứ quyền dùng/bàn giao.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


# T25: Hỗ trợ cùng quy trình upload với XLSX

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/39) ngày 28/10/2026. Tính năng: F07. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng tải XLSX, ghép cột, rà lỗi, dự đoán và xuất kết quả tương đương CSV.

## Công việc

- [ ] Thêm đọc XLSX và chính sách sheet/cột được hiển thị.
- [ ] Tái dùng mapping/validation/inference đang có.
- [ ] Thử XLSX có dòng đúng/sai và so với CSV tương đương.

## Acceptance criteria

- [ ] CSV/XLSX tương đương cho cùng prediction/trạng thái và thứ tự.
- [ ] File lỗi/rỗng/quá giới hạn có thông báo rõ.
- [ ] Không thực thi nội dung file hay nạp model từ upload.

## Blocked by

- T24 — Dự đoán hàng loạt CSV và xuất toàn bộ kết quả

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


# T24: Dự đoán hàng loạt CSV và xuất toàn bộ kết quả

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/38) ngày 28/10/2026. Tính năng: F07. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Từ CSV đã ghép cột, người dùng dự đoán dòng hợp lệ và tải kết quả của mọi dòng theo thứ tự gốc.

## Công việc

- [ ] Gọi model đã lưu cho dòng hợp lệ.
- [ ] Gộp prediction và lỗi theo row ID, giữ thứ tự.
- [ ] Xuất CSV có đơn vị/version/trạng thái; thử luồng trong trình duyệt.

## Acceptance criteria

- [ ] Đủ số dòng, dòng lỗi vẫn có lý do và không có prediction giả.
- [ ] Dòng hợp lệ khớp form đơn trên cùng hồ sơ.
- [ ] Artifact/snapshot trước và sau không đổi.

## Blocked by

- T23 — Upload CSV, ghép cột và xem lỗi chuẩn hóa
- T20 — Cảnh báo hồ sơ chưa đủ hỗ trợ khi dự đoán

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


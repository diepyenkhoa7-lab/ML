# T27: Cài mới và kiểm tra trọn demo offline

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/41) ngày 28/10/2026. Tính năng: F08. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người báo cáo cài từ gói nộp và demo biểu đồ, model, dự đoán, tư vấn, upload/export trên máy khi nguồn mạng bị tắt.

## Công việc

- [ ] Cài trong môi trường mới theo tài liệu.
- [ ] Chạy lệnh kiểm tra chung và thực hiện các luồng thật trong trình duyệt.
- [ ] Ghi bằng chứng, giới hạn và sửa lỗi thuộc gói mới nếu phát hiện.

## Acceptance criteria

- [ ] Biểu đồ/modelcomparison/predict/advice/CSV/XLSX/export chạy được từ gói nộp.
- [ ] Inference/biểu đồ demo không cần gọi nguồn ngoài, model nạp đúng artifact.
- [ ] Kết quả và giới hạn ghi theo thực thi; không dùng log startup thay smoke.

## Blocked by

- T26 — Tạo gói mã nguồn, dataset và artifact có manifest

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


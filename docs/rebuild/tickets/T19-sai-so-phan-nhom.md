# T19: Xem sai số theo nhóm nghề và dữ liệu

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/33) ngày 28/10/2026. Tính năng: F05. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem sai số và số mẫu theo nhóm để hiểu model hoạt động ở đâu.

## Công việc

- [ ] Tạo báo cáo sai số phân nhóm từ nhãn/prediction đã lưu.
- [ ] Hiển thị n, metric và trạng thái ít mẫu.
- [ ] Cho xuất bảng và kiểm tra metric tính lại.

## Acceptance criteria

- [ ] Metric nhóm tính từ tập đánh giá đã chốt, có n và đơn vị.
- [ ] Không diễn giải nhóm quá ít mẫu như kết luận chắc chắn.
- [ ] Tổng và nhóm truy được về prediction/nhãn thực.

## Blocked by

- T18 — Huấn luyện model thứ hai và so sánh metric
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


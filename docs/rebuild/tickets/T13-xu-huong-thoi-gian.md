# T13: Xem xu hướng khi đủ thời gian nguồn

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/27) ngày 28/10/2026. Tính năng: F03. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem thay đổi theo kỳ thời gian so sánh được, hoặc thấy lý do nguồn chưa đủ để kết luận xu hướng.

## Công việc

- [ ] Kiểm tra ngày/năm nguồn và độ phủ các kỳ.
- [ ] So sánh phạm vi nguồn/nhóm tin tương thích.
- [ ] Hiển thị biểu đồ/bảng/export hoặc trạng thái thiếu bằng chứng.

## Acceptance criteria

- [ ] Ngày đăng khác deadline/cập nhật/tải.
- [ ] Không dựng xu hướng nhiều năm từ các snapshot không so sánh được.
- [ ] Kỳ thiếu dữ liệu và thay đổi phạm vi nguồn được chỉ rõ.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


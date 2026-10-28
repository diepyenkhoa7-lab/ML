# T22: Bổ sung bằng chứng lương cho kỹ năng nên học

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/36) ngày 28/10/2026. Tính năng: F06. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem thêm liên hệ lương và chênh lệch dự đoán của kỹ năng theo cách xếp hạng đã chốt.

## Công việc

- [ ] Kết hợp tín hiệu lương/nhu cầu theo quyết định tư vấn.
- [ ] Giữ hồ sơ nền khi thử thêm từng kỹ năng.
- [ ] Hiển thị/xuất các tín hiệu riêng và giới hạn diễn giải.

## Acceptance criteria

- [ ] Số liệu lương/thống kê và delta model được phân biệt, truy được nguồn/train.
- [ ] Không dùng test để tối ưu danh sách.
- [ ] Save/reload tái lập gợi ý; không trình bày delta như hiệu quả nhân quả chắc chắn.

## Blocked by

- T21 — Gợi ý kỹ năng còn thiếu theo nhu cầu nghề
- [Chốt bằng chứng và cách xếp hạng kỹ năng nên học](https://github.com/theihoz/ML/issues/5)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


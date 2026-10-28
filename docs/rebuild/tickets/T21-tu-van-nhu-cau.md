# T21: Gợi ý kỹ năng còn thiếu theo nhu cầu nghề

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/35) ngày 28/10/2026. Tính năng: F06. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng nhận kỹ năng chưa có phù hợp nhóm nghề, kèm số tin yêu cầu và chứng cứ.

## Công việc

- [ ] Tạo bằng chứng nhu cầu từ train theo quyết định tư vấn.
- [ ] Loại kỹ năng đã có/alias và áp dụng ngưỡng hỗ trợ.
- [ ] Hiển thị lý do/số tin hoặc trạng thái thiếu dữ liệu.

## Acceptance criteria

- [ ] Không gợi ý lại kỹ năng đã có.
- [ ] Danh sách phụ thuộc hồ sơ và train; không dùng test hoặc danh sách cố định.
- [ ] Mỗi gợi ý có bằng chứng và không hứa tăng lương.

## Blocked by

- T20 — Cảnh báo hồ sơ chưa đủ hỗ trợ khi dự đoán
- [Chốt bằng chứng và cách xếp hạng kỹ năng nên học](https://github.com/theihoz/ML/issues/5)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


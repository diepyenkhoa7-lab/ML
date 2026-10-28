# T16: Xếp hạng kỹ năng theo lương có số mẫu

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/30) ngày 28/10/2026. Tính năng: F03. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem kỹ năng có lương quan sát cao trong phạm vi dữ liệu, kèm n và giới hạn diễn giải.

## Công việc

- [ ] Tính thống kê kỹ năng trên target hợp lệ và phạm vi filter.
- [ ] Áp dụng ngưỡng hỗ trợ để xếp hạng.
- [ ] Vẽ bảng/biểu đồ và xuất kết quả có nguồn.

## Acceptance criteria

- [ ] Không đưa kỹ năng một mẫu lên top mà bỏ qua chính sách hỗ trợ.
- [ ] Ghi rõ liên hệ quan sát, không khẳng định học kỹ năng gây tăng lương.
- [ ] Bảng/PNG/CSV có n, đơn vị và phạm vi thống nhất.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


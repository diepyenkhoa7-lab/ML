# T14: Xem tương quan kinh nghiệm và lương

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/28) ngày 28/10/2026. Tính năng: F03. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng xem scatter/tương quan kinh nghiệm–lương theo nhóm và tải bảng/ảnh có đơn vị.

## Công việc

- [ ] Chọn bản ghi đủ nhãn và kinh nghiệm theo chính sách đã chốt.
- [ ] Vẽ Matplotlib/Seaborn với n/phạm vi rõ.
- [ ] Nối filter, bảng và export.

## Acceptance criteria

- [ ] Dùng lương quan sát hợp lệ, đơn vị VND/tháng.
- [ ] Bảng/ảnh phản ánh cùng bản ghi và bộ lọc.
- [ ] Khoảng kinh nghiệm, ngoại lệ và nhóm ít mẫu được giải thích theo quy tắc.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


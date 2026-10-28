# T15: So sánh lương theo vai trò và khu vực

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/29) ngày 28/10/2026. Tính năng: F03. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng so sánh phân bố lương giữa bảy nhóm nghề và các khu vực với số mẫu hỗ trợ.

## Công việc

- [ ] Tạo thống kê theo nghề/địa điểm từ target hợp lệ.
- [ ] Vẽ biểu đồ so sánh và bảng n.
- [ ] Cho lọc/xuất và ghi rõ nhóm địa điểm chồng lắp.

## Acceptance criteria

- [ ] Vai trò/khu vực/đơn vị không bị cộng lẫn.
- [ ] Nhóm ít mẫu theo ngưỡng đã chốt có trạng thái rõ.
- [ ] Filter/export khớp, số tin duy nhất không bị tăng vì địa điểm.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


# T26: Tạo gói mã nguồn, dataset và artifact có manifest

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/40) ngày 28/10/2026. Tính năng: F08. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người báo cáo nhận gói dự án mới có đủ dữ liệu được phép phân phối, model, metric và hướng dẫn.

## Công việc

- [ ] Đóng gói chỉ đầu ra của bản mới và hồ sơ quyền dữ liệu.
- [ ] Tạo manifest/hash và hướng dẫn cài/chuẩn hóa/train/demo.
- [ ] Đối chiếu từng yêu cầu đề bài với đầu ra trong gói.

## Acceptance criteria

- [ ] Có dataset CSV/JSON/XLSX theo đề, không chỉ URL tải.
- [ ] Mã/model/metric/manifest đều thuộc bản mới, kiểm tra được hash.
- [ ] Thiếu mục nào phải ghi chưa đạt, không thay bằng kết quả cũ.

## Blocked by

- T12 — Xem top nhu cầu kỹ năng theo bộ lọc
- T13 — Xem xu hướng khi đủ thời gian nguồn
- T14 — Xem tương quan kinh nghiệm và lương
- T15 — So sánh lương theo vai trò và khu vực
- T16 — Xếp hạng kỹ năng theo lương có số mẫu
- T19 — Xem sai số theo nhóm nghề và dữ liệu
- T22 — Bổ sung bằng chứng lương cho kỹ năng nên học
- T25 — Hỗ trợ cùng quy trình upload với XLSX

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


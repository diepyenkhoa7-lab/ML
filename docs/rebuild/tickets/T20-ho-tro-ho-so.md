# T20: Cảnh báo hồ sơ chưa đủ hỗ trợ khi dự đoán

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/34) ngày 28/10/2026. Tính năng: F05. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng nhập hồ sơ và nhận prediction hoặc trạng thái/cảnh báo theo mức dữ liệu hỗ trợ.

## Công việc

- [ ] Áp dụng chính sách đầu vào thiếu/sai, alias và giá trị chưa gặp.
- [ ] Thêm trạng thái hỗ trợ, phiên bản model/dữ liệu và đơn vị.
- [ ] Thử form thực cùng CLI với các hồ sơ đúng/sai/ít bằng chứng.

## Acceptance criteria

- [ ] CLI và UI dùng cùng preprocessing/model, cho kết quả nhất quán.
- [ ] Hồ sơ ngoài hỗ trợ không luôn nhận số vô điều kiện.
- [ ] Không trả NaN/Inf/lương âm; lỗi artifact/schema/version rõ.

## Blocked by

- T18 — Huấn luyện model thứ hai và so sánh metric
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


# T17: Huấn luyện model đầu tiên và dự đoán một hồ sơ

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/31) ngày 28/10/2026. Tính năng: F04. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng train model đầu tiên bằng lệnh rồi nhập một hồ sơ trên Streamlit để dự đoán từ artifact đã lưu.

## Công việc

- [ ] Chia tập theo quyết định đánh giá; fit preprocessing chỉ train.
- [ ] Huấn luyện model đầu tiên, lưu cấu hình/seed/snapshot/metric.
- [ ] Nạp artifact vào form dự đoán đơn và kiểm tra reload tiến trình mới.

## Acceptance criteria

- [ ] Nguồn mới, nhóm trùng không giao tập; feature không chứa lương target.
- [ ] Metric tính thật; cấu hình và số mẫu được lưu.
- [ ] Prediction sau reload và qua form khớp probe trong dung sai công bố.

## Blocked by

- T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


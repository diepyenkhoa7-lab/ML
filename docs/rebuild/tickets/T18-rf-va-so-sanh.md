# T18: Huấn luyện model thứ hai và so sánh metric

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/32) ngày 28/10/2026. Tính năng: F04. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng train model thứ hai, xem bảng so sánh hai model và model được chọn bằng validation.

Cập nhật local theo quyết định 29/10: model thứ hai là Linear Regression (OLS), so với Ridge của T17; MAE chính, RMSE phụ. Tên file cũ giữ để không làm hỏng các liên kết hiện có. Chưa cập nhật bản issue trên GitHub trong giai đoạn giữ ML ở local.

## Công việc

- [ ] Huấn luyện Linear Regression tự học từ cùng snapshot/tập chia với Ridge.
- [ ] Tính ít nhất hai metric theo tiêu chí đã chốt.
- [ ] Hiển thị so sánh, lựa chọn validation và test riêng trên dashboard.

## Acceptance criteria

- [ ] Có ít nhất hai model tự huấn luyện và hai metric thực.
- [ ] Cùng tập đánh giá; không dùng test để chọn model.
- [ ] UI/ảnh/bảng metric khớp prediction/nhãn lưu; không gán sẵn model thắng.

## Blocked by

- T17 — Huấn luyện model đầu tiên và dự đoán một hồ sơ

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


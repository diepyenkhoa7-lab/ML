# F08: Bàn giao và demo tái lập trên máy

Trạng thái: đã được người dùng duyệt và đăng [spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/14) ngày 28/10/2026. Các quyết định phụ thuộc dataset vẫn chờ chốt qua wayfinder.

## Problem Statement

Mã nguồn chạy trên máy phát triển chưa đủ chứng minh gói nộp có dữ liệu và app demo hoàn chỉnh.

## Solution

Gói chỉ chứa dự án mới, dữ liệu được phép phân phối, model đã đánh giá, cấu hình/tài liệu và kịch bản demo kiểm tra từ môi trường mới.

## User Stories

1. Là người dùng dự án, tôi muốn cài và mở app theo hướng dẫn để demo trực tiếp trên máy.
2. Là người dùng dự án, tôi muốn dùng dataset trong gói nộp để đáp ứng sản phẩm bàn giao.
3. Là người dùng dự án, tôi muốn dự đoán, tư vấn và upload khi nguồn mạng không có để demo ổn định.
4. Là người dùng dự án, tôi muốn kiểm tra manifest và kết quả thực để biết gói nộp đầy đủ.

## Implementation Decisions

- Gói dữ liệu và quyền phân phối phải được chốt với nguồn mới; đường dẫn tải không thay thế dataset bắt buộc nếu rubric yêu cầu file.
- Có lệnh kiểm tra chung chạy lint, hợp đồng dữ liệu/model và smoke app; tích hợp CI cho bản mới.
- Tài liệu ghi rõ số mẫu, nguồn, thời gian, đơn vị, metric thực và giới hạn.
- Quy trình đóng gói chỉ lấy đầu ra bản mới, kiểm tra lại từ gói nộp và môi trường sạch.

## Testing Decisions

- Cài từ đầu, nạp model, xem biểu đồ, dự đoán, tư vấn, upload CSV/XLSX và export thành công.
- Thử demo offline, đối chiếu checksum dataset/model với manifest.
- Kiểm tra toàn bộ yêu cầu III–V có đầu ra và bằng chứng thực, không dùng log startup thay smoke.

## Out of Scope

Deploy cloud, mua quyền dữ liệu hoặc tạo báo cáo Word chưa được yêu cầu.

## Further Notes

Yêu cầu V. Công việc T26–T27.


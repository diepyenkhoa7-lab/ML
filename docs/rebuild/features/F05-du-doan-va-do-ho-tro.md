# F05: Dự đoán lương và giải thích giới hạn

Trạng thái: đã được người dùng duyệt và đăng [spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/11) ngày 28/10/2026. Các quyết định phụ thuộc dataset vẫn chờ chốt qua wayfinder.

## Problem Statement

Người dùng cần ước tính lương và hiểu khi hồ sơ thiếu hoặc khác quá xa dữ liệu hỗ trợ.

## Solution

Form vai trò, kinh nghiệm, kỹ năng, địa điểm và hình thức làm việc; model đã lưu trả kết quả có đơn vị, phiên bản và trạng thái hỗ trợ.

## User Stories

1. Là người dùng dự án, tôi muốn nhập hồ sơ và nhận dự đoán lương chào tuyển để tham khảo.
2. Là người dùng dự án, tôi muốn biết đơn vị, dữ liệu và model tạo ra kết quả để giải thích.
3. Là người dùng dự án, tôi muốn nhận thông báo trường sai hoặc thiếu thay vì kết quả vô nghĩa.
4. Là người dùng dự án, tôi muốn xem sai số theo nhóm và cảnh báo ít bằng chứng để cân nhắc kết quả.

## Implementation Decisions

- Inference dùng chính artifact đã đánh giá, cùng preprocessing; dashboard không train.
- Ngưỡng hỗ trợ và hành vi từ chối/cảnh báo được chốt sau kiểm toán nguồn.
- Giá trị âm, không hữu hạn hoặc schema/model lệch phiên bản phải có lỗi rõ.
- Kết quả là ước tính trong phạm vi dữ liệu; không trình bày như lương thực nhận hay khoảng tin cậy nếu chưa hiệu chuẩn.

## Testing Decisions

- Hồ sơ qua CLI và dashboard có cùng prediction, đơn vị và phiên bản.
- Kiểm tra đầu vào lỗi, kỹ năng/địa điểm chưa gặp, nhóm ít mẫu và artifact không tương thích.
- Dashboard hiển thị metric khớp báo cáo đánh giá thực và không sửa artifact khi dự đoán.

## Out of Scope

Khẳng định độ chính xác trước đánh giá; suy lương ngoài phạm vi mà không thông báo.

## Further Notes

Yêu cầu III.4. Công việc T19–T20.


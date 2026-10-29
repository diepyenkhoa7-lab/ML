# M02 — Snapshot, chia tập và chống rò nhãn

## Problem Statement

Model có thể đạt metric tốt giả tạo nếu học bản sao của test, fit encoder trên dữ liệu giữ lại hoặc đọc tiền lương trong nội dung tin.

## Solution

Khóa một snapshot đủ nhãn, tạo split có nhóm và feature schema minh bạch; hai model dùng chung các phân hoạch.

## User Stories

1. Là người huấn luyện, tôi muốn biết row nào ở split nào và vì sao, để kiểm toán leakage.
2. Là người huấn luyện, tôi muốn mọi transformation chỉ học từ train, để đánh giá độc lập.
3. Là người dùng, tôi muốn cùng một hồ sơ được mã hóa giống nhau khi train và predict, để kết quả nhất quán.

## Implementation Decisions

- Allowlist role, biểu diễn kinh nghiệm, skills, tập địa điểm và work mode. Không dùng raw title/JD, lương/cận lương/target, ID/URL, công ty hoặc source làm shortcut dự đoán; công ty/nguồn/thời gian chỉ phục vụ nhóm, audit và báo cáo theo policy.
- Không explode một tin nhiều địa điểm/kỹ năng thành nhiều training observations. Thực thể trùng và nhóm đăng lại không giao split; các trường mâu thuẫn không được giải quyết bằng giữ dòng đầu.
- Cách chia tập và threshold do #4 chốt sau kiểm toán. Đề xuất grouped split seed 42; không ép tỷ lệ bằng cách cắt nhóm. Lưu số mẫu, nhóm, nguồn, nghề và thời gian thực tế của mỗi phần.
- Static alias catalog đóng phiên bản; vocab/encoder, imputer và scaler fit train. Giữ missing indicator và kind của khoảng/cận, không biến thiếu thành 0 năm hoặc coi một cận là số năm chính xác.
- Chính sách biểu diễn experience và basis phải có phiên bản. Unknown/OOV ghi rõ; không tự bổ sung category từ test hoặc từ hồ sơ upload vào model đã lưu.

## Testing Decisions

Test ranh giới service: nhóm không giao, seed/cấu hình tái lập, một entity một quan sát, held-out-only skill không thành vocabulary train, thay giá trị test không đổi preprocessing đã fit. Fixture chỉ kiểm logic split/schema; fit thực chờ nhãn thật được chấp nhận.

## Out of Scope

Dùng target/text lương làm feature, pretrained embedding, chọn split có metric cao nhất sau khi nhìn test.

## Further Notes

Làm rõ F04/T17, bị chặn bởi M01 và quyết định #4. Không tự đổi split hoặc threshold trong ticket hiện tại khi chưa có quyết định tương ứng.

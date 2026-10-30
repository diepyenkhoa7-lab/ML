# F03: Phân tích tuyển dụng và trực quan hóa lương

Trạng thái: đã được người dùng duyệt và đăng [spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/9) ngày 28/10/2026. Các quyết định phụ thuộc dataset vẫn chờ chốt qua wayfinder.

## Problem Statement

Người dùng cần biểu đồ phản ánh đúng dữ liệu tuyển dụng, không nhầm tần suất kỹ năng, lương và xu hướng theo thời gian.

## Solution

Dashboard dùng Matplotlib/Seaborn, có bộ lọc, bảng số liệu kèm biểu đồ và xuất kết quả có nguồn/đơn vị.

## User Stories

1. Là người dùng dự án, tôi muốn xem top kỹ năng trong tin tuyển dụng và số tin hỗ trợ để nhận diện nhu cầu quan sát được.
2. Là người dùng dự án, tôi muốn xem lương theo kỹ năng, nghề và khu vực để so sánh đúng nhóm.
3. Là người dùng dự án, tôi muốn xem tương quan kinh nghiệm–lương để hiểu phân bố.
4. Là người dùng dự án, tôi muốn xem biến động thời gian khi nguồn đủ điều kiện, hoặc lý do chưa thể so sánh.

## Implementation Decisions

- Tách thống kê tuyển dụng trên tin đủ điều kiện EDA khỏi thống kê lương trên tin có target hợp lệ.
- Mỗi tin chỉ được đếm một lần trong tổng; nhóm địa điểm có thể chồng lắp nên tổng nhóm không cộng thành tổng thị trường.
- Mọi biểu đồ có đơn vị, n, thời gian và nguồn; top lương có ngưỡng hỗ trợ đã chốt.
- So sánh năm chỉ trên phạm vi nguồn/nhóm tin có thể đối chiếu; nếu không đủ thì hiển thị trạng thái thiếu bằng chứng.

## Testing Decisions

- Đối chiếu bảng aggregate với một tập kiểm tra đếm tay được, kể cả tin hai địa điểm.
- Bộ lọc cập nhật cả bảng, biểu đồ và file xuất thống nhất.
- Kiểm tra ảnh PNG được tạo thực bằng Matplotlib/Seaborn, có nhãn đọc được và không dùng số cố định.

## Out of Scope

Suy ra toàn thị trường từ một nguồn; gán năm tải cho tin thiếu ngày đăng.

## Further Notes

Yêu cầu III.2 và phần kỹ năng có giá trị thu nhập của III.3. Công việc T12–T16.


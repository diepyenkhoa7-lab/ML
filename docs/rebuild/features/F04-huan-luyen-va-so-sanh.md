# F04: Tự huấn luyện và so sánh ít nhất hai mô hình

Trạng thái: đã được người dùng duyệt và đăng [spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/10) ngày 28/10/2026. Các quyết định phụ thuộc dataset vẫn chờ chốt qua wayfinder.

## Problem Statement

Đề bài cần mô hình thực học từ dữ liệu dự án và kết quả so sánh có thể tái lập.

## Solution

Lệnh huấn luyện tạo snapshot, chia tập, preprocessing và artifact model; dashboard hiển thị metric tính thực trên cùng tập đánh giá.

## User Stories

1. Là người dùng dự án, tôi muốn huấn luyện lại theo cấu hình và seed để tái lập kết quả.
2. Là người dùng dự án, tôi muốn so sánh ít nhất hai model trên cùng dữ liệu để chọn phù hợp.
3. Là người dùng dự án, tôi muốn xem ít nhất hai metric cùng đơn vị để hiểu sai số.
4. Là người dùng dự án, tôi muốn biết cấu hình nào được chọn bằng validation để giữ test độc lập.

## Implementation Decisions

- Đề xuất Ridge và Random Forest, metric MAE/RMSE/R² và chọn validation MAE; chờ quyết định đánh giá trước triển khai.
- Chia tập theo nhóm tin/nguồn thời gian đã chốt; preprocessing chỉ fit train.
- Artifact ghi hash dữ liệu, cấu hình, seed, feature schema và model; train tạo run mới.
- Feature chỉ dùng thông tin người dùng có thể nhập, loại nội dung/đặc trưng chứa lương target.

## Testing Decisions

- Phát hiện nhóm trùng giữa các tập, feature rò nhãn và encoder fit ngoài train.
- Đo metric lại từ prediction/nhãn, hai model dùng cùng tập, test không tham gia chọn cấu hình.
- Nạp model/preprocessing trong tiến trình mới và tái lập prediction probe.

## Out of Scope

Pretrained/fine-tune; điền sẵn metric; dùng fixture tổng hợp để công bố độ chính xác.

## Further Notes

Yêu cầu III.3 và IV. Công việc T17–T18. Chờ quyết định đánh giá.


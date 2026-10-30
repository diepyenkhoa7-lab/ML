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

- Cập nhật quyết định người dùng 29/10: Ridge + Linear Regression, MAE là metric chính, RMSE là metric phụ; chọn bằng validation MAE, test riêng cho đánh giá cuối.
- Validation MAE bằng nhau chọn Linear Regression; chỉ promote model đã chọn nếu MAE nhỏ hơn baseline trung vị train trên cả validation và test. Nếu không đạt, giữ báo cáo nhưng không dùng test để chọn/chỉnh lại model.
- Chia theo công ty, các tin trùng/đăng lại cùng tập; tỷ lệ mục tiêu 70/15/15, seed 42; preprocessing chỉ fit train. Không cắt nhóm để ép tỷ lệ.
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


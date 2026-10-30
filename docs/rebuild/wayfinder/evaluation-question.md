## Question

Cập nhật các vòng quyết định 29/10: chia theo công ty, tin trùng/đăng lại luôn cùng tập; tỷ lệ mục tiêu 70/15/15, seed 42; Ridge + Linear Regression; MAE chính, RMSE phụ; chọn validation MAE, bằng nhau chọn Linear Regression (ADR 0008). Chỉ promote nếu MAE tốt hơn baseline trung vị train trên cả validation và test; test không đạt giữ báo cáo, không dùng để đổi model/tham số. Hồ sơ thiếu hỗ trợ không trả kết quả. Các nguyên tắc đã thống nhất; ngưỡng hỗ trợ bằng số và điều kiện dữ liệu cần khóa trước fit. Chưa đóng issue từ xa hoặc mở train.

Dựa trên dataset mới đã được kiểm tra, cách chia train/validation/test nào đo đúng khả năng dự đoán lương cho hồ sơ chưa gặp, kiểm soát tin trùng và ảnh hưởng thời gian, và vẫn đủ mẫu cho các nhóm nghề chính?

Phần còn phụ thuộc dữ liệu: quy tắc đối chiếu danh tính công ty/nhóm trùng, ngưỡng hỗ trợ và biểu diễn dữ liệu thiếu trước fit. Không khôi phục phương án mô hình cũ hoặc tự thay chia theo công ty đã được xác nhận.

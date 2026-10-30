## Question

Cập nhật các vòng quyết định 29/10: ưu tiên chênh lệch dự đoán của model được chọn; candidate đủ hỗ trợ, delta > 0; tối đa ba, tie-break n train rồi tên chuẩn; thiếu bằng chứng thì không gợi ý (ADR 0009). Ngưỡng hỗ trợ bằng số chờ dữ liệu mở rộng và khóa trước fit. Không đóng #5 hoặc mở train ở vòng này.

Ứng dụng nên xếp hạng kỹ năng nên học bằng bằng chứng nào để kết hợp nhu cầu tuyển dụng và liên hệ với lương, đồng thời phản hồi rõ khi dữ liệu của vai trò, kinh nghiệm hoặc địa điểm còn ít?

Đề xuất để thảo luận: tối đa ba kỹ năng người dùng chưa có, kèm số tin hỗ trợ, thống kê lương quan sát và chênh lệch dự đoán khi bổ sung kỹ năng; chỉ dùng phần dữ liệu huấn luyện cho việc xếp hạng. Cần chốt cách ưu tiên giữa các tín hiệu, ngưỡng hỗ trợ sau kiểm toán nguồn, và cách ghi rõ đây là gợi ý dựa trên liên hệ quan sát/dự đoán.

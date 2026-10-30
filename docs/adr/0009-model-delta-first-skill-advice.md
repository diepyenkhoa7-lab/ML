# Ưu tiên chênh lệch dự đoán khi tư vấn kỹ năng

Ngày 29/10/2026, người dùng chọn ưu tiên chênh lệch dự đoán của model để xếp hạng kỹ năng nên học, thay cho ưu tiên số tin nhắc kỹ năng. So sánh một hồ sơ nền với chính hồ sơ đó khi bổ sung từng kỹ năng chưa có; giữ nguyên vai trò, kinh nghiệm, địa điểm và phạm vi/basis lương.

Đây là chênh lệch model, không phải bằng chứng học kỹ năng gây tăng thu nhập. Candidate và số tin hỗ trợ chỉ lấy từ train của run đã khóa. Model hoặc hồ sơ không đủ hỗ trợ thì không sinh delta để xếp hạng; không tự chuyển sang danh sách cố định hay dùng test để tối ưu tư vấn.

Ở vòng tiếp theo, người dùng đồng ý: chỉ giữ kỹ năng đủ hỗ trợ và delta > 0; xếp giảm dần theo delta của model được chọn; tối đa ba gợi ý. Delta bằng nhau thì ưu tiên số tin train hỗ trợ nhiều hơn, rồi tên chuẩn của kỹ năng. Nếu không có ứng viên hợp lệ hoặc hồ sơ thiếu hỗ trợ, trả lý do thiếu bằng chứng, không trả con số lương/tư vấn thay thế.

Ngưỡng hỗ trợ bằng số còn cần dữ liệu mở rộng để chốt trước fit. Quyết định này không tự chọn một ngưỡng bất kỳ hoặc mở gate #42. Delta và điều kiện hỗ trợ được kiểm trên cả hồ sơ nền và hồ sơ thêm kỹ năng, cùng artifact/phạm vi/basis lương.

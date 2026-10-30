# Đánh giá trên công ty chưa xuất hiện trong train

Ngày 29/10/2026, người dùng chọn chia theo công ty; tin trùng hoặc đăng lại luôn nằm cùng tập. Mục tiêu đánh giá là dự đoán lương chào tuyển ở nhà tuyển dụng chưa có trong train, thay vì chỉ một tin mới từ công ty đã gặp.

Một công ty được chuẩn hóa danh tính không giao train/validation/test. Liên kết trùng/đăng lại cũng phải giữ cùng tập; khi các ràng buộc nối nhiều công ty vào cùng nhóm, giữ cả nhóm thay vì cắt bản sao qua các tập. Chưa rõ danh tính công ty hoặc quan hệ tin thì review trước split; không tự coi recruiter và khách hàng là một công ty.

Người dùng chọn MAE làm metric chính. Ở vòng cấu hình tiếp theo, người dùng sửa cặp mô hình thành Ridge + Linear Regression; các phần còn lại của gói đánh giá giữ tỷ lệ mục tiêu 70/15/15, seed 42, chọn bằng validation MAE và báo MAE/RMSE trên test riêng. Tỷ lệ là mục tiêu, không cắt nhóm công ty hoặc nhóm trùng để ép đúng số dòng.

Người dùng đồng ý không trả lương/tư vấn khi hồ sơ ngoài phạm vi hoặc không đủ mẫu hỗ trợ. Ngưỡng mẫu cụ thể phải dựa vào dữ liệu mở rộng và khóa trước fit. Hai nhãn đã duyệt hiện cùng một công ty nên không đủ phép đánh giá này và không mở training.

Ở vòng cuối, người dùng xác nhận tiêu chí lựa chọn/phát hành: chọn validation MAE nhỏ hơn; bằng nhau chọn Linear Regression. So sánh trên giá trị chưa làm tròn hiển thị. Baseline là trung vị target của train trong cùng cohort/basis/phạm vi thu nhập, không học từ validation/test. Model đã chọn chỉ được dùng cho demo/tư vấn khi MAE nhỏ hơn baseline trên cả validation và test của cùng split. RMSE vẫn được báo như metric phụ, không thay thứ tự lựa chọn MAE.

Nếu test không đạt, giữ báo cáo/run/model để kiểm toán nhưng không promote để tư vấn. Không đổi sang model khác hoặc chỉnh tham số bằng kết quả test. Không lặp thử các cấu hình trên cùng test để tìm bản đạt. Đây là tiêu chí phát hành của dự án, không chứng minh đủ độ chính xác tuyệt đối cho mọi hồ sơ hoặc bảo đảm tăng thu nhập.

Các nguyên tắc #4 đã thống nhất. Tham số hỗ trợ và cấu hình phụ thuộc dữ liệu vẫn cần khóa trước fit; ghi chép này không đóng issue từ xa, mở gate #42 hoặc tự thực thi training.

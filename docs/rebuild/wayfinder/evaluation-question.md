## Question

Dựa trên dataset mới đã được kiểm tra, cách chia train/validation/test nào đo đúng khả năng dự đoán lương cho hồ sơ chưa gặp, kiểm soát tin trùng và ảnh hưởng thời gian, và vẫn đủ mẫu cho các nhóm nghề chính?

Cần chốt cách nhóm tin gốc/tin gần trùng, vai trò của công ty và thời gian, các nhóm cần báo cáo riêng, tiêu chí low-support, và cách xử lý hồ sơ ngoài phạm vi hỗ trợ. Đề xuất khởi đầu để thảo luận là Ridge và Random Forest tự huấn luyện, dùng MAE/RMSE/R², chọn model bằng validation MAE và giữ test riêng; đây chưa phải kết quả hay quyết định người dùng đã duyệt.

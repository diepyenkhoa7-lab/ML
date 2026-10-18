# Bảng demo Gemma mô tả dài

File JSON có 3 dòng: mô tả đầy đủ từ tin train `tinixai:263594`, một job-card silver từ corpus replay cũ, rồi lặp lại dòng đầu. Đây là dữ liệu minh họa từ train, không phải test độc lập. Dòng đầu vượt ngân sách context cũ 1.024 token khi tính cả 256 token dành cho đáp án.

Địa chỉ/câu yêu cầu được giữ trong nội dung nguồn. Tin dài có khoảng lương header khác câu benefits; không dùng lương Gemma trích để tính MAE. Tên kỹ năng nguồn và nhãn silver có thể thiếu/mơ hồ. Mục đích là kiểm tra nhập file, đọc mô tả, giữ dòng trùng, sinh dự đoán/biểu đồ và tải ZIP. Không dùng bảng này để công bố độ chính xác model.

Nhập file trên web, ghép `description` vào Mô tả tuyển dụng, bật Gemma và bấm Phân tích. Cột kỹ năng người dùng nhập riêng luôn được ưu tiên; khi không có cột riêng, pipeline dùng kỹ năng có literal evidence thuộc danh mục nhận diện và lưu đầu ra Gemma nguyên bản để đối chiếu.

# Kiểm tra lại nguồn ngày 29/10/2026

Hai ZIP được tải mới từ Kaggle bằng revision cố định. Không sử dụng file dữ liệu của ứng dụng cũ.

| Dataset | Revision | Số dòng CSV | SHA-256 ZIP |
| --- | --- | ---: | --- |
| lucaznguyenofficial/vietnamese-job-posting-vietnamese-version | 2 | 2.056 | ffaf1a9a06848036e25ed9d87836e6f5a4918237aa34d312298fdf9e24b59307 |
| baocgb/vietnam-it-jobs-raw-data-from-topcv-2026 | 1 | 1.550 | 29651eb3e85d4d5b0fb8e45f968e01585c51de95f038cb850dc72607352f0426 |

Metadata nguồn thứ nhất ghi CC0, nguồn thứ hai ghi CC BY 4.0 và tác giả baocgb. Khi phân phối phải giữ xuất xứ, giấy phép và ghi rõ phần chuẩn hóa do dự án thực hiện. Đây là khai báo của bên phát hành dataset, không phải tuyên bố quyền sở hữu đối với nền tảng tuyển dụng.

Nguồn 2023 có trường announcement_date, khác expiration_date. Ngày quan sát thực tế gồm 16–22/02/2023. Nguồn mang tên 2026 còn có tin đăng tháng 12/2025; không gán toàn bộ bản ghi vào năm 2026 theo tên dataset. Hai nguồn khác nền tảng và phạm vi, chưa đủ để kết luận xu hướng nhiều năm.

Trong dữ liệu gốc, chức danh có cả công việc ngoài bảy nhóm nghề: lập trình CNC, developer hàng dệt, marketing full-stack, sales phát triển khách hàng. Từ khóa developer hoặc lập trình đơn lẻ không đủ để đưa vào phân tích nghề phần mềm. Chức danh mơ hồ phải được giữ để review.

Chuỗi kinh nghiệm “Nhân viên” ở nguồn 2023 xuất hiện 220 dòng, không phải số năm; 111 dòng thiếu. Nguồn 2026 có 186 dòng thiếu kinh nghiệm. Không thay các trường hợp này bằng 0.

Lương nguồn 2023 thường có VND nhưng thiếu kỳ; nguồn 2026 thường chỉ ghi “triệu”. Chưa có căn cứ đồng nhất toàn bộ thành VND/tháng. Gate xác minh nhãn lương vẫn mở; chưa có huấn luyện, metric hoặc dự đoán mới.

Đối chiếu từ API metadata chính chủ và CSV trong ZIP:

- https://www.kaggle.com/api/v1/datasets/view/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version
- https://www.kaggle.com/api/v1/datasets/view/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026

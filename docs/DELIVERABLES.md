# Đối chiếu đề bài và sản phẩm bàn giao

| Yêu cầu | Đầu ra cần hoàn thành | Trạng thái hiện tại |
|---|---|---|
| Xử lý dữ liệu | CSV/JSON/XLSX sạch + data card, quy tắc lương/kỹ năng | Đã có v1, salary v2.1.0 và thử nghiệm strict v3/v3.1; corpus Gemma corrected v2.2.0; còn silver labels/nguồn yếu, xem data card và các runbook |
| Matplotlib & Seaborn | Top nhu cầu kỹ năng; top lương kỹ năng; kinh nghiệm–lương; vai trò/khu vực | Đã có biểu đồ train trong outputs/eda/ |
| Ít nhất 2 mô hình | Ridge và Random Forest, cùng tập chia | Đã train/so sánh cùng salary v2.1.0; Ridge đang dùng, RF đối chiếu và model cũ giữ rollback |
| Ít nhất 2 metric | MAE, RMSE; thêm R² | Cùng 30 test mới: Ridge MAE 4,433M, RMSE 5,664M, R² 0,540; xem REPORT salary v2 |
| Giá trị kỹ năng | Thống kê theo vai trò, số mẫu và mức lương | Đã có thống kê và hệ số Ridge trên train; không suy nhân quả |
| Gemma | google/gemma-4-E4B-it + adapter + so sánh trước/sau | Adapter web 105728Z; reviewed candidate 501 bước không đạt regression guards; corrected run 051656Z đã hoàn tất nhưng không đạt; web giữ parent. Xem GEMMA_LABEL_QUALITY_AUDIT.md |
| Ứng dụng tư vấn | Hồ sơ → lương → đề xuất kỹ năng → giải thích | Đã có Vue/FastAPI, dự đoán RF/Ridge và gợi ý có hỗ trợ từ train; xem APP_RUNBOOK.md |
| Báo cáo cá nhân | `STT_Họ và tên_MSSV`, theo mẫu giảng viên | Đã có reports/BAO_CAO_NOI_DUNG.md làm nội dung kỹ thuật; chưa có mẫu hoặc thông tin sinh viên, chưa phải file báo cáo cá nhân hoàn tất |
| Link dự án | GitHub/GitLab truy cập được, README chạy lại | Remote theihoz/ML; nhánh publish/salary-gemma-prep |
| Dataset | File dữ liệu thật + nguồn, quyền sử dụng | Đã nhập nguồn; một số xuất xứ/điều khoản còn cần xác minh, xem docs/DATA_SOURCES.md |
| Demo | Kịch bản, model/adapter, môi trường chạy ổn định | App local đã kiểm chứng browser JSON mô tả dài → Gemma GPU → kỹ năng đối chiếu nguồn → Ridge/RF → biểu đồ → ZIP; có bảng mẫu48 dòng, còn chuẩn bị thuyết trình |

API thực tế: upload tại `POST /api/datasets`, job tại `POST /api/analyses`,
đọc trạng thái/kết quả/biểu đồ/download theo ID; `POST /api/salary/predict` và
`POST /api/career/advice`. Gemma đọc mô tả trong job với `use_gemma: true`.
Giải thích/tư vấn điền từ số liệu Python; không gọi Gemma để bịa số lương.

Đánh giá Gemma: JSON hợp lệ, accuracy từng trường và Skill F1 trên cùng test set;
tư vấn hiện lấy số liệu từ Python/model, không có kết quả chấm rubric ngôn ngữ để báo cáo.

Phân công theo context: dữ liệu; EDA; Gemma trên Mac; mô hình lương + API;
frontend + tích hợp. Cả năm người tự viết phần báo cáo cá nhân.

Trạng thái thực nghiệm và giới hạn: [TRAINING_RUNBOOK.md](TRAINING_RUNBOOK.md).

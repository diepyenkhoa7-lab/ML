# Đối chiếu đề bài và sản phẩm bàn giao

| Yêu cầu | Đầu ra cần hoàn thành | Trạng thái hiện tại |
|---|---|---|
| Xử lý dữ liệu | CSV/JSON/XLSX sạch + data card, quy tắc lương/kỹ năng | Đã làm sạch, rà soát nhãn và đóng băng bộ chia v1.0.1; còn giới hạn nhãn nguồn và số mẫu, xem docs/LABEL_REVIEW_AND_SPLITS.md |
| Matplotlib & Seaborn | Top nhu cầu kỹ năng; top lương kỹ năng; kinh nghiệm–lương; vai trò/khu vực | Đã có biểu đồ train trong outputs/eda/ |
| Ít nhất 2 mô hình | Ridge và Random Forest, cùng tập chia | Đã train Ridge/Random Forest trên bộ developer v1.0.1 |
| Ít nhất 2 metric | MAE, RMSE; thêm R² | Đã có MAE, RMSE, R² của baseline/Ridge/RF |
| Giá trị kỹ năng | Thống kê theo vai trò, số mẫu và mức lương | Đã có thống kê và hệ số Ridge trên train; không suy nhân quả |
| Gemma | google/gemma-4-E4B-it + adapter + so sánh trước/sau | Đủ trọng số và JSONL silver; chưa train, chờ xác nhận |
| Ứng dụng tư vấn | Hồ sơ → lương → đề xuất kỹ năng → giải thích | API khởi tạo có health, chưa có nghiệp vụ |
| Báo cáo cá nhân | `STT_Họ và tên_MSSV`, theo mẫu giảng viên | Chưa có mẫu hoặc thông tin sinh viên |
| Link dự án | GitHub/GitLab truy cập được, README chạy lại | Remote theihoz/ML; nhánh publish/salary-gemma-prep |
| Dataset | File dữ liệu thật + nguồn, quyền sử dụng | Đã nhập nguồn; một số xuất xứ/điều khoản còn cần xác minh, xem docs/DATA_SOURCES.md |
| Demo | Kịch bản, model/adapter, môi trường chạy ổn định | Có mô hình lương; còn API/giao diện, adapter và kịch bản |

API dự kiến: `GET /analytics/overview`, `POST /jobs/extract`,
`POST /salary/predict`, `POST /career/advice`. Chưa tạo endpoint trả kết quả giả.
Gemma nhận kết quả hồi quy và thống kê làm bằng chứng khi tư vấn.

Đánh giá Gemma: JSON hợp lệ, accuracy từng trường và Skill F1 trên cùng test set;
chấm tư vấn bằng rubric cố định và tỷ lệ phát biểu đúng số liệu.

Phân công theo context: dữ liệu; EDA; Gemma trên Mac; mô hình lương + API;
frontend + tích hợp. Cả năm người tự viết phần báo cáo cá nhân.

Trạng thái thực nghiệm và giới hạn: [TRAINING_RUNBOOK.md](TRAINING_RUNBOOK.md).

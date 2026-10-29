# M03 — Hai mô hình tự huấn luyện và chọn ứng viên

## Problem Statement

Ứng dụng cần model thực học từ dữ liệu mới, thay cho công thức cố định, artifact cũ hoặc kết quả so sánh điền sẵn.

## Solution

Lệnh train ngoại tuyến kiểm readiness, fit hai pipeline trên cùng split, lưu run và chọn champion theo policy validation được duyệt.

## User Stories

1. Là người huấn luyện, tôi muốn chạy lại bằng snapshot/config/seed, để tái lập thí nghiệm.
2. Là người đánh giá, tôi muốn hai model dùng cùng nhãn và split, để so sánh công bằng.
3. Là người demo, tôi muốn run lỗi không phá model đang dùng, để demo ổn định.

## Implementation Decisions

- Đã chốt Ridge + Linear Regression (OLS), khởi tạo mới và fit độc lập bằng cùng train/features của dự án. Ridge có regularization với alpha > 0; không đổi tên hoặc dùng lại cùng model để đếm hai mô hình. Baseline trung vị train dùng để tham chiếu, không được tính thay một trong hai model bắt buộc.
- Phạm vi tìm tham số, seed, budget tài nguyên và lựa chọn biến đổi target được ghi trong cấu hình sau #4; không chọn cấu hình bằng test. Nếu biến đổi target, metric và prediction xuất phải quay về đơn vị gốc.
- MAE là metric chính; chọn bằng validation MAE trên giá trị chưa làm tròn, bằng nhau chọn Linear Regression. Báo MAE/RMSE và giữ test riêng để đánh giá cuối. Model được chọn chỉ promote cho demo/tư vấn khi MAE nhỏ hơn baseline trung vị train trên cả validation và test của cùng cohort/split. Test không đạt thì giữ báo cáo/run nhưng không đổi model hoặc tham số bằng test. Không tự refit train+validation hoặc đổi định nghĩa train sau khi đã dùng phần này để đánh giá/tư vấn.
- Run lưu snapshot/split/policy/catalog/schema/config/library versions, hai model, preprocessing, prediction từng phần và kết quả chọn. Run chưa hoàn tất không được active; lỗi/ngắt giữ artifact tốt trước đó nguyên vẹn.
- Chưa có nhãn thật được chấp nhận thì chỉ chạy kiểm tra hợp đồng/cấu hình/trạng thái blocked, không gọi fit hoặc sinh metric/model giả.

## Testing Decisions

Sau gate, dùng tập con nhãn thật có xuất xứ để kiểm train/save/reload qua service và CLI. Đối chiếu split/model config và prediction, không mock model do dự án sở hữu. Kiểm n=0, split không đủ nhóm, ngắt run, config sai và dữ liệu/schema khác hash; không train trên fixture tổng hợp. Test logic lựa chọn/phát hành phải bắt được tie chọn Linear Regression, baseline chỉ từ train và trường hợp test không đạt giữ nguyên model đã chọn nhưng không promote.

## Out of Scope

Fine-tune/pretrained, neural network hoặc dịch vụ ngoài thay cho hai model đã chốt, hứa trước một mức sai số.

## Further Notes

F04, T17/T18; M01/M02 và #4 phải sẵn sàng trước fit thật. Việc phát triển code không đồng nghĩa hai model đã được huấn luyện hoặc đủ chất lượng phát hành.

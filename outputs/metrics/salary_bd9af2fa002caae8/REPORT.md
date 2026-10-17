# Kết quả thực nghiệm lương — bd9af2fa002caae8

Bộ vn_developer v1.0.1; nhãn trung điểm lương VND/tháng, chưa rõ gross/net.
Train 123 / validation 25 / test 28.
Chọn bằng MAE validation: random_forest. Fit preprocessing/model chỉ trên train.

| Model | Test MAE (triệu) | Test RMSE (triệu) | Test R² |
|---|---:|---:|---:|
| baseline_median | 8.921 | 14.339 | -0.033 |
| ridge | 7.074 | 9.603 | 0.537 |
| random_forest | 6.656 | 10.517 | 0.444 |

Không đổi lựa chọn model bằng test; baseline được báo cáo đầy đủ.
Giới hạn: 28 mẫu test; snapshot hỗn hợp 2025–2026, nhãn nguồn chưa phải gold,
chưa kiểm thử thời gian hoặc xác minh khả năng tổng quát toàn thị trường.
Liên hệ kỹ năng không phải tác động nhân quả.

Model: models/salary/bd9af2fa002caae8/best_model.joblib
Bằng chứng: protocol.json, selection.json, validation_metrics.csv, test_metrics.csv,
test_predictions.csv, test_errors.csv và các biểu đồ trong cùng thư mục.

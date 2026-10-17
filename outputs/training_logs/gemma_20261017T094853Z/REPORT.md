# Gemma trial — gemma_20261017T094853Z

Completed 100 iterations; rank 8 / 4 layers / batch 1 / context 1024.
Train loss: 0.501 → 0.081.
Validation loss: 1.135 → 0.07 on 5 validation batches per event (before the displayed optimizer update).

Losses are rounded console observations, not extraction accuracy. Test was not used.
Labels are silver job-card fields, not independently reviewed gold.
Adapter: `adapters/gemma-jobs/20261017T094853Z/adapters.safetensors`.
Full config, console, loss CSV, curve and checksums are stored with this run.

## Đánh giá validation sau trial

72 mẫu từ 25 tin nguồn, nhãn silver, chưa dùng test. Adapter: JSON thuần hợp lệ
100%, đúng schema 90,3%, trung bình accuracy 8 trường 91,1%, Skill micro F1 0,884.
Model gốc bọc cả 72 câu trả lời trong Markdown; sau khi chỉ bỏ lớp này, trung bình
accuracy trường 79,0%, Skill F1 0,835. Không diễn giải điểm strict JSON 0 của model
gốc thành không hiểu nội dung. Chẩn đoán bỏ fence dùng cùng quy tắc cho cả hai.

Adapter còn 7 lỗi schema (6 kỹ năng trùng, 1 sai bộ khóa), lưu nguyên kết quả và
schema_errors.json; không sửa output hoặc train tiếp để làm đẹp điểm. Mẫu bỏ trường
là biến thể, không phải tin độc lập. Kết quả chỉ đo khớp nhãn silver của phiếu tin.

Bảng so sánh và metric từng trường: `outputs/metrics/gemma_20261017T094853Z_comparison/REPORT.md`.
Dự đoán thô và checksums: `outputs/metrics/gemma_20261017T094853Z_{base,adapter}_valid/`.

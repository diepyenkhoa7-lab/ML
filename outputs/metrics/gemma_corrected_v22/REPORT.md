# Corrected Gemma v2.2.0 — huấn luyện và đánh giá đã hoàn tất

## Quyết định

**Không promote.** Run `20261018T051656Z` hoàn tất 501/501 bước, exit code 0, LR 2e-6 từ serving parent `20261017T105728Z`, optimizer reset. Validation loss 0,343→0,183, train loss cuối 0,011. Loss không phải accuracy. Trọng số candidate SHA256 `06719c09647a1208f7e85127ccd54d3ad214339f23bdb636bc984b6fb07eb378` được giữ riêng.

| Tập và metric | Parent | Candidate |
|---|---:|---:|
| Validation mới (31 tin) Skill F1 | 80,58% | 82,35% |
| Validation mới (31 tin) mean field exact | 85,48% | 86,69% |
| Validation mới (31 tin) experience exact | 70,97% | 70,97% |
| Validation mới (31 tin) schema | 100% | 96,77% |
| Validation mới (31 tin) score | 0,869167 | 0,874075 |
| Validation cũ (72 mẫu) Skill F1 | 93,76% | 91,94% |
| Validation cũ (72 mẫu) schema | 95,83% | 91,67% |
| Validation cũ (72 mẫu) score | 0,941685 | 0,920945 |

JSON validity đều 100%. New score tăng 0,004908, chưa đạt mức 0,005. Legacy score/skills/schema guards đều fail. Giữ ngưỡng đã khóa, giữ adapter web parent và Ridge v2. Không chấm test mới 33 tin hoặc mở lại old test; không chọn checkpoint trung gian theo kết quả sau cùng. Hai candidate trên 31 validation đã dùng hết ngân sách; một thí nghiệm mới cần validation nguồn mới.

## Reference và giới hạn

Corpus corrected501/31/33 sửa 7 train, 10 validation và 1 test; inputs và company split giữ nguyên. Test chỉ rebuild nhãn bằng policy cố định trước train, không dùng predictions test hoặc thêm alias từ test. Vẫn là rule-based/AI-reviewed silver, không phải human gold. Baseline trên corrected reference được tính lại từ cached raw predictions có cùng prompt/group/order đã xác minh. Không so80,58% với72,73% reference cũ để tuyên bố model tự cải thiện.

F1 trên cùng corrected validation tăng nhưng chất lượng chưa đủ ổn định. Hai yếu tố LR và labels cùng thay đổi nên không quy kết tác động riêng của LR. Không có kết quả MAE dự đoán lương mới; hệ thống vẫn dùng kết quả Ridge v2 đã công bố.

## Kiểm chứng phục vụ

- `worker_duplicate_gpu_smoke.json`: GPU thật trên parent,3 mô tả giống nhau → 1 lần sinh, đủ 3 kết quả, 8,27 giây tổng lượt. Không phải benchmark tốc độ so sánh độc lập.
- `serving_qa/context_2048_without_retry.json`: fullsource dài 1.211 token tính cả dự phòngoutput được đọc nhưng sai schema vì lặp kỹ năng.
- `serving_qa/context_2048_with_retry.json`: thêm tối đa 1 lần model trả lại JSON, lưu đủ raw attempts; schema hồi phục. Không sửa raw JSON hoặc sửa metric benchmark.
- Raw model vẫn có thể suy đoán kỹ năng hoặc liệt kê chức năng chung. App chỉ dùng kỹ năng trong danh mục có literal evidence ở mô tả khi cột skills người dùng thiếu; giữ nguyên extraction, source_skill_evidence và cảnh báo. Cột skills người dùng nhập riêng được ưu tiên. Đây là thay đổi pipeline ứng dụng, chưa chứng minh giảm MAE thị trường.
- Context web hiện 2.048 token, giữ toàn bộ input; training/evaluation raw trước đây vẫn 1.024 token và không dùng schema retry. Không coi metric raw lịch sử là metric của pipeline ứng dụng mới.

Các file run/summary/config/loss curve nằm ở `outputs/training_logs/gemma_20261018T051656Z/`; raw prediction và từng gate ở thư mục này. Nghiệm thu source/frontend và app end-to-end được ghi riêng trong `serving_qa/`, không suy ra từ unit tests.

# Gemma reviewed v2 — kết quả fine-tune và nghiệm thu

## Quyết định

**Không thay adapter web**: candidate `20261018T002705Z` không đạt ba regression guard trên validation cũ. Web giữ `20261017T105728Z`; mô hình lương Ridge v2 không thay đổi. Không chấm test mới 33 tin, không chấm lại test Gemma cũ, không train lượt trùng bằng cùng protocol.

## Dữ liệu và lượt train thực

Đã rà soát 214 dòng: 201 chấp nhận và 13 loại. Đây là **AI-reviewed silver, chưa phải human gold**. Queue gốc được giữ nguyên; quyết định và bằng chứng ở `data/annotation/gemma_v2.0.0/`. Corpus mới gồm 501 train (137 tin mới + 364 legacy replay), 31 validation và 33 test mới chia theo công ty. 105/201 tin được chấp nhận giữ kinh nghiệm null vì thiếu một giá trị rõ trong văn bản hiển thị.

Run `20261018T002705Z` đã train thật, hoàn tất 501/501 bước, exit 0; LR 1e-5, LoRA rank 8, 4 layers, context 1024. Tiếp tục trọng số adapter cha, khởi tạo lại optimizer. Train loss cuối 0,006; validation loss 0,392 → 0,110 trên toàn bộ 31 validation. Loss không phải accuracy. Log/config/summary/đồ thị ở `outputs/training_logs/gemma_20261018T002705Z/`.

## So sánh cùng từng tập

| Tập | Adapter | Skill micro F1 | Mean field exact | Schema đúng | Score |
|---|---|---:|---:|---:|---:|
| Validation mới — 31 tin | Adapter đang dùng | 72.73% | 85.08% | 100.00% | 0.843585 |
| Validation mới — 31 tin | Candidate vừa train | 78.49% | 85.89% | 93.55% | 0.852016 |
| Validation cũ — 72 mẫu / 25 tin | Adapter đang dùng | 93.76% | 93.75% | 95.83% | 0.941685 |
| Validation cũ — 72 mẫu / 25 tin | Candidate vừa train | 90.22% | 93.06% | 93.06% | 0.922048 |

JSON validity đều 100%. Score mới tăng 0,008431, đạt mức tăng tối thiểu 0,005; schema mới 93,55% vượt sàn 90%. Tuy nhiên trên validation cũ, score giảm 0,019638 (chỉ cho phép 0,01), Skill F1 giảm 0,035366 (chỉ cho phép 0,015), schema giảm 0,027778 (chỉ cho phép 0,01). Không đổi ngưỡng sau khi xem kết quả.

Trên validation mới, exact experience giảm 67,74% → 58,06%, dù skills exact tăng 29,03% → 38,71% và hai cận lương tăng 96,77% → 100%. Hai lỗi schema đều do kỹ năng trùng, có 13/31 trường kinh nghiệm không khớp. Xem `new_validation_diagnostics.json` để đối chiếu từng ca. Không sửa raw output hoặc nhãn đã đóng băng để cải thiện điểm.

## Giới hạn và hướng tiếp theo

Kết quả cho thấy candidate học được một phần cách đọc kỹ năng từ trích đoạn mới nhưng chưa giữ chất lượng trên định dạng cũ; mức độ đóng góp riêng của từng nguyên nhân chưa được chứng minh. Không gọi việc loss giảm là thành công nghiệm thu. Các metric dùng nhãn silver, không đo MAE dự đoán thu nhập hoặc độ khớp báo cáo thị trường.

Vòng cải tiến sau cần người rà soát độc lập nhãn từ văn bản gốc, ưu tiên kinh nghiệm mơ hồ, alias và kỹ năng lặp; chuẩn bị protocol mới với cân bằng replay/nhãn thiếu và validation mới trước khi thử thêm candidate. Đây là hướng tiếp theo, chưa được thực hiện trong run này. Giữ test mới chưa chấm để tránh tối ưu theo test.

## Bằng chứng và tái lập

- `selection.json`: checksum adapter/corpus/protocol, paired metrics và từng gate.
- `baseline_new_valid/`, `candidate_new_valid/`, `candidate_legacy_valid/`: dự đoán JSON thô, metrics và checksum.
- `baseline_legacy_validation_verified.json`: xác minh dự đoán validation cha đã lưu.
- `configs/gemma_reviewed_protocol.json`, `configs/gemma_reviewed.yaml`: protocol đã khóa trước train.
- Bản source copy tách biệt vượt qua 79 tests, Ruff, kiểm tra frozen/strict SFT, npm ci offline, Prettier và frontend build; bằng chứng `source_export.json`. Báo cáo và cập nhật tài liệu nghiệm thu được bổ sung sau lần kiểm thử, không thay code/model/nhãn.
- 79 unit tests đạt, Ruff check/format 59 file đạt; strict corpus 501/31/33 đạt. Kiểm tra corpus đọc nhãn/checksum, không chạy suy luận trên test.

Lệnh chấm lại từ raw predictions, không train hay gọi GPU:

```bash
.venv/bin/python scripts/compare_reviewed_gemma.py \
  --candidate adapters/gemma-jobs/20261018T002705Z
```

`make app` chỉ suy luận. `make gemma-reviewed-train` là lệnh train thật; protocol hiện tại đã dùng hết một candidate nên từ chối train lại. Muốn chạy vòng khác cần protocol/corpus được chuẩn bị riêng, không sửa khóa của vòng này.

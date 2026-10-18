# Gemma corrected v2.2.0 — lượt thứ hai trên validation hiện hành

Corpus `data/finetune_reviewed/v2.2.0` sửa nhãn theo policy có dẫn chứng từ audit v2.1.1. Train 501 (364 replay +137 tin mới), valid31/test33 giữ nguyên input và company split. Có 7 train,10 validation và1 test thay đổi nhãn. Test được rebuild tự động theo policy đã cố định từ train/valid; không xem predictions test để thêm alias hoặc chọn tham số. Vẫn là silver, không phải người độc lập duyệt gold.

`prepare_gemma_corrected.py` kiểm tra checksum, giữ byte replay, đếm lại token và chỉ ghi phiên bản mới. `rescore_gemma_references.py` cho phép dùng cached generation trên validation khi mọi prompt, source, group và thứ tự giống hệt; không giả làm lượt suy luận mới. Baseline Skill F1 trên reference corrected là 0,805825; đây là thay đổi cách chấm so với v2, không phải model mới tốt lên.

Protocol `configs/gemma_corrected_protocol.json` khóa một candidate 501 bước, LR 2e-6, parent adapter105728Z, optimizer reset, seed20261018, context1024. Hypothesis: sửa nhãn và giảm LR năm lần có thể học thêm source text mà ít làm quên dạng phiếu cũ. Cả hai yếu tố cùng đổi nên không suy riêng đóng góp nhân quả của LR.

Giữ nguyên score/skill/schema guards cũ; thêm exact experience trên valid mới không được giảm. Trên cùng31valid, đây là lần thử thứ hai và cuối cùng tính cùng reviewed v2; code kiểm tra ngân sách gộp. Vòng tiếp theo cần validation từ nguồn mới, không lách bằng tên protocol khác. Chỉ khi validation đạt mới chấm paired test33 một lần; test Gemma cũ không mở lại. Adapter web không đổi tự động.

```bash
# Kiểm tra, không train
make gemma-corrected-plan

# Train thật, bị từ chối nếu đã hết ngân sách
make gemma-corrected-train

# Chỉ chạy web/suy luận
make app
```

Run thực `20261018T051656Z` đã hoàn tất501/501; `outputs/training_logs/gemma_20261018T051656Z/` có xác nhận, config và console. Đã chấm raw JSON và không đạt nghiệm thu, xem `outputs/metrics/gemma_corrected_v22/REPORT.md`. Các lệnh dưới đây ghi lại cách đánh giá đã thực hiện; output hiện có được giữ bất biến, không chạy lại vào các thư mục này:

```bash
.venv/bin/python scripts/evaluate_gemma.py --data data/finetune_reviewed/v2.2.0 \
  --split valid --adapter adapters/gemma-jobs/20261018T051656Z --generate \
  --output outputs/metrics/gemma_corrected_v22/candidate_new_valid
.venv/bin/python scripts/evaluate_gemma.py --data data/finetune --split valid \
  --adapter adapters/gemma-jobs/20261018T051656Z --generate \
  --output outputs/metrics/gemma_corrected_v22/candidate_legacy_valid
.venv/bin/python scripts/compare_reviewed_gemma.py \
  --data data/finetune_reviewed/v2.2.0 --protocol configs/gemma_corrected_protocol.json \
  --output outputs/metrics/gemma_corrected_v22 \
  --candidate adapters/gemma-jobs/20261018T051656Z
```

Không chạy các lệnh GPU này đồng thời với train. Nếu validation fail, giữ parent và không chấm test. Trạng thái cuối phải đọc run.json/summary/selection thực, chưa có chúng thì vẫn đang làm.

Worker app đã kiểm chứng GPU thật việc tái sử dụng mô tả trùng hoàn toàn trong một request: giữ đủ index/hash/raw output/lỗi cho từng dòng, không cache dữ liệu giữa người dùng/lượt chạy. GPU test3 mô tả trùng dùng 1 lần sinh đã đạt. Web sau đó hỗ trợ context2048, tốiđa1schema retry giữrawattempts và source-grounded skill features; xem APP_RUNBOOK.md. Context dài hơn không bảo đảm nội dung trích xuất đúng.

Mốc source preparation đã qua 89 tests, Ruff check/format66 file, source-copy frozen/strict checks và frontend install/build offline. Bằng chứng `outputs/metrics/gemma_corrected_v22/source_export_preparation.json`. Đây là kiểm chứng phần mềm/dữ liệu chuẩn bị, không phải kết quả model đang train. Source snapshot chỉ chứa launch record và code/corpus ổn định; console/checkpoint đang ghi vẫn giữ local đến khi nghiệm thu.

Kết quả cuối: validation_passed=false. New score chỉ tăng 0,004908; cả ba legacy guards không đạt. Không chấm test33, không đổi adapter web. Xem REPORT.md và [cải tiến phục vụ](SERVING_IMPROVEMENTS.md) để phân biệt chất lượng model với thay đổi pipeline ứng dụng.

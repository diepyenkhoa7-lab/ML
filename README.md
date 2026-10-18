# IT Career Insight

Đề tài 4: phân tích thị trường việc làm CNTT và dự đoán lương lập trình viên bằng Python.
Model trích xuất đã chốt: [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it).
Ứng dụng Vue 3 + FastAPI đã nối nhập bảng → dự đoán → biểu đồ → xuất kết quả,
cùng trang tư vấn nghề nghiệp và Gemma đọc mô tả khi bật.

Vòng nhãn rõ kỳ tháng **v3/v3.1 đã train 24 cấu hình**, chưa đạt điều kiện triển khai:
v3.1 không còn giả định kỳ tháng nhưng kiểm tra độc lập chỉ có 3 mẫu và độ lệch nhóm
ITviec còn kém v2. Web giữ Ridge v2. Xem [kết quả và nhãn cần duyệt](docs/SALARY_V3_REVIEW.md).

## Mở ứng dụng

```bash
make frontend-setup  # Lần đầu: cài dependency Vue/Vite theo lockfile.
make app
```

Mở **http://127.0.0.1:8000**. Chọn CSV/XLSX/JSON hoặc thử 48 tin có sẵn,
kiểm tra ghép cột rồi bấm Phân tích. Tải CSV, Excel, PNG hoặc toàn bộ ZIP.
Lệnh này chỉ chạy ứng dụng/suy luận; không train. Dữ liệu nhập nằm tại
`outputs/app_runtime/`, giữ ngoài Git. [Hướng dẫn chi tiết](docs/APP_RUNBOOK.md),
[kế hoạch & tiêu chí](docs/APP_IMPLEMENTATION_PLAN.md).

## Lệnh train và lệnh suy luận

Bộ 214 dòng đã có bản rà soát AI riêng: 201 chấp nhận, 13 loại; chưa phải human gold.
Fine-tune reviewed đã hoàn tất 501 bước; F1 validation mới tăng 72,73% → 78,49% nhưng
không đạt guard validation cũ, nên giữ adapter web cũ và chưa chấm test mới.
Kết quả: [báo cáo reviewed v2](outputs/metrics/gemma_reviewed_v2/REPORT.md).
[Audit nhãn tiếp theo](docs/GEMMA_LABEL_QUALITY_AUDIT.md) xác nhận reference còn thiếu;
đã lưu 17 quyết định sửa có dẫn chứng, chưa train vòng kế tiếp.
Corpus mới gồm 137 tin train mới + 364 replay, 31 validation và 33 test mới theo công ty.
Lượt dữ liệu này dùng `make gemma-reviewed-plan` (không train) và
`make gemma-reviewed-train` (**train thật 501 bước**, một candidate theo protocol).
Xem [nhãn, lineage và cách đánh giá](docs/GEMMA_REVIEWED_FINETUNE.md).

| Lệnh | Tác dụng |
|---|---|
| `make gemma-adapter` | **Train thật** toàn bộ 364 mẫu train, mặc định 1 epoch = 364 bước |
| `EPOCHS=3 make gemma-adapter` | Train thật 3 epochs = 1.092 bước |
| `make gemma-infer-adapter` | **Chỉ suy luận**, không cập nhật trọng số |
| `make gemma-plan-full` | Kiểm tra dữ liệu và in lịch train, không huấn luyện |
| `make gemma-train` / `make gemma-smoke` | In kế hoạch trial cũ, không tự train |

Dữ liệu ở `data/finetune_full/v1.0.0/`: 364 train / 72 validation / 82 test.
Validation/test giữ riêng. Mỗi lần train tạo run và adapter mới.
**`make gemma-infer-adapter` mặc định nạp bản tốt nhất theo validation:
`20261017T105728Z`.** Có thể chỉ định `GEMMA_ADAPTER` để dùng bản khác.

Lượt bạn tự chạy `20261017T101925Z` đã hoàn tất **364/364 bước**, exit code 0.
Train loss cuối **0,032**, validation loss **0,068** trên đủ 72 mẫu. Xem log bằng lệnh chỉ đọc:

```bash
tail -f outputs/training_logs/gemma_20261017T101925Z/console.log
```

Suy luận bằng adapter được chọn sau các lượt cải tiến (không train):

```bash
make gemma-infer-adapter
# Bản full ban đầu vẫn được giữ để so sánh/quay lại:
GEMMA_ADAPTER=adapters/gemma-jobs/20261017T101925Z make gemma-infer-adapter
```

Xem [hướng dẫn train, giám sát và suy luận](docs/GEMMA_FULL_TRAINING.md).
Protocol và lệnh đánh giá: [Gemma tuning](docs/GEMMA_TUNING.md).
Kết quả: [bảng chọn bằng validation](outputs/metrics/gemma_tuning/REPORT.md),
[đánh giá cuối](outputs/metrics/gemma_tuning/FINAL_REPORT.md).

## Trạng thái hiện tại

- Đã nhập/làm sạch bốn nguồn, rà soát nhãn và đóng băng split v1.0.1.
- Đã chạy EDA Matplotlib/Seaborn và train median baseline, Ridge, Random Forest.
- Bộ developer Việt Nam: **train 123 / validation 25 / test 28**. Fit trên train;
  chọn Random Forest bằng MAE validation, giữ test cho đánh giá cuối theo protocol.
- Test MAE RF **6,656 triệu VND/tháng**, RMSE **10,517 triệu**, R² **0,444**.
  Ridge: MAE 7,074 triệu, RMSE 9,603 triệu; baseline MAE 8,921 triệu.
  Báo cáo cả ba, không chọn lại bằng test. Chỉ 28 mẫu test, nhãn nguồn chưa phải gold,
  chưa chứng minh tổng quát toàn thị trường.
- Gemma: đủ trọng số Google và MLX 4-bit, checksum đã xác minh. JSONL silver có
  **364 / 72 / 82** mẫu, tương ứng 122 / 25 / 28 tin nguồn; gồm biến thể bỏ trường.
  Sau full baseline đã train thật thêm 3 lượt × 364 bước với lr giảm dần.
  Chọn `20261017T105728Z` bằng validation; lượt cuối giảm điểm nên bị loại.
  Validation: Skill F1 **93,76%** (baseline full 90,22%), accuracy trung bình 8 trường
  **93,75%**, schema **95,83%**, JSON **100%**. Skills exact chỉ **56,94%**;
  nhãn silver, còn alias/duplicate và mục tiêu schema 98%/accuracy 95% chưa đạt.
  Test (82 mẫu / 28 tin): Skill F1 **91,85%**, accuracy trung bình **93,90%**,
  schema **95,12%**, JSON **100%**; skills exact **54,88%**.
  Test chỉ chấm sau khi khóa lựa chọn, không train tiếp bằng lỗi test;
  xem [báo cáo cuối và từng trường](outputs/metrics/gemma_tuning/FINAL_REPORT.md).
  [Trial 100 bước cũ](outputs/metrics/gemma_20261017T094853Z_comparison/REPORT.md)
  vẫn được giữ riêng.
- Đã chuẩn bị notebook 03, kế hoạch, wrapper lưu log và script đánh giá Gemma;
  mặc định suy luận dùng adapter đã chọn bằng validation;
  ứng dụng tư vấn dùng dự đoán RF/Ridge và hỗ trợ kỹ năng từ train.
  Giải thích bằng Python có bằng chứng; Gemma dùng cho trích xuất, không sinh số lương.

Xem [hướng dẫn train và bằng chứng](docs/TRAINING_RUNBOOK.md),
[kết quả lương](outputs/metrics/salary_bd9af2fa002caae8/REPORT.md),
[hồ sơ nguồn](docs/DATA_SOURCES.md), [quy tắc làm sạch](docs/DATA_CLEANING.md),
[bộ chia](docs/LABEL_REVIEW_AND_SPLITS.md), [data card](data/DATA_CARD.md).

## Mở môi trường

```bash
cd /Users/scara2906/Downloads/ML
source .venv/bin/activate
make lab
```

Chọn kernel **Python (IT Career Insight)**. Nếu đang mở bản notebook cũ, nạp lại từ ổ đĩa.

- `notebooks/01_eda.ipynb`: đầy đủ cell và output, EDA trên train CNTT VN.
- `notebooks/02_salary_models.ipynb`: đầy đủ cell huấn luyện, metric, lưu/nạp model.
  [Bản thực thi đầy đủ, lưu riêng](outputs/training_logs/salary_20261017T094526Z/02_salary_models.executed.ipynb)
  giữ output khi phiên Jupyter đang mở lưu đè bản cũ.
- `notebooks/03_gemma_extraction.ipynb`: đủ bước chuẩn bị/xác nhận/train/đánh giá;
  các cell kiểm tra đã được chạy riêng; Run All với mặc định không train hoặc suy luận Gemma.
  Lệnh full và suy luận hiện hành xem bảng phía trên.

```bash
make salary-train  # Chạy notebook 01 + 02, lưu transcript; không chạy Gemma.
make validate-sft
make gemma-train   # CHỈ xuất kế hoạch, không train.
make api          # http://127.0.0.1:8000/docs và /health
```

Pipeline lương ở `models/salary/bd9af2fa002caae8/`; metrics/biểu đồ và dự đoán test ở
`outputs/metrics/salary_bd9af2fa002caae8/`; transcript ở `outputs/training_logs/`.
Cùng protocol sẽ kiểm tra/đọc kết quả test đã chốt, không dùng test để tìm tham số.
Hệ số kỹ năng Ridge là liên hệ có điều kiện, không phải tác động nhân quả.

## Cài lại

```bash
bash scripts/setup.sh
make test-data
make lint
.venv/bin/python scripts/verify_salary_splits.py --training-only
```

Python 3.11.17, macOS arm64; MLX 0.32.4, MLX-LM 0.32.2. Script ưu tiên uv nếu có,
không có thì pip. File lock macOS giữ phiên bản; Windows/Linux dùng
`requirements-dev.txt` cho EDA/hồi quy/API. MLX dùng Apple Silicon/Metal.
Kernel được cài trong `.venv/share/jupyter`, cache ở `.cache/` dự án.
`make check-mlx` cần quyền truy cập Metal; môi trường sandbox có thể không thấy GPU.
Các số đo giả lập cũ trong `outputs/environment/` chỉ kiểm tra kỹ thuật.

## Gemma: model, dữ liệu và xác nhận

Model gốc Google revision `ee0ef6023621cff504d758262d4e04895a5af4a2`, trọng số
15.992.595.884 byte; bản MLX text-only 4-bit 4.198.925.877 byte.
Trên máy hiện tại đã có đủ, không cần tải lại. SHA256 tại
`outputs/gemma_preparation/weights.json`; manifest ở hai thư mục model.
Đã chạy full baseline và 3 lượt cải tiến thật, lưu/nạp lại adapter để đánh giá.
Bản chuyển chỉ dùng văn bản.

Máy khác tải riêng, không đưa trọng số lên Git:

```bash
.venv/bin/python scripts/download_gemma.py --revision ee0ef6023621cff504d758262d4e04895a5af4a2 --convert
```

Nếu cần đăng nhập, nhập token bằng Hugging Face CLI, không lưu vào source.

JSONL gồm phiếu tin thật và nhãn **silver_source_fields**, chưa qua duyệt thủ công độc lập,
chưa phải dữ liệu tin tự do đầy đủ hoặc dữ liệu tư vấn. Kế thừa split/nhóm từ bộ lương;
không trùng nguồn/nhóm/prompt, không cắt token; dài nhất 614 token. Năm/tháng và tiền tệ
được giữ theo nguồn. Manifest/ledger ghi nguồn và các biến thể bị loại.

Full baseline: MLX 4-bit LoRA, 4 lớp cuối, rank 8, batch 1, 364 updates,
learning rate 1e-4, context 1024, mask prompt, gradient checkpoint. Các config tuning
dùng lr 5e-5 / 2e-5 / 1e-5 và ghi adapter cha/seed. Người dùng đã cho phép đợt train
lặp này; lệnh `make gemma-adapter` là yêu cầu chạy thật một lượt mới.
`make gemma-train` và `make gemma-smoke` chỉ giữ kế hoạch trial cũ.

Wrapper lưu console loss, cấu hình, exit code và checkpoint theo run_id; không ghi đè
lượt cũ. `scripts/evaluate_gemma.py` chấm JSON validity, schema validity, accuracy
8 trường và Skill F1. Chọn adapter trên validation, sau đó chấm test riêng cho bản
được chọn; không đổi model từ kết quả test. Log/loss curve theo từng run tại
`outputs/training_logs/`; kết quả và quyết định ở `outputs/metrics/gemma_tuning/`.

## Nhánh Git gọn và dữ liệu lớn

Nhánh bàn giao **`publish/salary-gemma-prep`** chứa source, notebook, CSV sạch VN,
CSV split, JSONL, pipeline lương nhỏ, metric và log. Manifest liệt kê file tại
`outputs/source_publication/manifest.json`. Lịch sử cũ và dữ liệu lớn local được giữ
nguyên; không force-push. Trọng số Gemma gốc, cache, raw/bảng audit lớn và checkpoint trung gian tải/lưu riêng.
Adapter cuối nhỏ (6,95 MB), config và checksum được đưa cùng source để tái sử dụng.

`configs/data_sources.json` ghi URL/revision/checksum. File `vietnam_it_job_posts.csv`
người dùng gửi chưa có URL nguồn, cần cung cấp thủ công để làm sạch lại từ raw.
`make data-verify` đầy đủ cần raw/bảng trung gian local; clone gọn dùng
`verify_salary_splits.py --training-only` để kiểm tra frozen CSV.

```bash
make data-fetch
make data-clean
make data-split
make data-verify
```

Không chạy lại làm sạch/chia đè snapshot đã dùng báo cáo; tạo phiên bản mới khi đổi nhãn.
Các nguồn có giới hạn xuất xứ/điều khoản ghi rõ tại DATA_SOURCES.md.

## Sản phẩm còn lại

Bổ sung nhãn gold và holdout mới khi mở vòng nghiên cứu khác; báo cáo cá nhân theo
mẫu giảng viên, đặt tên `STT_Họ và tên_MSSV`; chuẩn bị kịch bản thuyết trình.
Ứng dụng local đã có luồng demo nhập bảng, dự đoán, biểu đồ, tư vấn và tải kết quả.
Đối chiếu [bảng bàn giao](docs/DELIVERABLES.md).

Tham chiếu: [Google model card](https://huggingface.co/google/gemma-4-E4B-it),
[MLX-LM LoRA/QLoRA](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md).

Audit kiến trúc ngày 18/10: [báo cáo](outputs/architecture_audit/2026-10-18/REPORT.md).
Hành trình, khái niệm và khó khăn có bằng chứng: [PROJECT_JOURNEY](docs/PROJECT_JOURNEY.md).

## Cập nhật 18/10: salary v2 + Gemma trên web

Ứng dụng hiện chọn Ridge `v2_042e3aa1a886`, Random Forest đối chiếu, Gemma trích mô tả. Trên **cùng30 test mới**, MAE RFv1 8,246 → Ridgev2 4,433 triệu VND/tháng, RMSE10,508→5,664; không so trực tiếp với test cũ28tin. Train1157 gồm79 nhãn tháng +1078 nhãn yếu(weight0,3); valid25/test30 chỉ nhãn có bằng chứng tháng, company-disjoint.

Đối chiếu ITviec theo nhóm vẫn lệch khoảng21,1% và tệ hơn v1 ở phép sanity check này; đó là thu nhập khảo sát, khác lương chào tuyển. Web hiển thị số tham chiếu riêng, không ép dự đoán khớp báo cáo. [Kết quả và giới hạn](outputs/metrics/salary_v2_042e3aa1a886/REPORT.md), [lệnh chạy/train/rollback](docs/SALARY_V2_RUNBOOK.md).

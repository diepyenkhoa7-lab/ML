# IT Career Insight

Đề tài 4: phân tích thị trường việc làm CNTT và dự đoán lương lập trình viên bằng Python.
Model trích xuất đã chốt: [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it).
Frontend Vue 3 dự kiến ở bước tích hợp; FastAPI hiện có health, chưa có endpoint nghiệp vụ.

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
  **Chưa train Gemma. Mọi huấn luyện Gemma, kể cả smoke, cần bạn xác nhận trước.**
- Đã chuẩn bị notebook 03, kế hoạch, wrapper lưu log và script đánh giá Gemma;
  chưa có metric/adapter Gemma hoặc chức năng tư vấn hoàn chỉnh.

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
  chưa thực thi. Run All với mặc định không train hoặc suy luận Gemma.

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
Chưa benchmark hoặc xác minh LoRA trên model đầy đủ. Bản chuyển chỉ dùng văn bản.

Máy khác tải riêng, không đưa trọng số lên Git:

```bash
.venv/bin/python scripts/download_gemma.py --revision ee0ef6023621cff504d758262d4e04895a5af4a2 --convert
```

Nếu cần đăng nhập, nhập token bằng Hugging Face CLI, không lưu vào source.

JSONL gồm phiếu tin thật và nhãn **silver_source_fields**, chưa qua duyệt thủ công độc lập,
chưa phải dữ liệu tin tự do đầy đủ hoặc dữ liệu tư vấn. Kế thừa split/nhóm từ bộ lương;
không trùng nguồn/nhóm/prompt, không cắt token; dài nhất 614 token. Năm/tháng và tiền tệ
được giữ theo nguồn. Manifest/ledger ghi nguồn và các biến thể bị loại.

Trial đề xuất: MLX 4-bit LoRA, 4 lớp cuối, rank 8, batch 1, 100 iterations,
learning rate 1e-4, context 1024, mask prompt, gradient checkpoint. `make gemma-train`
và `make gemma-smoke` chỉ tạo kế hoạch. Sau khi bạn xác nhận mới dùng lệnh
`--confirm-training` ghi rõ trong [runbook](docs/TRAINING_RUNBOOK.md).

Wrapper lưu console loss, cấu hình, exit code và checkpoint theo run_id; không ghi đè
lượt cũ. `scripts/evaluate_gemma.py` chuẩn bị JSON validity, schema validity, accuracy
8 trường và Skill F1. Chọn checkpoint trên validation, sau đó so base/adapter trên test.
Chưa có metric Gemma cho đến khi thực hiện đánh giá.

## Nhánh Git gọn và dữ liệu lớn

Nhánh bàn giao **`publish/salary-gemma-prep`** chứa source, notebook, CSV sạch VN,
CSV split, JSONL, pipeline lương nhỏ, metric và log. Manifest liệt kê file tại
`outputs/source_publication/manifest.json`. Lịch sử cũ và dữ liệu lớn local được giữ
nguyên; không force-push. Trọng số Gemma, cache, raw/bảng audit lớn tải/lưu riêng.

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

Tích hợp API dự đoán/trích xuất/tư vấn và giao diện; đánh giá Gemma sau xác nhận;
báo cáo cá nhân theo mẫu giảng viên, đặt tên `STT_Họ và tên_MSSV`; demo ứng dụng.
Đối chiếu [bảng bàn giao](docs/DELIVERABLES.md).

Tham chiếu: [Google model card](https://huggingface.co/google/gemma-4-E4B-it),
[MLX-LM LoRA/QLoRA](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md).

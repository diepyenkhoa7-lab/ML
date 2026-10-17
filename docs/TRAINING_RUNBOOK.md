# Huấn luyện và kết quả — 17/10/2026

## 1. Dự đoán lương: đã chạy

Chạy `make salary-train` hoặc mở notebook 01 rồi 02, kernel **Python (IT Career Insight)**.
Hai notebook đã có đủ cell và đã thực thi trên dữ liệu thật. Notebook 03 dành riêng Gemma.
Runner lưu bản `*.executed.ipynb` trong thư mục log, bảo toàn output độc lập với phiên
Jupyter đang mở. Bản thực thi lương đầy đủ tại
`outputs/training_logs/salary_20261017T094526Z/02_salary_models.executed.ipynb`;
bản này sửa lưu model để không ghi đè file đã gắn với test; grid, seed, tập chia và
quy tắc chọn model giữ nguyên. Lượt kiểm tra salary_20261017T094556Z cùng protocol đã đọc test cache thành công,
không đọc lại nhãn test và không dự đoán test lại.

Bộ chính `vn_developer/v1.0.1`: train 123 / validation 25 / test 28,
nhãn trung điểm lương VND/tháng, chưa rõ gross/net. Toàn bộ preprocessing fit trên train;
chọn tham số/model theo MAE validation, không refit bằng test. Notebook lưu/nạp pipeline và
kiểm tra nạp bằng tiến trình Python mới. Test được chốt theo protocol hash; chạy lại cùng
protocol sẽ kiểm tra và đọc kết quả test đã lưu. Đổi cấu hình sau khi xem test sẽ làm mất
ý nghĩa holdout độc lập; không thử nhiều cấu hình rồi chọn theo test cũ.

Experiment `bd9af2fa002caae8`, chọn **Random Forest** (validation MAE 8,473 triệu VND).

| Mô hình | Test MAE (triệu VND) | Test RMSE (triệu VND) | Test R² |
|---|---:|---:|---:|
| Median baseline | 8,921 | 14,339 | -0,033 |
| Ridge | 7,074 | 9,603 | 0,537 |
| Random Forest | 6,656 | 10,517 | 0,444 |

Ridge có RMSE tốt hơn; vẫn giữ lựa chọn từ validation. Bootstrap MAE RF: khoảng
4,290–10,163 triệu (2.000 lần lấy mẫu trên 28 mẫu test); chưa phản ánh mọi bất định nguồn.
Dữ liệu ít, snapshot hỗn hợp 2025–2026, không chia theo thời gian, nhãn nguồn chưa phải gold.
Đây là thực nghiệm học phần, chưa chứng minh khả năng tổng quát toàn thị trường.

Bằng chứng:

- `outputs/metrics/salary_bd9af2fa002caae8/REPORT.md`, metrics, predictions, residuals và biểu đồ.
- `models/salary/bd9af2fa002caae8/manifest.json` và các pipeline nhỏ đã fit.
- `outputs/training_logs/salary_20261017T092948Z/{run.json,console.log}`.
- `outputs/eda/20261017T092843Z_e3747c/`: biểu đồ Matplotlib/Seaborn trên train CNTT VN.

## 2. Gemma: chuẩn bị xong, đang chờ người dùng xác nhận train

Điều kiện xác nhận chỉ áp dụng Gemma; không chặn mô hình lương. Chưa chạy LoRA hoặc
smoke train Gemma. `make gemma-train` và `make gemma-smoke` **chỉ xuất kế hoạch**.

Model chính thức `google/gemma-4-E4B-it`, revision
`ee0ef6023621cff504d758262d4e04895a5af4a2`. Trọng số gốc 15.992.595.884 byte đã khớp SHA256
Google; bản MLX 4-bit có 4.198.925.877 byte. Không cần tải lại trên máy hiện tại.
Chi tiết: `outputs/gemma_preparation/weights.json`. GPU Metal M3 Pro đã tính tensor được;
chưa xác minh LoRA, thông lượng train, bộ nhớ train hay chất lượng adapter.

Bộ `data/finetune/manifest.json`:

| Tập | Mẫu JSONL | Tin nguồn | Nhóm nguồn |
|---|---:|---:|---:|
| train | 364 | 122 | 121 |
| valid | 72 | 25 | 25 |
| test | 82 | 28 | 28 |

123 tin train gốc còn 122 sau khử prompt/nhãn giống nhau. Mỗi tin có bản gốc và tối đa
hai biến thể bỏ lương hoặc kinh nghiệm; bỏ biến thể nếu bằng chứng trường đó vẫn xuất hiện
trong các trường khác. Các biến thể giữ nguyên split nguồn, không tạo tin độc lập mới.
Không có ID/nhóm/prompt giao nhau giữa các tập, không có prompt mang target mâu thuẫn.

Nhãn **silver_source_fields**: từ các trường đã làm sạch, chưa qua duyệt thủ công độc lập.
Input là phiếu tin tuyển dụng, chưa phải toàn bộ tin văn bản tự do. Không dùng để huấn luyện
chất lượng tư vấn nghề nghiệp. Có 8 khóa JSON: role, location, experience_years, skills,
salary_min, salary_max, currency, salary_period. Giữ kỳ lương/tiền tệ gốc, không đổi ngoại tệ,
không thay cận bằng trung điểm. Trường bị bỏ trả null. Cặp prompt/chat đã kiểm tra prefix
mask và token bằng tokenizer thật; dài nhất 614 token, không cắt mẫu.

### Các bước chạy sau khi xác nhận

1. Mở `notebooks/03_gemma_extraction.ipynb` hoặc dùng Terminal trong thư mục dự án.
2. Chạy `make validate-sft` và `make gemma-train` để đọc kế hoạch.
3. Xác nhận với Codex rằng bạn đồng ý train Gemma theo kế hoạch này.
4. Sau xác nhận, lệnh thực thi là:

```bash
.venv/bin/python scripts/gemma_train.py --config configs/gemma_train.yaml --confirm-training
```

Trial: MLX 4-bit LoRA, 4 lớp cuối, rank 8, scale 20, batch 1, 100 iterations (không phải
100 epochs), learning rate 1e-4, seed 42, context 1024, mask prompt, gradient checkpoint.
Log mỗi 5 bước; validation 5 batch mỗi 25 bước; checkpoint mỗi 25 bước. Đây là trial ban
đầu, chưa phải tham số tối ưu. Chưa hứa thời gian chạy vì chưa benchmark train thực tế.

Wrapper rehash trọng số trước khi train, giữ log console/exit code/config tại
`outputs/training_logs/gemma_<UTC>/`; adapter/checkpoint ở `adapters/gemma-jobs/<UTC>/`.
Không ghi đè lượt trước. Console MLX-LM cho biết train/validation loss và tốc độ/bộ nhớ;
loss không phải độ chính xác trích xuất. Nếu lỗi, giữ log và sửa trước khi chạy lại.

5. Suy luận/đánh giá base và adapter trên validation (không train):

```bash
.venv/bin/python scripts/evaluate_gemma.py --generate --split valid --output outputs/metrics/gemma_trial_base_valid
.venv/bin/python scripts/evaluate_gemma.py --generate --split valid --adapter adapters/gemma-jobs/RUN_ID --output outputs/metrics/gemma_trial_adapter_valid
```

Chọn checkpoint theo validation rồi đánh giá cả hai trên `--split test`, thư mục output
mới, giữ nguyên mọi tham số. Script xuất predictions và JSON validity, schema validity,
accuracy từng trường, Skill micro F1. Chưa chạy bước này nên chưa có metric Gemma.
Trường thiếu tính sai; numeric tolerance 1e-6; skills dùng tập và F1 không phân biệt hoa/thường.
Metric này đo khớp nhãn silver, không chứng minh nhãn đúng thực tế.

## 3. Git và dữ liệu lớn

Người dùng chọn nhánh source gọn. Nhánh `publish/salary-gemma-prep` là snapshot source
độc lập: không mang các commit cha chứa CSV >100 MB. Lịch sử cũ và toàn bộ raw/processed
trên máy vẫn được giữ nguyên trên `main` và `feat/salary-training-gemma-prep`.
Không force-push, không rewrite lịch sử cũ. Danh sách file thực tế và checksum nằm trong
`outputs/source_publication/manifest.json`.

Snapshot có code, notebook đã chạy, JSONL, bộ chia v1.0.1, hai CSV sạch VN, pipeline lương
nhỏ, metrics/log, config tái lập. Không đưa trọng số Gemma, cache, token hoặc raw/bản audit
cồng kềnh lên Git. URL/revision/checksum để tải nguồn nằm ở `configs/data_sources.json` và
các manifest. File người dùng chưa có URL gốc; phải bổ sung thủ công nếu cần tái làm sạch
nguồn đó, không thể tải lại tự động. Nguồn/điều khoản chưa xác nhận ghi tại DATA_SOURCES.md.

Sau clone có thể kiểm tra dữ liệu huấn luyện bằng:

```bash
.venv/bin/python scripts/verify_salary_splits.py --training-only
make validate-sft
make test-data
```

`make data-verify` đầy đủ cần cả raw và các bảng trung gian lớn trên máy gốc; chế độ
training-only chỉ xác minh CSV đã đóng băng, không thay thế audit nguồn toàn bộ.
Tải model riêng bằng revision cố định:

```bash
.venv/bin/python scripts/download_gemma.py --revision ee0ef6023621cff504d758262d4e04895a5af4a2 --convert
```

API hiện chỉ có health; bước tích hợp dự đoán/trích xuất/giao diện và báo cáo cá nhân
chưa hoàn thành. Xem `docs/DELIVERABLES.md`.

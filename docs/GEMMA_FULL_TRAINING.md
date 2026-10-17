# Huấn luyện Gemma trên toàn bộ bộ train

Lệnh chạy thật:

```bash
cd /Users/scara2906/Downloads/ML
make gemma-adapter
```

Lệnh này kiểm tra dữ liệu, nạp `google/gemma-4-E4B-it` đã chuyển MLX 4-bit rồi
huấn luyện LoRA **1 epoch = 364 optimizer steps**, batch 1. Không chỉ in kế hoạch.
Việc bạn gõ lệnh chính là yêu cầu/xác nhận huấn luyện; không cần xác nhận thêm.
Mỗi lần chạy bắt đầu từ model gốc đã tải, lưu adapter mới, giữ nguyên các lượt trước.

Để chạy nhiều vòng:

```bash
EPOCHS=3 make gemma-adapter
# 3 epochs = 1.092 bước, mỗi mẫu train xuất hiện một lần trong mỗi epoch.
```

## Dữ liệu đã chuẩn bị

Bộ snapshot `data/finetune_full/v1.0.0/` có đầy đủ:

| File | Mẫu JSONL | Tin nguồn |
|---|---:|---:|
| train.jsonl | 364 | 122 |
| valid.jsonl | 72 | 25 |
| test.jsonl | 82 | 28 |

`manifest.json` và `full_training.json` ghi checksum, số mẫu và xuất xứ. Đây là
bản xuất đủ toàn bộ JSONL trích xuất hiện có, không sinh thêm tin giả. Mẫu bỏ trường
là biến thể của cùng tin. Nhãn silver chưa được duyệt độc lập như gold.
CSV lương khác cần nhãn trích xuất phù hợp trước khi bổ sung vào Gemma.

Huấn luyện chỉ dùng train; valid dùng tính loss, test giữ cho đánh giá sau khi chốt
pipeline. Batch 1 bảo đảm không bỏ mẫu cuối. Script từ chối batch không chia hết
số mẫu, vì bộ nạp MLX loại phần batch thiếu. Tất cả mẫu dài tối đa 614 token,
giới hạn context 1.024, không cắt nội dung.

## Cấu hình và output thật

- LoRA rank 8, 4 lớp cuối, scale 20; learning rate 1e-4, seed 42.
- Gradient checkpoint, mask prompt; log mỗi 10 bước, lưu checkpoint mỗi 100 bước.
- Validation toàn bộ 72 mẫu trước bước đầu và ở cuối mỗi epoch (trước update tại
  số bước được hiển thị theo vòng lặp MLX).
- Cấu hình tính toán: `configs/gemma_full.yaml`, `scripts/gemma_full_train.py`.
- Console in `REAL TRAINING`, `Training`, train/validation loss và số bước.
- Log/config/exit code: `outputs/training_logs/gemma_<UTC>/`.
- Adapter/checkpoint: `adapters/gemma-jobs/<UTC>/`.
- Sau khi train thành công, tự kiểm tra file và xuất `manifest.json`, `summary.json`,
  `loss_history.csv`, `loss_curve.png`, `REPORT.md`. Loss không thay thế accuracy/F1.

Muốn chỉ kiểm tra lịch chạy, không train:

```bash
make gemma-plan-full
```

Muốn suy luận bằng adapter đã có (lệnh này không train):

```bash
make gemma-infer-adapter
# Hoặc chỉ định adapter từ log lượt mới:
GEMMA_ADAPTER=adapters/gemma-jobs/20261017T101925Z make gemma-infer-adapter
```

`make gemma-adapter` là train; `make gemma-infer-adapter` là suy luận.
Lệnh suy luận mặc định dùng adapter trial `20261017T094853Z`, vì vậy cần chỉ định
`GEMMA_ADAPTER` khi muốn dùng kết quả của lượt full mới.
Trên máy hiện tại trọng số đã đủ. Máy clone khác cần tải model riêng theo revision
cố định trong README. Base weights và checkpoint trung gian lớn giữ local; adapter
cuối nhỏ được publish cùng source sau khi xác minh.

## Các lượt trước

Trial đầu `20261017T094853Z`: 100 bước và có đánh giá trích xuất trên validation.
Lượt tiếp `20261017T100839Z`: thêm 100 bước từ adapter đó, tổng 200 updates;
optimizer khởi tạo lại và seed 43, không phải resume đầy đủ optimizer. Loss validation
cuối 0,057 chỉ trên 5 batch, chưa có metric trích xuất riêng cho lượt tiếp này.
Các adapter này giữ riêng; lệnh full mặc định bắt đầu từ base, không nạp chúng.

## Kết quả lượt bạn tự chạy: 20261017T101925Z

Lượt bạn tự chạy đã hoàn tất 364/364 bước, exit code 0. Train loss 0,380 → 0,032;
validation loss 1,052 → 0,068 trên toàn bộ 72 mẫu. Adapter cuối đã khớp checksum
trong manifest; log, CSV và biểu đồ loss đã được tạo. Chưa đo accuracy/F1 riêng
cho adapter full. Lượt do Codex khởi động `101734Z`
đã dừng để tránh chạy hai job trên cùng GPU; log riêng vẫn được giữ.

```bash
# Chỉ đọc log, không khởi chạy thêm training:
tail -f outputs/training_logs/gemma_20261017T101925Z/console.log

# Xem cấu hình, trạng thái và exit code:
cat outputs/training_logs/gemma_20261017T101925Z/run.json
```

Ban đầu MLX tính loss trên đủ 72 mẫu validation trước bước train đầu tiên;
chưa thấy dòng train loss trong giai đoạn này không có nghĩa lệnh chỉ in kế hoạch.
Sau đó console hiện train loss mỗi 10 bước, checkpoint mỗi 100 bước. Cuối epoch
có một lượt validation đầy đủ trước update của bước 364 theo vòng lặp MLX.

Hoàn tất thành công khi `run.json` có `status: completed`, `returncode: 0` và
summary/adapter được tạo. File kết quả:

- `adapters/gemma-jobs/20261017T101925Z/adapters.safetensors`
- `adapters/gemma-jobs/20261017T101925Z/adapter_config.json`
- `adapters/gemma-jobs/20261017T101925Z/manifest.json`
- `outputs/training_logs/gemma_20261017T101925Z/summary.json`
- `outputs/training_logs/gemma_20261017T101925Z/loss_history.csv`
- `outputs/training_logs/gemma_20261017T101925Z/loss_curve.png`

Không chạy thêm `make gemma-adapter` trong lúc chờ; đó là lệnh tạo một lượt train
mới. Lệnh xem log và `gemma-infer-adapter` có mục đích khác nhau. Chỉ chạy suy luận
bằng adapter mới sau khi lượt train hoàn tất.

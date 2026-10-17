# Đánh giá và cải tiến Gemma

Người dùng đã cho phép train lặp để cải thiện chất lượng ngày 17/10/2026.
Các lượt dưới đây train thật bằng MLX LoRA trên máy, không phải kế hoạch mô phỏng.
Mỗi lượt có config, console, exit code, checksum adapter và dự đoán thô riêng.

## Protocol cố định trước khi xem kết quả full

`configs/gemma_tuning_protocol.json` ghi tiêu chí trước khi đọc metric của adapter
full `20261017T101925Z`:

- Chỉ chọn model bằng validation: 72 biến thể từ 25 tin nguồn. Test 82 biến thể
  từ 28 tin nguồn chỉ chấm một lần cho adapter được chọn sau cùng.
- Điểm chọn = 50% accuracy trung bình 8 trường + 30% Skill micro F1 + 20% schema.
  Chỉ thay bản tốt nhất nếu tăng ít nhất 0,002; JSON không giảm, accuracy không
  giảm quá 0,005 và Skill F1 không giảm quá 0,01.
- Mục tiêu validation: JSON 100%, schema ≥98%, accuracy trung bình ≥95%, Skill F1 ≥92%.
- Tối đa 3 ứng viên, mỗi ứng viên thêm một lượt qua đủ 364 mẫu train, learning
  rate 5e-5 / 2e-5 / 1e-5, seed 44 / 45 / 46. Tiếp tục từ adapter tốt nhất,
  optimizer khởi tạo lại; không gọi đây là resume đầy đủ trạng thái optimizer.
- Dừng khi đạt toàn bộ mục tiêu, hoặc 2 ứng viên liên tiếp không được chọn,
  hoặc hết 3 ứng viên. Không cam kết sai số bằng 0 hoặc cực tiểu toàn cục.

Mục tiêu do nhóm đặt ra, không phải chuẩn đánh giá bên ngoài. Không đổi tiêu chí,
sửa đầu ra hoặc sửa validation/test để đạt điểm mong muốn. Loss chỉ để theo dõi
hội tụ; không thay thế metric trích xuất. Loss 5 batch của các lượt tuning không
so trực tiếp với loss toàn bộ 72 mẫu của lượt full đầu.

## Phân tích lỗi ban đầu

Adapter full một epoch có JSON 100%, schema 88,89%, Skill F1 90,22%.
Accuracy role 80,56%, location 100%, experience 98,61%, skills exact 44,44%;
4 trường salary_min/salary_max/currency/salary_period đều 100% trên validation.
8 lỗi schema đều do kỹ năng trùng lặp. Model còn đổi alias kỹ năng hoặc thêm
kỹ năng suy ra từ tên tin. Một số vai trò có thể mơ hồ giữa frontend/mobile;
nhãn đang là silver từ quy tắc nguồn, chưa được người độc lập duyệt.

Giả thuyết thử: thêm một epoch với learning rate nhỏ hơn giúp bám quy ước nhãn
và giảm lặp kỹ năng mà không làm giảm trích xuất lương. Các lượt sau chỉ dùng
train có sẵn, giữ nguyên các tập và nhãn đóng băng.

## Các vòng cải tiến đã đo

1. `20261017T104241Z`: thêm 364 updates từ baseline, lr 5e-5, seed 44.
   Role sai 14 → 5 mẫu, skills exact sai 40 → 34, schema lỗi 8 → 4.
   Experience sai 1 → 3 (suy 0 từ tin khi nhãn cần null). Skill F1 91,02%,
   accuracy trung bình 92,71%, schema 94,44%. Được chọn theo điểm và guardrail;
   không khẳng định mọi trường đều tốt hơn.
2. `20261017T105728Z`: thêm 364 updates từ lượt 1, lr 2e-5, seed 45.
   Role sai còn 4, skills exact sai 31, experience sai 1, schema lỗi 3.
   Skill F1 93,76%, accuracy trung bình 93,75%, schema 95,83%. Được chọn.
3. `20261017T111205Z`: thêm 364 updates từ lượt 2, lr 1e-5, seed 46.
   Skill F1 giảm còn 92,90%, role accuracy còn 91,67%, schema vẫn 95,83%.
   Không được chọn vì điểm tổng hợp giảm. Dừng sau đủ 3 ứng viên theo protocol;
   giữ lượt 2, tổng lineage 1.092 updates. Mục tiêu schema 98% và accuracy trung
   bình 95% vẫn chưa đạt; không thay mục tiêu sau khi xem kết quả.

JSON vẫn 100%; bốn trường lương/tiền tệ/kỳ lương vẫn 100% trên validation ở
cả ba bản. Đây là trích xuất lương đã ghi trong phiếu, không phải dự đoán lương
chưa biết. Các cấu hình thay cả learning rate và seed; không suy diễn mức đóng
góp nhân quả riêng của learning rate. Các lượt tiếp theo và quyết định cuối
nằm trong `selection.json`/`FINAL_REPORT.md`.

## Lệnh đánh giá: chỉ suy luận, không train

```bash
.venv/bin/python scripts/evaluate_gemma.py --generate --split valid \
  --adapter adapters/gemma-jobs/RUN_ID \
  --output outputs/metrics/gemma_RUN_ID_adapter_valid
```

Mỗi thư mục output phải mới để giữ bằng chứng. Temp 0, seed 42, tối đa 256 token,
không thinking. Chấm JSON thô bằng json.loads, không bỏ Markdown fence, sửa key,
loại kỹ năng lặp hay đổi alias trước khi tính điểm. Skill F1 dùng tập tên kỹ năng
casefold; skills exact dùng tập chuỗi gốc, schema kiểm tra cả duplicate.

```bash
# Chỉ tính lại/chọn bằng dự đoán đã lưu; không train hoặc gọi model:
.venv/bin/python scripts/select_gemma_adapter.py --evaluations \
  outputs/metrics/gemma_20261017T101925Z_adapter_valid \
  outputs/metrics/gemma_RUN_ID_adapter_valid
```

Script từ chối metric từ test, checksum sai, điều kiện sinh khác nhau và ứng viên
vượt điều kiện dừng. `outputs/metrics/gemma_tuning/selection.json` ghi quyết định;
`REPORT.md` có bảng đối chiếu. Mỗi run có `error_analysis.json` lưu lỗi từng trường,
lỗi schema, metric theo biến thể và MAE số trên các cặp cùng đơn vị, đều có số mẫu.
MAE số này chỉ là diagnostic; dự đoán thiếu/sai kỳ vẫn bị phạt ở accuracy chính.

## Lệnh train thật

```bash
.venv/bin/python scripts/gemma_train.py --config configs/gemma_tune_01.yaml \
  --confirm-training --summarize \
  --confirmation-note 'User authorized repeated Gemma improvement on 2026-10-17'
```

Mỗi config lưu rõ adapter cha. Chỉ chạy một tác vụ GPU mỗi lúc. Lệnh trên cập nhật
trọng số; `make gemma-infer-adapter` và `evaluate_gemma.py` chỉ suy luận.
Đọc `selection.json` để lấy adapter được chọn, không lấy run mới nhất theo tên
hoặc loss thấp nhất. Giữ lại adapter trước để có thể quay lại mà không train lại.

Bộ nhãn chỉ 122 tin train độc lập, được biến đổi thành 364 mẫu. Kết quả chưa
chứng minh khả năng đọc mọi tin tuyển dụng dài hay tư vấn nghề nghiệp. Muốn cải
thiện chắc chắn hơn cần thêm tin độc lập và nhãn gold đã kiểm tra nguồn.

# Trạng thái cập nhật — 17/10/2026

Đã chạy EDA và mô hình lương thật, chuẩn bị JSONL Gemma và xác minh đủ trọng số.
Xem [runbook hiện tại](TRAINING_RUNBOOK.md) và `outputs/gemma_preparation/weights.json`.
Gemma chưa train; chờ xác nhận riêng của người dùng. Nội dung bên dưới là biên bản
thiết lập ban đầu, các dòng "chưa có dữ liệu/trọng số" là trạng thái lịch sử.

---

# Biên bản kiểm tra môi trường — 17/10/2026

Máy: Apple M3 Pro, RAM 36 GiB, macOS arm64. Python 3.11.17 trong `.venv`.
Đây là biên bản bước thiết lập ban đầu; dữ liệu được bổ sung sau đó cùng ngày,
xem `DATA_SOURCES.md` để biết trạng thái dữ liệu hiện tại.
Nguồn model đã chốt: `google/gemma-4-E4B-it`, revision
`ee0ef6023621cff504d758262d4e04895a5af4a2`.

## Đã xác minh

- Cài thư viện vào `.venv`; `pip check` không có xung đột.
- Cài lại qua `bash scripts/setup.sh` dùng file lock 161 package thành công.
- MLX 0.32.4 tính toán trên GPU Metal Apple M3 Pro.
- Ridge và Random Forest fit/predict được; MAE, RMSE, R² hoạt động.
- Matplotlib/Seaborn xuất PNG; Pandas/OpenPyXL ghi rồi đọc lại XLSX.
- FastAPI `/health` trả HTTP 200 qua TestClient; chưa nạp model nghiệp vụ.
- Hai notebook đúng cấu trúc và được thực thi bằng kernel `it-career-insight`.
- Ruff kiểm tra mã và định dạng đạt.
- JSONL giả lập có 6/2/2 mẫu, không trùng ID nguồn/prompt giữa các tập;
  tokenizer chính thức áp dụng chat template, mask prompt và giới hạn 512 token được.
- Cấu hình smoke/train và tùy chọn converter phù hợp CLI MLX-LM 0.32.2.
- Ba JSONL dữ liệu thật ban đầu vẫn trống; lệnh kiểm tra từ chối train trên tập trống.

## Chưa xác minh / chưa triển khai

Trọng số Google khoảng 16 GB tải chậm; đã dừng lượt tải và giữ cache. Chưa có
model MLX chuyển đổi hoàn chỉnh, chưa chạy suy luận hoặc huấn luyện QLoRA trên
model đầy đủ. Chạy `make gemma-download` trên kết nối ổn định để tải lại và chuyển đổi.

Chưa có dataset thật, EDA thị trường, mô hình lương huấn luyện thật, adapter nghiệp vụ,
tư vấn kỹ năng, frontend hoàn chỉnh, remote Git hoặc báo cáo theo mẫu giảng viên.
Toàn bộ số đo trong `outputs/environment/` chỉ phục vụ kiểm tra kỹ thuật, không phải
kết quả thực nghiệm của đề tài.

## Bằng chứng

`outputs/environment/check.json`, `check_mlx.json`, `notebook_check.json`,
`tokenizer_check.json`, `mlx_cli_check.json`, `sft_status.json`, `model_source.json`;
`requirements-lock-macos-arm64.txt` lưu phiên bản thư viện.

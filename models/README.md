# Model artifacts

Nguồn chính thức: `google/gemma-4-E4B-it`.

- `gemma-source/`: snapshot Google; chỉ coi tải hoàn tất khi có `manifest.json`.
- `gemma-mlx-4bit/`: nhánh văn bản chuyển MLX affine 4-bit; converter chạy sau khi tải xong.
- `salary/`: pipeline Ridge/Random Forest được huấn luyện từ dữ liệu thật sau này.

Weights được ignore; manifest nguồn và README được phép commit.
Tạo lại model bằng `make gemma-download` trên Mac có Metal và mạng ổn định.

# Nhật ký thay đổi

## 2026-10-17 — Salary training và Gemma preparation

- Chuẩn bị đầy đủ notebook EDA/so sánh baseline, Ridge, Random Forest; chạy trên split
  developer v1.0.1 (123/25/28), chọn bằng validation MAE, test khóa theo protocol.
- Lưu pipeline, kiểm tra reload trong Python mới; xuất metrics, predictions, bootstrap
  MAE, lỗi theo vai trò, biểu đồ và liên hệ kỹ năng. RF test MAE 6.656.370 VND/tháng.
- Thêm runner notebook và transcript salary_20261017T092948Z; lưu bản output riêng
  tại salary_20261017T094526Z. Sửa ghi đè pipeline khi chạy lại, giữ byte của model đã
  gắn với test cache; grid/seed/split giữ nguyên. Protocol hiện hành bd9af2fa002caae8; báo cáo đầy đủ baseline,
  Ridge và Random Forest, không chọn lại model từ test.
- Kiểm tra đủ trọng số Google Gemma-4-E4B-it revision ee0ef602...; SHA256 khớp chính thức.
  Kiểm tra file MLX 4-bit và tokenizer prompt masking; không tải lại file đã đủ.
- Tạo JSONL silver job-card extraction 364/72/82, kế thừa nhóm nguồn. Loại prompt trùng
  và biến thể còn bằng chứng ẩn; giữ lương gốc theo kỳ/tiền tệ, missing = null.
- Thêm kiểm tra schema/nhóm/prompt, notebook Gemma, metric extraction và wrapper plan-only.
  Theo yêu cầu người dùng, CHƯA train/smoke train Gemma; cần xác nhận riêng sau kế hoạch.
- Nhánh source gọn độc lập tránh commit cha chứa CSV >100 MB; giữ toàn bộ lịch sử/dữ liệu
  local. Trọng số/raw lớn không publish; whitelist/checksum ghi trong publication manifest.

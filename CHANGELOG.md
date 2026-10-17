# Nhật ký thay đổi

## 2026-10-17 — Gemma trial đã được xác nhận

- Người dùng trả lời `xac nhan`; đã chạy đúng cấu hình 100 iterations, 4 lớp cuối,
  LoRA rank 8, batch 1, context 1024, lr 1e-4; không mở rộng trial hoặc dùng test.
- Run `20261017T094853Z` hoàn tất exit 0. Train loss 0,501 → 0,081;
  validation loss 1,135 → 0,070 trên 5 batch/lần, đo trước update tại iteration hiển thị.
- Lưu checkpoint 25/50/75/100, final adapter 6.953.691 byte, SHA256 và manifest.
  Trọng số gốc và checkpoint trung gian giữ local; final adapter nhỏ được publish.
- Xuất CSV/biểu đồ loss và runbook; so sánh model gốc/adapter trên validation,
  giữ raw predictions và diagnostic bỏ Markdown fence để phân biệt định dạng/nội dung.
- Validation 72 mẫu / 25 tin: adapter JSON validity 100%, schema 90,3%, Skill F1
  0,884; base sau bỏ fence có Skill F1 0,835. Giữ 7 lỗi schema (6 duplicate skill,
  1 sai keys) và dự đoán thô; không train thêm hoặc dùng test.
- Mặc định lệnh train vẫn xuất kế hoạch; lượt train mới vẫn cần xác nhận người dùng.

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

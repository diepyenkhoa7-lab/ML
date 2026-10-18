# Changelog

## 2026-10-18 — Rà soát nhãn và fine-tune Gemma reviewed v2

- Rà soát đủ 214 dòng: 201 chấp nhận AI-reviewed silver, 13 loại; không có human gold.
  Tách corpus theo công ty: train501 (137 mới +364 replay), valid31/test33 mới.
- Run `20261018T002705Z` hoàn tất 501 bước, LR1e-5; validation loss 0,392→0,110.
  Giữ config, xác nhận, lineage, checksum, loss CSV/đồ thị và trọng số candidate riêng.
- F1 validation mới 72,73%→78,49%, nhưng legacy 93,76%→90,22% và không đạt
  score/schema guards: không promote, giữ adapter web cũ, không chấm test mới/cũ.
  Không diễn giải loss/extraction F1 thành cải thiện MAE lương.
- Raw predictions, paired selection và chẩn đoán lỗi được lưu; 79 tests, Ruff59 và
  strict corpus đạt. Train thật và suy luận tách rõ; protocol một candidate chặn chạy trùng.

## 2026-10-18 — Thử nghiệm nhãn rõ kỳ tháng v3/v3.1

- Train thật 24 cấu hình Ridge/RF; v3.1 chọn RF leaf=5, 214 nhãn có bằng chứng kỳ tháng,
  không dùng nhãn giả định kỳ. Validation 28 mẫu: MAE 4,847M / RMSE 6,707M VND.
- Lưu câu dẫn chứng, xử lý khung header khác nội dung, giữ `VND MONTH`, loại mâu thuẫn
  kinh nghiệm và công ty từng gặp khỏi kiểm tra mới. Thêm 89 JobPosting công khai và
  Stack Overflow 2026 đã kiểm tra SHA; dữ liệu khảo sát khác target, không trộn nhãn.
- Không promote: chỉ 3 mẫu/3 công ty độc lập trong vòng cuối và market gap 31,09%,
  kém v2 21,09%. Giữ v2 trên web, chặn nạp checkpoint thất bại gate.
- Xuất 214 dòng annotation pending chỉ thuộc train, chưa có gold; không fine-tune Gemma
  lại bằng nhãn chưa duyệt. Giữ toàn bộ test/weights cũ và logs thực nghiệm.

## 2026-10-18 — Thêm dữ liệu, train salary v2 và đối chiếu thị trường

- Tải nguồn TiniX606878 tin có revision/checksum/CC-BY-NC; raw lớn tải riêng. Frozen
  v2.1.0 có train79 explicit+1078 weak(monthly assumption, weight0,3), valid25/test30
  explicit-month; company-disjoint, oldholdoutcompany excluded. Drafts chưa fit giữ local.
- Train thật12 ứng viên; chọn Ridgealpha1 bằng validation. Cùng30test mới: MAE4,433M
  soRFv1 8,246M, RMSE5,664M so10,508M; passfixedgate, kích hoạt quaapplication.json,
  RF đối chiếu và v1rollback. Giữ nguyên Gemma/frozenv1; không tuning theo test đã mở.
- Đối chiếu ITviec/TopDev riêng: lệch aggregate ITviec v2~21,1%, v1~8,2% nên không
  tuyên bố cải thiện marketalignment; không đưa reportmedian vào nhãn cá nhân. Web
  hiển thị modelthực chạy, salaryoffer estimate và ITviec reference/source riêng.
- 63 tests đạt; train/serve parity, selection/export/metric, frozenv2 và marketreference.
  API CSV/XLSX/JSON và Gemma GPU thật→Ridge đạt. Báo cáo/runbook/journal có evidence.

## 2026-10-18 — ECC architecture audit và tích hợp Gemma rõ trên web

- Sửa 3 finding high và 5 medium: hợp đồng Gemma theo request/dòng/hash, provenance
  thực chạy, checksum snapshot, queue giới hạn 2, phục hồi state hỏng, evidence kỹ năng
  từ train đã kiểm chứng, UI chống response cũ, managed GPU lock và parser strict.
- Web hiển thị adapter Gemma, số mô tả thành công/lỗi, raw JSON và trạng thái từng dòng.
  API chỉ suy luận, không có endpoint train; không đổi trọng số/nhãn/holdout đã chốt.
- 55 tests đạt; Ruff 42 file, Prettier/build, frozen CSV/strict JSONL đạt. API và một
  mẫu Gemma GPU thật → RF đạt; browser kiểm tra phản hồi đến muộn của advice/pagination.
- Báo cáo trước/sau, JSON schema ECC và screenshot thật ở outputs/architecture_audit/2026-10-18/.
  Luna 5.6 viết docs/PROJECT_JOURNEY.md từ repo/log/metric có dẫn nguồn.

# Nhật ký thay đổi

## 2026-10-17 — Ứng dụng từ nhập bảng đến xuất kết quả

- Lập kế hoạch/AC và triển khai Vue 3 + FastAPI: CSV/XLSX/JSON → preview/ghép cột →
  dự đoán RF/Ridge từ pipeline đã lưu → biểu đồ Matplotlib/Seaborn → CSV/XLSX/JSON/PNG/ZIP.
- Dữ liệu gốc và số dòng được giữ; dòng lỗi có lý do, bản trùng không đếm lại trong
  thống kê. Không đoán tiền tệ/kỳ; không tạo metric khi thiếu nhãn hoặc trend khi thiếu ngày.
- Gemma worker inference-only dùng adapter 105728Z, checksum/schema/context guard,
  kiểm tra GPU đang train, lưu raw output. Đã kiểm tra thực chuỗi extraction → RF.
- Tư vấn theo hồ sơ dùng các kỹ năng có support train ≥5, hệ số Ridge dương và
  chênh lệch RF dương; giải thích bằng số liệu Python, không hứa tác động nhân quả.
- Export chống công thức bảng tính, manifest ghi input/model/code/output hash.
  Runtime/upload local ở outputs/app_runtime bị loại khỏi Git. Source publication
  chỉ giữ các lượt Gemma đã review/release, không lấy thêm job người dùng đang chạy.
- 40 tests đạt, Ruff/Prettier/build đạt; browser kiểm tra upload bằng File API từ
  template app, mapping guard, phân trang, chuyển nguồn biểu đồ, download và tư vấn.
  Ảnh desktop/mobile thật và bằng chứng tại outputs/app_verification/.
- `make app` build Vue và chạy app tại 127.0.0.1:8000, không train. Hướng dẫn tại
  docs/APP_RUNBOOK.md. Đây là app local một người dùng, chưa triển khai public.

## 2026-10-17 — Đánh giá full và train lặp Gemma thật

- Theo xác nhận mới của người dùng, chấm full baseline và train thêm 3 lượt × 364
  updates với lr 5e-5 / 2e-5 / 1e-5, seed 44/45/46; resume adapter tốt nhất,
  optimizer khởi tạo lại. Cấu hình/console/loss/exit code/checksum lưu riêng từng run.
- Khóa protocol trước khi đọc baseline: chọn bằng validation, không sửa output/nhãn,
  có ngưỡng cải thiện/guardrail và giới hạn 3 ứng viên. JSONL/splits giữ nguyên checksum.
- Baseline full Skill F1 90,22%; lượt 1 đạt 91,02%; lượt 2 đạt 93,76%; lượt 3
  giảm còn 92,90% nên loại. Chọn `20261017T105728Z`, lineage 1.092 updates.
- Validation bản chọn: JSON 100%, schema 95,83%, accuracy trung bình 93,75%,
  skills exact 56,94%. Mục tiêu schema 98%/accuracy 95% chưa đạt; không hạ mục tiêu.
- Test chỉ chấm một lần sau khóa chọn: JSON 100%, schema 95,12%, accuracy trung
  bình 93,90%, Skill F1 91,85%, skills exact 54,88% trên 82 biến thể / 28 tin.
  Không train tiếp theo lỗi test. Nhãn silver, chưa phải benchmark gold hoặc mọi tin tự do.
- Đặt `make gemma-infer-adapter` mặc định về adapter được chọn; giữ `make gemma-adapter`
  là train từ base. Đồng bộ system prompt suy luận với train; báo lỗi schema, không sửa
  đầu ra. Giữ nguyên file suy luận người dùng tự tạo, không publish output tạm đó.
- Cập nhật notebook 03, kiểm tra các cell mặc định không train/inference; thêm báo cáo,
  biểu đồ so sánh, lỗi từng trường/slice và numeric MAE cùng đơn vị. 30 unit tests,
  Ruff, strict JSONL và frozen CSV integrity đạt. Trọng số base/checkpoint giữ local.

## 2026-10-17 — Train thật toàn bộ JSONL và tách lệnh suy luận

- `make gemma-adapter` train thật toàn bộ train JSONL, mặc định 1 epoch = 364 bước;
  `EPOCHS=3` tính 1.092 bước. Chuẩn bị snapshot đủ 364/72/82, giữ valid/test riêng.
- `make gemma-infer-adapter` chỉ suy luận; README và runbook phân biệt rõ các lệnh,
  nhắc chỉ định GEMMA_ADAPTER để nạp adapter full mới thay cho default trial cũ.
- Người dùng tự chạy full run `20261017T101925Z`: hoàn tất 364/364, exit 0;
  train loss 0,380 → 0,032, validation loss 1,052 → 0,068 trên đủ 72 mẫu.
- Dừng riêng lượt trùng do Codex khởi động `101734Z` ở khoảng 40 bước; giữ nguyên
  lượt người dùng và log. Không khởi chạy suy luận hay huấn luyện mới trong giám sát.
- Lưu config/console/CSV/biểu đồ/summary và final adapter 6.953.691 byte với checksum.
  Accuracy/F1 của adapter full chưa đo; metric trial 100 bước được ghi riêng.
- Lượt tiếp `100839Z` trước đó đã train thêm 100 từ adapter đầu, optimizer reset,
  seed 43; tổng lineage 200 updates, validation loss 0,057 trên 5 batch, chưa có F1 riêng.
- Bổ sung kiểm tra tương thích/checksum resume và coverage cả epoch; 25 unit tests
  và Ruff đạt trước lượt full thực tế. Không đưa checkpoint trung gian/base weights lên Git.


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

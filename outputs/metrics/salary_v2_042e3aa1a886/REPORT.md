# Salary v2.1.0 — kết quả train thật (18/10/2026)

## Kết quả trên cùng holdout mới

| Model | MAE triệu VND/tháng | RMSE triệu | R² | Tỷ lệ sai số ≤5 triệu |
|---|---:|---:|---:|---:|
| RF v1 (model cũ) | 8,246 | 10,508 | -0,582 | 30,0% |
| Median baseline | 6,958 | 8,998 | -0,160 | 40,0% |
| RF v2 | 5,737 | 6,990 | 0,300 | 43,3% |
| **Ridge v2 (được chọn)** | **4,433** | **5,664** | **0,540** | **60,0%** |

30 tin test có bằng chứng kỳ tháng, từ 23 nhóm công ty chưa có trong train/validation. Trên cùng tập này Ridge giảm MAE khoảng 46,2% so với RF v1. Bootstrap theo công ty, 2.000 lần, khoảng 95% của chênh MAE v1−v2 là 0,707–6,776 triệu. Tập còn nhỏ/silver, không đại diện mọi vai trò hay toàn thị trường. 6,656 triệu trên 28 test cũ là kết quả lịch sử khác tập, không dùng làm mẫu số cải thiện.

## Dữ liệu, lựa chọn và giới hạn nhãn

TiniX 606.878 raw → 207.122 tin năm 2025–2026 → 3.489 title candidate → lọc tám vai trò, kinh nghiệm, số tiền VND, range/censor/period → loại mâu thuẫn và trùng nội dung. Frozen v2.1.0: strict train79, weak train1.078, validation25, test30. Weak thiếu kỳ lương được giả định tháng và chỉ vào train với trọng số0,3; không tuyên bố đây là nhãn xác minh. Không dùng lương/công ty/ID/title/description/benefits làm feature. Kỹ năng lấy từ requirements theo lexicon cố định; model dùng năm kinh nghiệm, vai trò, cấp bậc, khu vực, kỹ năng.

Split theo normalized company, kể cả weak train; loại công ty của v1 valid/test trước khi chia. Không bảo đảm mọi alias/tin gần trùng đều được bắt vì nguồn thiếu URL/ngày cụ thể. Tất cả nhãn vẫn silver, gross/net có thể chưa rõ. Draft2.0.0/2.0.1 chỉ chuẩn bị, không fit model.

Hai nhánh strict và strict+weak, mỗi nhánh Ridge alpha1/10/100 và RF leaf2/5/10, 300 cây criterion absolute_error, seed42. Tổng12 ứng viên thật. Chọn bằng MAE validation, RMSE phá hòa, preprocessing train-only. Ridge alpha1 strict+weak1157train đạt validation MAE5,424 triệu; RF leaf2 cùng nhánh đạt6,207 triệu. Khóa selection và model artifact trước khi mở test. Không train/refit theo lỗi test.

Gate trước train đều đạt: ≥20 test, MAE giảm≥10% so v1 trên cùng test mới, RMSE≤1,05×v1, R²≥0. `configs/application.json` kích hoạt Ridge v2, model v1 giữ rollback. Random Forest còn dùng đối chiếu. Gợi ý kỹ năng đòi ít nhất5 mẫu cùng vai trò và hệ số Ridge dương; đây là association/counterfactual model, không bảo đảm học kỹ năng sẽ tăng lương.

## Đối chiếu báo cáo uy tín

- ITviec2025–2026: VND/tháng, trung vị theo vai trò/kinh nghiệm. 13 nhóm đủ≥5 profile train để so. Trung vị độ lệch tuyệt đối theo nhóm: **v1 khoảng8,2%; v2 khoảng21,1% (tệ hơn)**. Không giấu kết quả này. Quần thể khảo sát thu nhập khác quần thể lương chào tuyển; chỉ là sanity check, không phải MAE test.
- TopDev2024–2025: USD/tháng gross, trang28–29. Giữ nguyên đơn vị, đối chiếu tỷ số từng vai trò với backend; không tự đổi tỷ giá.

Không đưa trung vị báo cáo thành nhãn cá nhân và không ép hậu xử lý để khớp bảng. Web trình bày riêng dự đoán lương chào tuyển và tham chiếu ITviec kèm nguồn. Giới hạn market-alignment này còn mở, dù gate cho target lương chào tuyển đạt. Nguồn/bảng số: `data/references/README.md`. Biểu đồ và CSV: `external_sanity/`.

## Tích hợp và kiểm chứng

Gemma giữ adapter20261017T105728Z, không train lại. Web đọc mô tả→JSON có kiểm chứng request/dòng/hash→Ridge dự đoán, RF đối chiếu→Matplotlib/Seaborn→CSV/XLSX/JSON/PNG/ZIP. Lương Gemma trích không dùng tính MAE. Giao diện ghi adapter/count/lỗi và model thực chạy, gồm model lịch sử khi mở job cũ.

63 unit/integration tests đạt; checks bổ sung kiểm tra frozen v2, train/serve parity, selected-model/metric/export, tham chiếu thị trường. API thật CSV/XLSX/JSON và một Gemma GPU→Ridge đã đạt (`outputs/research/2026-10-18/api_smoke_v2.json`). Bằng chứng browser/final source export lưu cùng thư mục research; xem trạng thái cuối ở các file kiểm chứng, không suy diễn từ log train.

Không có thêm vòng tuning sau khi đọc test này. Bước tiếp cần dữ liệu tháng/gross/net có provenance tốt, nhãn gold, senior/embedded/data/ML đủ mẫu và holdout mới; không tái dùng test hiện tại làm validation.

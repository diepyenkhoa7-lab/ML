# Salary v2.1.0: dữ liệu, train và vận hành

## Kết quả được triển khai

`configs/application.json` chọn `v2_042e3aa1a886`: Ridge alpha=1. Random Forest leaf=2 là mô hình đối chiếu. Model gốc `bd9af2fa002caae8` còn nguyên để rollback. Gemma dùng adapter đã chọn `20261017T105728Z` để trích mô tả trên web; đợt này không train lại Gemma.

Trên **cùng 30 tin test mới**, MAE của RF v1 là 8,246 triệu VND/tháng, Ridge v2 là 4,433 triệu (giảm khoảng 46,2%); RMSE 10,508 → 5,664 triệu, R² của v2 là 0,540. Không so 4,433 với 6,656 trên test cũ 28 tin như một phép so cùng tập. Chi tiết: `outputs/metrics/salary_v2_042e3aa1a886/`.

## Nguồn và nhãn

Nguồn mới: [TiniX / Vietnamese Job Descriptions](https://huggingface.co/datasets/tinixai/vietnamese-job-descriptions), revision `679c3a17347ff6ce769d9bf510c122a087493cf6`, 606.878 tin nhiều ngành, năm 2022–2026. Giấy phép nguồn CC-BY-NC-4.0, ghi công TiniX AI / Le et al. CareerPathKG 2026. Bản parquet khoảng 280 MiB giữ local, metadata/checksum và tập dẫn xuất cần thiết nằm trong source gọn.

Chỉ lấy nhóm lập trình viên năm 2025–2026. Target là trung điểm **khoảng lương chào tuyển**, VND/tháng. Loại lương thương lượng, ngoại tệ, khoảng hở/up-to, kỳ khác tháng/mâu thuẫn, khoảng quá rộng, công việc PLC/CNC và nhóm ngoài phạm vi. Không suy kinh nghiệm bằng seniority. Kỹ năng lấy từ requirements với từ điển cố định, không lấy lương/benefits/ID/công ty làm feature.

- `train.csv`: 79 tin có bằng chứng kỳ tháng, trọng số 1.
- `weak_train.csv`: 1.078 tin có số tiền VND nhưng thiếu kỳ; **giả định tháng**, trọng số 0,3, chỉ dùng nhánh train mở rộng. Đây là nhãn yếu, không phải dữ liệu đã xác minh đầy đủ.
- `valid.csv`: 25 tin; `test.csv`: 30 tin, đều có bằng chứng tháng. Chia theo công ty, không có công ty chung với train, kể cả weak train. Loại công ty của valid/test v1 trước khi chia.

Cùng nội dung nhưng lương mâu thuẫn bị cách ly; bản trùng chỉ giữ một. Không thể bảo đảm phát hiện toàn bộ alias công ty hoặc tin gần trùng khi nguồn không có URL. Tất cả nhãn vẫn là silver; gross/net có thể chưa rõ. Draft preparation 2.0.0/2.0.1 giữ local để truy vết, chưa dùng train.

## Lệnh tái hiện

Train lương và suy luận ứng dụng là hai việc riêng:

```bash
# Chạy app đã có model; chỉ suy luận
make app

# Kiểm tra chức năng, không train
make app-test
.venv/bin/python scripts/verify_application.py --gemma

# Tải raw đúng revision/checksum khi cần dựng lại dữ liệu
.venv/bin/python scripts/download_salary_v2.py

# Dựng split: cần dữ liệu review v1 local để loại công ty holdout cũ
.venv/bin/python scripts/prepare_salary_v2.py

# TRAIN THẬT Ridge/RF: 12 ứng viên theo protocol đã khóa
.venv/bin/python scripts/train_salary_v2.py

# Chỉ đối chiếu báo cáo, không train và không mở holdout
.venv/bin/python scripts/compare_salary_reports.py
```

Script prepare/train từ chối ghi đè snapshot/experiment đã tồn tại. Khi mở nghiên cứu mới, tạo version protocol/dataset mới và holdout độc lập; không xóa artifact cũ rồi tối ưu tiếp theo test đã mở. Clone nhánh source đã có split, model và metrics nên chạy app/kiểm chứng trực tiếp được; tải raw chỉ cần cho dựng lại pipeline đầu nguồn. Huấn luyện lương không gọi Gemma/GPU.

Có 2 nhánh train (strict và strict+weak), mỗi nhánh 3 alpha Ridge và 3 leaf RF, seed 42. Preprocessing chỉ fit trên train. Chọn từng model/nhánh và model chính bằng MAE validation, RMSE phá hòa; không refit sau chọn. Khóa selection/artifact trước khi mở test một lần. Gate triển khai: ít nhất 20 test, MAE tốt hơn v1 trên cùng test ít nhất 10%, RMSE không tệ quá 5%, R² không âm. Gate đạt; không đồng nghĩa độ chính xác đã đủ cho toàn thị trường.

## Đối chiếu bên ngoài và giới hạn

[ITviec 2025–2026](https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam) cung cấp trung vị thu nhập theo nhóm. [TopDev 2024–2025](https://topdev.vn/download-report), trang in 28–29, dùng USD/tháng gross; giữ đơn vị gốc và so tỷ số theo vai trò, không tự áp tỷ giá. Bảng số và nguồn tại `data/references/`.

Trên 13 nhóm ITviec đủ ít nhất 5 profile train để đối chiếu, trung vị độ lệch tuyệt đối theo nhóm của v2 khoảng 21,1%, **tệ hơn** v1 khoảng 8,2%. Đây không phải MAE cá nhân: nguồn khảo sát thu nhập và nguồn lương chào tuyển có quần thể, kỹ năng, công ty và gross/net khác nhau. Không lấy báo cáo tổng hợp làm hàng nghìn nhãn giả, không ép dự đoán khớp trung vị bằng hậu xử lý.

Web giữ hai số riêng: dự đoán lương chào tuyển của model và trung vị ITviec nếu có đúng vai trò/nhóm kinh nghiệm. Nhóm không có ô tham chiếu thì báo thiếu, không tự bịa. Biểu đồ/CSV đối chiếu tại `outputs/metrics/salary_v2_042e3aa1a886/external_sanity/`.

Hướng nghiên cứu tiếp theo: thu thập nhãn tháng/gross/net có URL và thời điểm rõ, mở rộng nhóm senior/embedded/ML/data engineer còn ít, duyệt nhãn gold và giữ holdout mới. Không dùng lỗi của test v2 hiện tại để chạy vòng chọn tham số tiếp.

## Rollback

Dừng app, đổi `salary_experiment` trong `configs/application.json` về `bd9af2fa002caae8`, rồi `make app`. Không cần train lại. Kết quả lịch sử giữ model và provenance của chính lượt đó; badge/trang kết quả lấy metadata lịch sử, không gán model đang chạy cho kết quả cũ.

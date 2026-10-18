# Dữ liệu và mô hình quốc tế đã triển khai

Ứng dụng có hai ngữ cảnh độc lập: khảo sát tổng thu nhập **USD/năm** và tin tuyển dụng Việt Nam **VND/tháng**. Chọn ngữ cảnh trên dashboard, trang nhập file hoặc tư vấn. Không tự quy đổi tiền tệ, không dùng số USD/năm làm nhãn VND/tháng. ITviec không được dùng trong tư vấn, dữ liệu mới hoặc gate chọn model; các tài liệu thử nghiệm cũ chỉ là lịch sử.

## Nguồn đã tải thật

| Nguồn | Dòng raw | Sử dụng | Giấy phép theo nhà công bố |
|---|---:|---|---|
| [Stack Overflow Developer Survey 2024](https://survey.stackoverflow.co/2024/) | 65.437 | Vai trò, Country, WorkExp, công nghệ đã sử dụng và ConvertedCompYearly; train + biểu đồ + suy luận | ODbL 1.0 cho database; DbCL 1.0 cho nội dung; ghi nguồn Stack Overflow |
| [AIJobs salaries](https://github.com/foorilla/ai-jobs-net-salaries) | 151.445 | Benchmark AI/Data USD/năm riêng; không có kỹ năng hay số năm kinh nghiệm | CC0 1.0 |
| [Level tech jobs](https://huggingface.co/datasets/jobsbylevel/level-tech-jobs-by-ai-level) | 52.296 | Lưu raw và profile; chưa train vì không có salary period hoặc số năm kinh nghiệm | CC BY 4.0 cho compilation; nội dung nhà tuyển dụng giữ quyền gốc |

Revision, URL từng file, dung lượng, SHA-256: `configs/open_salary_sources_20261018.json`. README, USAGE và manifest từng nguồn nằm trong `data/raw/<source>/`. Audit dòng/duplicate/độ phủ Việt Nam: `outputs/data_quality/open_sources_20261018.json`. `training_started:false` trong catalog là trạng thái lúc tải; trạng thái train sau đó được ghi ở manifest mô hình và metric, không sửa bằng chứng tải ban đầu.

## Hai vòng train đã hoàn thành

Protocol được khóa trước khi fit. Chỉ fit preprocessing trên train, chọn tham số và model theo validation, lưu selection trước khi mở test. Không chọn lại model theo test hay dữ liệu người dùng tải lên.

| Bộ / model | Train / validation / test | MAE USD/năm | RMSE USD/năm | R² |
|---|---|---:|---:|---:|
| SO2024 Ridge | 10.261 / 2.368 / 3.158 | 29.274,41 | 53.197,06 | 0,457 |
| SO2024 Random Forest **được chọn** | cùng tập | 29.606,92 | 51.699,84 | 0,487 |
| SO2024 baseline trung vị train | cùng test | 49.017,47 | 73.734,29 | −0,043 |
| AIJobs Ridge **được chọn, nghiên cứu** | 48.321 / 8.206 / 15.363 | 44.895,67 | 64.320,16 | 0,240 |
| AIJobs Random Forest | cùng tập | 46.866,82 | 67.317,62 | 0,168 |
| AIJobs baseline trung vị train | cùng test | 55.177,80 | 73.807,48 | −0,0001 |

SO2024 còn 15.787 dòng sau lọc; AIJobs còn 71.890 dòng unique hợp lệ. `profile_group` giữ các hồ sơ cùng feature ở một tập; không có danh tính để chứng minh độc lập theo người/công ty, và đây không phải temporal holdout. Nhãn là dữ liệu khảo sát tự khai, không phải human gold. Sai số vẫn đáng kể; không gọi đây là “độ chính xác cao” hoặc cam kết sai số cho từng cá nhân. SO2024 là dữ liệu năm 2024, không phải báo cáo lương mới nhất năm 2026.

RF SO2024 được chọn vì MAE validation thấp hơn, dù Ridge có MAE test thấp hơn. Model global phục vụ qua `configs/international_application.json`; không thay `configs/application.json` của model Việt Nam. AIJobs chỉ nằm ở trang so sánh, không dùng để tư vấn kỹ năng. Manifest, split và metric nằm ở các thư mục tên `global_survey_v1_7f2c2dbf6989` và `open_aijobs_v1_ceea75a58f85`.

## Demo trên web

1. `make app`, mở `http://127.0.0.1:8000/`.
2. **Xu hướng & kỹ năng**: chọn SO2024 hoặc tin Việt Nam. Năm biểu đồ Matplotlib/Seaborn dùng train, tách biểu đồ quan sát khỏi dự đoán. Công nghệ đã sử dụng trong khảo sát không được gọi là nhu cầu tuyển dụng.
3. **So sánh mô hình**: chọn đúng bài toán và đơn vị để xem Ridge/RF/baseline với MAE, RMSE, R².
4. **Dự đoán & tư vấn**: chọn khảo sát quốc tế, vai trò, quốc gia, WorkExp và kỹ năng. Xem hai dự đoán, MAE test lịch sử và kỹ năng có ít nhất 5 mẫu train cùng vai trò. Chênh lệch dự đoán khi thêm kỹ năng không chứng minh tăng thu nhập thực tế.
5. **Phân tích file**: chọn ngữ cảnh, tải CSV/XLSX/JSON, ghép `role`, `country`, `experience_years`, `skills`. Nhãn đối chiếu tùy chọn `salary_annual_usd` (số USD/năm) hoặc cột số được xác nhận USD/năm. Không ghép nhãn VND/tháng vào nhánh này. Vai trò/quốc gia chưa có trong train được báo lỗi theo dòng.
6. Chạy phân tích, kiểm tra biểu đồ/bảng lỗi/metric, tải CSV/XLSX/JSON/PNG hoặc ZIP có manifest/checksum. Bản trùng không đếm lại trong biểu đồ/metric. Metric trên file nhập không phải test độc lập. Nút demo 48 dòng và file mẫu 12 dòng lấy từ **train**, chỉ kiểm chứng chức năng.

Gemma vẫn được tích hợp trong ngữ cảnh tin Việt Nam khi bảng có mô tả, tối đa 20 mô tả/lượt. Adapter hiện tại dùng schema Việt Nam nên không chạy trên nhánh khảo sát quốc tế; chưa fine-tune Gemma với ba nguồn mới. Nhập file và suy luận không tự khởi động training.

## Lệnh tái lập và bàn giao

```bash
make open-data-fetch       # tải đúng revision; bỏ qua file đã đúng checksum
make open-data-verify      # chỉ kiểm tra raw, không tải hoặc train
make salary-global-train   # TRAIN thật SO2024; từ chối ghi đè run đã tồn tại
make salary-aijobs-train   # TRAIN thật benchmark AIJobs riêng
make global-research      # dựng lại biểu đồ train; không train
make submission-open-data # ZIP các split quốc tế + nguồn/giấy phép/checksum
make app                  # build giao diện và phục vụ suy luận local
```

Không chạy lại hai lệnh train trên experiment đã đóng băng để tìm kết quả đẹp hơn trên test. Vòng mới cần protocol/experiment riêng và holdout mới trước khi đánh giá. Giữ dữ liệu gốc trong `data/raw`; CSV lớn không đưa vào Git. Nhánh source có các split và model nén để demo; script fetch khôi phục raw từ nguồn pinned. `outputs/submission/open_datasets.zip` kèm `OPEN_MANIFEST.json` là gói dữ liệu quốc tế; gói `datasets.zip` cũ vẫn phục vụ mô hình Việt Nam/Gemma. Dữ liệu dẫn xuất SO2024 giữ nghĩa vụ ODbL/DbCL và ghi nguồn Stack Overflow.

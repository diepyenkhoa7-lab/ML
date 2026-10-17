# Hành trình xây dựng IT Career Insight

Tài liệu này ghi lại cách dự án đi từ đề bài đến bản demo hiện tại dựa trên README, CHANGELOG, tài liệu thiết kế, manifest, báo cáo và log đã lưu trong repository. Những câu mô tả có số liệu hoặc trạng thái đều trỏ tới bằng chứng tương ứng; phần diễn giải được ghi như diễn giải, không xem là một thử nghiệm đã chạy.

## 1. Đề bài và hướng giải quyết

Đề tài là phân tích thị trường việc làm CNTT và dự đoán lương lập trình viên bằng Python. Dự án tách thành hai bài toán:

* Python/scikit-learn dùng các trường có cấu trúc (`experience_years`, `role`, `level`, `location`, `skills`) để hồi quy lương.
* Gemma 4 E4B IT, chuyển sang MLX 4-bit và fine-tune bằng LoRA, đọc mô tả tin tuyển dụng để trích xuất JSON có schema cố định.

Gemma không trực tiếp hồi quy lương. Lương Gemma đọc được được giữ như trường trích xuất và không dùng để tính MAE của mô hình lương. Cách tách này phù hợp với vai trò của từng mô hình: hồi quy cần một bộ feature và nhãn số ổn định, còn mô hình ngôn ngữ xử lý văn bản không cấu trúc. Đây là quyết định kiến trúc được mô tả trong `README.md`, `docs/APP_IMPLEMENTATION_PLAN.md` và `docs/DATASET.md`.

## 2. Nguồn dữ liệu và làm sạch

Bốn nguồn được catalog trong `configs/data_sources.json` và `docs/DATA_SOURCES.md`: file Vietnam IT Job Posts do người dùng cung cấp, VietJobs 2025, Stack Overflow Developer Survey 2025 và DataForge 08/2026. Các nguồn có ý nghĩa khác nhau: lương chào tuyển VND/tháng, tổng thu nhập khảo sát USD/năm hoặc lương quốc tế theo nhiều đơn vị. Vì vậy dự án giữ loại nhãn, tiền tệ và kỳ lương riêng, không gộp số liệu khác bản chất vào một cột.

Báo cáo làm sạch (`outputs/data_quality/cleaning/REPORT.md`) ghi nhận 498.362 dòng đầu vào từ bốn nguồn. Quy trình giữ raw, chuẩn hóa tên trường, phân tích chuỗi lương và đưa những trường hợp không chắc chắn vào review/cách ly. Một số khó khăn có bằng chứng cụ thể:

* File người dùng có 3.200 dòng lịch sử cần xác minh xuất xứ, nhiều dòng thiếu kỳ lương, ký hiệu tiền tệ không rõ và 30 URL trùng.
* VietJobs có các cột số bị mất phần thập phân so với chuỗi lương ở một số dòng.
* DataForge có nhiều currency/period và không có số năm kinh nghiệm dạng số.
* Stack Overflow là khảo sát thu nhập, không phải dữ liệu tin tuyển dụng.

Do đó dự án không tự đoán tỷ giá, không biến “thỏa thuận” thành 0, không suy số năm từ seniority và không dùng các dấu hiệu nguồn chưa xác minh để kết luận xu hướng. Những quy tắc này nằm trong `docs/DATA_CLEANING.md` và `docs/DATA_SOURCES.md`; chúng là biện pháp xử lý đã ghi nhận, không phải giả định về dữ liệu.

## 3. Rà soát nhãn, silver label và đóng băng nhóm

Sau làm sạch, nhãn số được rà soát theo nguồn, đơn vị, vai trò và các trường hợp mâu thuẫn. Báo cáo `outputs/label_review/v1.0.1/REPORT.md` ghi nhận 33.539 nhãn ứng viên, giữ 33.133 dòng, cách ly 402 và bỏ 4 bản trùng cùng danh tính/nhãn. Nhãn này vẫn là **silver label**: có quyết định đọc trường được lưu lại nhưng chưa phải nhãn gold được nhà tuyển dụng hoặc nhóm độc lập xác nhận.

Bộ chính là `vn_developer`, gồm 176 mẫu từ 175 nhóm: 123 train, 25 validation và 28 test. Việc chia dùng `group_id`/URL/hash/nội dung/chức danh/địa điểm để giữ các biến thể cùng tin trong một nhóm, seed 42 và manifest/checksum. Báo cáo xác nhận không phát hiện record hoặc group xuất hiện ở nhiều tập, nhưng cũng ghi rõ chưa đảm bảo bắt được mọi tin gần trùng qua các nguồn thiếu URL hoặc mô tả.

“Freeze” có ý nghĩa thực tế: sau khi v1.0.1 được chốt, các tham số preprocessing/model phải fit trên train; validation dùng chọn mô hình; test chỉ mở sau khi lựa chọn xong. ID, source, group và row index không được đưa vào feature. Cấu hình và assignments nằm trong `configs/salary.yaml`, `data/splits/v1.0.1/vn_developer/` và manifest đi kèm.

## 4. EDA và các mô hình lương

Notebook `notebooks/01_eda.ipynb` tạo các biểu đồ phân phối lương, lương theo vai trò/địa điểm/kinh nghiệm và nhu cầu kỹ năng trên train. Notebook `notebooks/02_salary_models.ipynb` huấn luyện median baseline, Ridge và Random Forest; preprocessing được fit trên train rồi áp dụng cho validation/test. Run thành công được lưu ở `outputs/training_logs/salary_20261017T094556Z/run.json` và notebook thực thi liên quan.

Kết quả đã chốt trong `outputs/metrics/salary_bd9af2fa002caae8/REPORT.md`:

| Mô hình | Test MAE (triệu VND/tháng) | Test RMSE | Test R² |
|---|---:|---:|---:|
| Median baseline | 8,921 | 14,339 | -0,033 |
| Ridge | 7,074 | 9,603 | 0,537 |
| Random Forest | 6,656 | 10,517 | 0,444 |

Random Forest được chọn bằng MAE trên validation, rồi test được dùng một lần để báo cáo cuối. Không dùng test để chọn lại mô hình hoặc tham số. Vì test chỉ có 28 mẫu, nhãn còn là silver và chưa có kiểm thử theo thời gian, các số trên chỉ mô tả snapshot đã đóng băng; chúng chưa chứng minh tổng quát cho toàn thị trường. Hệ số Ridge và gợi ý kỹ năng trong ứng dụng được hiểu là quan hệ có điều kiện, không phải tác động nhân quả.

## 5. Gemma, LoRA và lựa chọn adapter

Gemma gốc Google được kiểm tra revision/checksum; bản MLX text-only 4-bit được chuẩn bị cho Apple Silicon. JSONL silver có 364 train, 72 validation và 82 test, tương ứng 122/25/28 tin nguồn với các biến thể bỏ trường. Split và nhóm kế thừa bộ lương; prompt trùng và biến thể không đủ bằng chứng bị loại. Các manifest và checksum nằm trong `outputs/gemma_preparation/`, `outputs/label_review/` và thư mục model.

Protocol full dùng LoRA trên 4 lớp cuối, rank 8, batch 1, context 1024, mask prompt. Lựa chọn adapter được khóa theo validation trước khi mở test. CHANGELOG ghi nhận baseline full và ba continuation thật ở learning rate 5e-5, 2e-5 và 1e-5; lượt cuối giảm điểm nên bị loại. Adapter `20261017T105728Z` được chọn bằng validation. `outputs/metrics/gemma_tuning/FINAL_REPORT.md` ghi:

* Validation: JSON 100%, schema 95,83%, accuracy trung bình 8 trường 93,75%, Skill micro F1 93,76%.
* Test sau khi khóa lựa chọn: JSON 100%, schema 95,12%, accuracy 93,90%, Skill micro F1 91,85%.
* Skills exact chỉ 56,94% validation và 54,88% test; mục tiêu schema 98%/accuracy 95% chưa đạt.

Điểm cần phân biệt: loss trong log chỉ là loss huấn luyện, không phải accuracy trích xuất. Test không dùng để train tiếp. `make gemma-infer-adapter` chỉ suy luận và mặc định nạp adapter đã chọn; API ứng dụng không có endpoint train. Đây là cách xác nhận train và inference là hai luồng khác nhau.

## 6. Ứng dụng upload đến kết quả

Ứng dụng local dùng Vue 3 ở frontend và FastAPI ở backend. Luồng đã triển khai là:

`upload CSV/XLSX/JSON → preview và mapping cột → normalize → Gemma trích xuất nếu bật → predict bằng RF/Ridge đã lưu → metric/charts → export CSV/XLSX/JSON/PNG/ZIP`.

Gemma chỉ điền trường thiếu, kiểm tra context/schema và lưu raw output; nó không ghi đè trường người dùng đã cung cấp và không dùng lương trích xuất làm nhãn metric. Các giới hạn vận hành được ghi trong `docs/APP_RUNBOOK.md` và `docs/APP_IMPLEMENTATION_PLAN.md`: file 10 MiB, tối đa 2.000 dòng/100 cột, tối đa 20 mô tả mỗi lượt; ứng dụng bind `127.0.0.1`, một worker, một người dùng.

`outputs/app_verification/REPORT.md` ghi nhận 40 unit/integration tests, API smoke trên server thật, một chuỗi extraction → RF, kiểm tra browser desktop/mobile, download và tư vấn. Ba screenshot thật và manifest/checksum export được lưu trong `outputs/app_verification/`. Đây là kiểm chứng local của demo; chưa phải deployment public, authentication, load test hay bằng chứng mọi loại bảng người dùng đều hoạt động.

## 7. Provenance, log và nhánh source

Mỗi giai đoạn giữ artifact theo run hoặc version: cleaning report, label manifest, split assignments, pipeline joblib, metrics/predictions, Gemma config/console/loss/checksum và app verification. `outputs/source_publication/manifest.json` mô tả danh sách source công bố. Raw dataset lớn, cache, base weights và checkpoint trung gian được giữ ngoài nhánh source gọn; lý do là CSV lớn vượt giới hạn Git thông thường và trọng số không phù hợp đưa vào Git. README ghi rõ nhánh bàn giao `publish/salary-gemma-prep` giữ source, notebook, CSV/split/JSONL cần thiết, metric và log được chọn lọc.

Lịch sử Git cho thấy các mốc chính: chuẩn bị split và salary ngày 17/10; trial Gemma, full epoch và tuning validation; sau đó triển khai ứng dụng upload-to-prediction. Đây là bằng chứng lịch sử của repository, còn trạng thái hiện tại phải đọc từ artifact và working tree khi nghiệm thu.

## 8. Khó khăn đã gặp và cách xử lý có bằng chứng

Các khó khăn được ghi nhận trong tài liệu/log gồm provenance không đầy đủ của file người dùng, dữ liệu lương khác tiền tệ/kỳ, nhãn và biến thể trùng, nguy cơ leakage qua group, CSV lớn, và sự khác nhau giữa train Gemma với inference Gemma. Cách xử lý tương ứng là giữ raw và manifest, tách nhãn theo loại, review/cách ly, group split đóng băng, publication manifest/nhánh source gọn, và tách lệnh `make gemma-adapter` với `make gemma-infer-adapter`.

Không có bằng chứng trong các tài liệu đã đọc để kết luận thêm về các thử nghiệm chưa ghi log. Vì vậy các mục như nhãn gold, holdout mới, kiểm thử theo thời gian, deployment public và đánh giá trên dữ liệu người dùng mới được xem là việc còn lại, không mô tả như đã hoàn thành.

## 9. Trạng thái và hướng tiếp theo

Bản hiện tại đã có snapshot dữ liệu/nhãn/split, kết quả Ridge/RF, adapter Gemma được chọn bằng validation, ứng dụng local và bằng chứng kiểm thử tương ứng. Những giới hạn còn mở được README và báo cáo cuối nêu rõ: test lương 28 mẫu, silver labels, Gemma skills còn yếu, nguồn một số bộ chưa đủ provenance, và demo chưa public.

Nếu mở vòng nghiên cứu tiếp theo, tài liệu hiện hành đề xuất duyệt nhãn gold, thêm tin độc lập và tạo holdout mới trước khi đánh giá; không dùng lại test đã mở làm validation. Các bước đó chưa được tính là kết quả của phiên bản này.

## 10. Mốc audit và nguồn dữ liệu mới ngày 18/10/2026

Commit local `344d108` đã ghi nhận một vòng audit kiến trúc ứng dụng với 3 lỗi mức high và 5 lỗi mức medium. Báo cáo `outputs/architecture_audit/2026-10-18/REPORT.md` mô tả các biện pháp đã kiểm chứng: hợp đồng batch Gemma theo từng dòng, snapshot/checksum và provenance gắn với lần chạy, hàng đợi tối đa 2 job, cô lập state JSON hỏng, tái tạo tư vấn kỹ năng từ train + Ridge đã xác minh, revision fence cho UI, file lock GPU và parser/schema nghiêm ngặt. Bằng chứng là 55 test, Ruff 42 file, Prettier/build, API CSV/XLSX/JSON và một mẫu Gemma suy luận GPU thật → RF; ảnh web Gemma nằm tại `outputs/architecture_audit/2026-10-18/gemma_web.png`.

Audit này chỉ xác nhận cấu trúc, provenance và luồng suy luận. Báo cáo nói rõ không train lại, không chấm lại benchmark, không làm giảm MAE lịch sử; MAE 6,656 triệu/tháng trên 28 mẫu silver test vẫn là kết quả cũ. Vì vậy các thay đổi audit được ghi là đã kiểm chứng ở tầng ứng dụng, không được diễn giải thành cải thiện chất lượng mô hình.

Sau audit, người dùng yêu cầu tìm thêm dữ liệu và tiếp tục một vòng train lương để đối chiếu nguồn ITviec/TopDev. Nguồn mới đã tải và lưu cục bộ là Tinix Vietnam Job Description: 606.878 tin, revision `679c3a17347ff6ce769d9bf510c122a087493cf6`, giấy phép được dataset card ghi là CC BY-NC 4.0. Manifest, checksum và README nằm ở `data/raw/tinixai_2026/`; profile nghiên cứu nằm ở `outputs/research/2026-10-18/`. Hiện đang rà soát label period, censored salary và duplicate. Chưa train vòng mới, chưa có metric mới và chưa có kết luận đối chiếu ITviec/TopDev; mọi trạng thái đó vẫn là đang thực hiện.

## 11. Protocol lương v2.1.0 và vòng train mới

Sau bước rà soát Tinix, protocol `configs/salary_v2_protocol.json` v2.1.0 được khóa trước khi train. Hai bản 2.0.0 và 2.0.1 chỉ là draft preparation để truy vết các lần sửa guard censored/period và holdout company cũ; chúng không được dùng như kết quả train. Bộ frozen tại `data/splits/v2.1.0/vn_developer/` tách strict train 79 mẫu khỏi weak train 1.078 mẫu (trọng số 0,3, monthly là ASSUMPTION và chỉ được dùng trong train), cùng validation 25 và test 30 có explicit-month. Split company-disjoint bao gồm cả weak data và loại các company đã có trong valid/test cũ v1.

Đã train thật 12 ứng viên (2 arms × 3 Ridge alpha × 3 Random Forest leaf). Kết quả và log nằm tại `outputs/metrics/salary_v2_042e3aa1a886/` và `outputs/training_logs/salary_v2_20261018/console.log`. Candidate được chọn là Ridge alpha=1 trên strict+weak 1.157 mẫu; RF tốt nhất dùng leaf=2. Validation MAE của Ridge là 5,424 triệu VND, RF là 6,207 triệu. Trên cùng new test 30 mẫu: Ridge MAE 4,433 triệu, RMSE 5,664 triệu, R² 0,54035 và 60% mẫu có sai số dưới 5 triệu; RF v2 MAE 5,737 triệu. So sánh với RF v1 trên cùng new test cho MAE 8,246 triệu, RMSE 10,508 triệu và R² âm; paired company bootstrap improvement 95% là 0,707–6,776 triệu. Các promotion gates cố định đã đạt và `configs/application.json` kích hoạt Ridge v2, trong khi v1 được giữ để rollback.

Các số v2 không được so trực tiếp với RF v1 MAE 6,656 triệu trên test cũ 28 mẫu như thể cùng một holdout. V2 có nhãn, split và mục tiêu khác; ý nghĩa của kết quả là so sánh đã định trước trong v2 và đối chiếu RF v1 trên new test. Gemma không train thêm và adapter được chọn trước đó không đổi.

## 12. Sanity check ITviec/TopDev và trạng thái hiện tại

Sanity check bên ngoài dùng các nhóm median VND chính thức từ ITviec 2025–2026 và dữ liệu TopDev 2024–2025 theo USD gross ratio-only. File tham chiếu nằm ở `data/references/`, kết quả ở `outputs/research/2026-10-18/external_sanity/`. Trên 13 nhóm ITviec có thể đối chiếu, median absolute aggregate gap được ghi là 8,18% cho mô hình cũ và 21,09% cho mô hình mới, với mô hình mới phần lớn thấp hơn. Đây không phải cùng population hoặc cùng label: survey là actual salary, còn mục tiêu hiện tại là midpoint của advertised salary range. Vì vậy chưa được kết luận là market alignment đã cải thiện, không fit các median tham chiếu để dự đoán từng cá nhân, và không dùng sanity check này để hiệu chỉnh model.

Ứng dụng hiện có API `market_reference`; web hiển thị nhóm tham chiếu ITviec cùng source URL nhưng không ép calibration. Luồng Gemma extraction → Ridge được chọn + RF comparison → charts/export đã được API real-GPU kiểm chứng trong `outputs/research/2026-10-18/api_smoke_v2.json`. Trạng thái hiện tại ghi nhận 63 tests đã pass và final checks vẫn đang diễn ra; chưa coi publication/push là hoàn tất. Heartbeat monitoring đã được tạo để theo dõi định kỳ, nhưng nhật ký này không suy diễn rằng agent chạy vô hạn khi phiên rảnh.

Mốc nghiệm thu trước publication tiếp tục xác nhận 63 tests sau khi tích hợp serving và `market_reference`, Ruff trên 48 file, Prettier/build và pip check. Bản source copy độc lập cũng chạy 63 tests, `npm ci` offline/build sạch và kiểm tra frozen v1/strict SFT; bằng chứng ở `outputs/research/2026-10-18/source_export.json`. Browser thật trên desktop 1440px và mobile 390px kiểm tra adapter/count, Ridge v2, ITviec và không tràn ngang; bằng chứng ở `outputs/research/2026-10-18/browser_checks.json`, `gemma_mobile.png` và `ridge_market_desktop.png`. Các kiểm tra ghi nhận ITviec 30,1M cho Backend 3–4 years riêng với model 26,5M, recommendations giữ support >=5 cùng role train, và lịch sử RF v1 vẫn hiển thị RF dù current model là Ridge.

Runbook `docs/SALARY_V2_RUNBOOK.md`, metrics report, `run.json` và `executed_training_source.py` đã lưu; README, data source và data card đã đồng bộ. Advisor role-support filter đã được kiểm tra theo đúng ngữ cảnh và không fit lại model mới. Publication/commit/push vẫn do parent thực hiện; heartbeat 15 phút là cơ chế theo dõi, không phải bằng chứng agent chạy liên tục.

## Tài liệu và bằng chứng chính

* `README.md`, `CHANGELOG.md`
* `docs/DATA_SOURCES.md`, `docs/DATA_CLEANING.md`, `docs/LABEL_REVIEW_AND_SPLITS.md`, `docs/DATASET.md`
* `docs/GEMMA_TUNING.md`, `docs/APP_IMPLEMENTATION_PLAN.md`, `docs/APP_RUNBOOK.md`
* `outputs/data_quality/cleaning/REPORT.md`
* `outputs/label_review/v1.0.1/REPORT.md`
* `outputs/metrics/salary_bd9af2fa002caae8/REPORT.md`
* `outputs/metrics/gemma_tuning/FINAL_REPORT.md`
* `outputs/app_verification/REPORT.md`
* `outputs/source_publication/manifest.json` và các run log dưới `outputs/training_logs/`

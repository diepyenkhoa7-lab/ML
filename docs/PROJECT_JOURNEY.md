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

Sanity check bên ngoài dùng các nhóm median VND chính thức từ ITviec 2025–2026 và dữ liệu TopDev 2024–2025 theo USD gross ratio-only. File tham chiếu nằm ở `data/references/`, kết quả ở `outputs/metrics/salary_v2_042e3aa1a886/external_sanity/`. Trên 13 nhóm ITviec có thể đối chiếu, median absolute aggregate gap được ghi là 8,18% cho mô hình cũ và 21,09% cho mô hình mới, với mô hình mới phần lớn thấp hơn. Đây không phải cùng population hoặc cùng label: survey là actual salary, còn mục tiêu hiện tại là midpoint của advertised salary range. Vì vậy chưa được kết luận là market alignment đã cải thiện, không fit các median tham chiếu để dự đoán từng cá nhân, và không dùng sanity check này để hiệu chỉnh model.

Ứng dụng hiện có API `market_reference`; web hiển thị nhóm tham chiếu ITviec cùng source URL nhưng không ép calibration. Luồng Gemma extraction → Ridge được chọn + RF comparison → charts/export đã được API real-GPU kiểm chứng trong `outputs/research/2026-10-18/api_smoke_v2.json`. Trạng thái hiện tại ghi nhận 63 tests đã pass và final checks vẫn đang diễn ra; chưa coi publication/push là hoàn tất. Heartbeat monitoring đã được tạo để theo dõi định kỳ, nhưng nhật ký này không suy diễn rằng agent chạy vô hạn khi phiên rảnh.

Mốc nghiệm thu trước publication tiếp tục xác nhận 63 tests sau khi tích hợp serving và `market_reference`, Ruff trên 48 file, Prettier/build và pip check. Bản source copy độc lập cũng chạy 63 tests, `npm ci` offline/build sạch và kiểm tra frozen v1/strict SFT; bằng chứng ở `outputs/research/2026-10-18/source_export.json`. Browser thật trên desktop 1440px và mobile 390px kiểm tra adapter/count, Ridge v2, ITviec và không tràn ngang; bằng chứng ở `outputs/research/2026-10-18/browser_checks.json`, `gemma_mobile.png` và `ridge_market_desktop.png`. Các kiểm tra ghi nhận ITviec 30,1M cho Backend 3–4 years riêng với model 26,5M, recommendations giữ support >=5 cùng role train, và lịch sử RF v1 vẫn hiển thị RF dù current model là Ridge.

Runbook `docs/SALARY_V2_RUNBOOK.md`, metrics report, `run.json` và `executed_training_source.py` đã lưu; README, data source và data card đã đồng bộ. Advisor role-support filter đã được kiểm tra theo đúng ngữ cảnh và không fit lại model mới. Publication/commit/push vẫn do parent thực hiện; heartbeat 15 phút là cơ chế theo dõi, không phải bằng chứng agent chạy liên tục.

## 13. Hoàn tất publication v2 và nghiên cứu vòng tiếp theo

Vòng v2 đã được commit trong feature commit `5211a73`; source gọn đã được push tới `publish/salary-gemma-prep` tại `769dbacaaa6f390fbfc884bde8670b48177d1eb7`. Các bằng chứng nghiệm thu trước đó vẫn giữ nguyên: 63 tests, Ruff 48 file, source export và luồng Gemma → Ridge qua browser/API thật đều đạt. Test v2 đã mở để báo cáo, nên không được dùng lại để tuning vòng sau.

Người dùng đã yêu cầu giảm ảnh hưởng của nhãn yếu, cải thiện đối chiếu thị trường và train/fine-tune tiếp. Vòng v3 hiện **chưa train**. Đang nghiên cứu dữ liệu cá nhân Stack Overflow 2026 từ file chính thức `survey_results_public.csv` tại pinned revision `6c646551e86ffcafca0ac04f1dfb17a2558ec23d`, cùng các nhãn MONTH lấy từ JSON-LD của tin tuyển dụng công khai. Đây là nghiên cứu nguồn và nhãn mới, chưa phải kết quả mô hình.

Hạn chế market sanity của v2 được giữ nguyên khi chuyển sang vòng mới: độ lệch nhóm median v2 khoảng 21,09% so với khoảng 8,18% của v1 không bị che giấu hoặc dùng để tuyên bố cải thiện. Cần tạo split/holdout mới và khóa protocol trước khi train; không dùng test v2 đã mở để điều chỉnh.

## 14. Vòng salary v3 và quyết định không promote

Nguồn Stack Overflow 2026 đã tải xong với 30.903 dòng, trong đó 68 phản hồi Việt Nam và chỉ 13 dòng có total compensation VND/năm hợp lệ cùng kinh nghiệm sau sanity. Nguồn này là khảo sát thu nhập cá nhân, không được trộn vào job salary. Manifest và kiểm tra chất lượng nằm ở `data/raw/stackoverflow_2026/manifest.json` và `outputs/research/v3/stackoverflow_2026_quality.json`.

Run `v3_b5ae152b9dd5` đã train thật 12 cấu hình CPU Ridge/Random Forest, gồm train recent-strict 55 mẫu và ablation older 60 mẫu, validation 18 mẫu, không có weak data. RF `min_leaf=2` trên recent-strict thắng validation với MAE 6,249 triệu và RMSE 10,236 triệu. Tuy nhiên trên cùng panel ITviec frozen của v2, gap v2 là 21,09456% còn v3 là 29,97975%, nên v3 thất bại promotion gate và không được promote; config v2 vẫn là cấu hình hoạt động.

Public Careerlink/TopDev có 45 tin đăng nhưng sau quality và seen-company filters chỉ còn 1 mẫu độc lập. Mẫu đơn này không đủ để xem như test đáng tin, không báo R²; confidence interval suy biến cũng không có ý nghĩa. Vì vậy kết quả này không được dùng để tuyên bố market alignment.

Hiện JobOKO công khai đã hoàn tất thu thập 44 tin; access audit ghi nhận `access_blocked=[]`. Audit access cũng ghi nhận CareerLink có 42 trang HTTP 200 chứa challenge, không có `JobPosting`, nên không dùng làm nhãn; collector đã được sửa để dừng ngay khi phát hiện HTML challenge. Chi tiết nằm ở `outputs/research/v3/access_audit.json`.

Đồng thời v3.1 đang sửa parser đã bỏ sót header rõ `VND MONTH` và loại các bản ghi có metadata experience mâu thuẫn body. Đây là sửa có căn cứ từ dữ liệu, không phải giả định rằng mọi salary đều theo tháng. v3.1 chưa train và các mốc thu thập còn đang chạy chưa được ghi là hoàn thành.

V3.1 sau đó đã train thật với 87 mẫu recent và 127 mẫu older (older trọng số 0,5), validation 28 mẫu và 12 cấu hình. RF `min_leaf=5` thắng validation với MAE 4,846979 triệu và RMSE 6,706734 triệu. JobOKO hoàn tất 44 tin, không bị access block; test mới chỉ có 3 mẫu từ 3 công ty, nên RF MAE 7,331 triệu so với incumbent 9,7145 triệu chỉ là thăm dò, không có CI và không phải benchmark đủ tin. Market gap v3.1 là 31,087866%, kém v2 21,094562%, nên không promote và ứng dụng giữ v2.

Có 214 annotation pending tại `data/annotation/v3.1.0/salary_review_queue.jsonl` với `gold=null`, chỉ dùng cho train data/annotation review. Bằng chứng chính nằm ở `docs/SALARY_V3_REVIEW.md`, `outputs/metrics/salary_v31_b089fdf458a5/` và `outputs/training_logs/salary_v31_20261018/run.json`; 71 tests và Ruff 56 cũng đã đạt. Source export, commit và push cho v3.1 chưa hoàn tất.

Sau đó bộ kiểm thử chốt đạt 72 tests, trong đó có test annotation xác nhận không chứa holdout; Ruff 56 và pip check cũng đạt. Mốc 71 tests ở đoạn trên được giữ nguyên vì đó là trạng thái trước khi bổ sung test. Source copy vẫn đang được kiểm tra và commit/push chưa xong.

Verification cuối trước publication đã đạt: `outputs/research/v3/source_export.json` xác nhận bản source copy 516 files, 72 tests, Ruff56, strict SFT, frozen v1 và clean offline npm ci/build; `outputs/research/v3/api_active_model.json` xác nhận HTTP 200 sau restart server với active model `Ridge v2_042e3aa1a886`. V3.1 không promote vì chỉ có 3 mẫu/3 công ty kiểm tra độc lập và market gap kém v2, không đạt gate đã khóa. Zero-assumed-period là đặc điểm nhãn của thử nghiệm; silver chưa phải gold là giới hạn chất lượng, không phải một điều kiện nghiệm thu được thêm sau khi chấm. Commit/push v3 vẫn chưa xong tại thời điểm ghi nhận này.

Release v3 source gọn sau đó đã push thành công lên `publish/salary-gemma-prep` tại commit `3b138e336745d5f9013e6c65ee8524df8090dd03` (feature commit `b8bc10dcc20d4604a3e36b734426583302c3577d`). Bản release gồm 519 files, khoảng 93 MB; source copy kiểm tra trước đó gồm 516 files/72 tests, ba file bổ sung là `source_export.json`, `api_active_model.json`, `gemma_unchanged.json`; nhật ký được cập nhật trong file đã có. Đây là mốc publication đã hoàn tất cho release v3.

## 15. Rà soát nhãn, fine-tune Gemma và nghiệm thu

Người dùng đã yêu cầu bắt đầu duyệt 214 nhãn pending và fine-tune Gemma. Khi bắt đầu, công việc mới ở bước kiểm tra corpus, schema và provenance; lúc đó chưa có run training mới hoặc metric mới. Các kết quả hoàn tất được ghi bên dưới; vẫn chưa có nhãn human gold được duyệt thêm. Nhãn AI rà soát vẫn được phân biệt với nhãn gold của con người. Test cũ tiếp tục được giữ nguyên, không mở lại để tuning. Các kết quả sau này chỉ được ghi khi có artifact, log hoặc report xác nhận.

Manifest `data/annotation/gemma_v2.0.0/manifest.json` hiện ghi 214 dòng đã review, gồm 201 accepted AI-reviewed silver và 13 rejected; `human_gold_rows=0`. Queue và split salary v3 cũ không bị sửa. Corpus Gemma reviewed v2.0.0 có 501 train (364 legacy replay + 137 mẫu mới), validation 31 mẫu mới và test 33 mẫu mới theo company-group, loại các company đã xuất hiện trong train cha.

Baseline trên validation mới được lưu tại `outputs/metrics/gemma_reviewed_v2/baseline_new_valid/metrics.json`: Skill F1 0,7272727, mean field accuracy 0,850806, JSON/schema 1,0. Đây là tập mới nên không so trực tiếp với 0,937 cũ như cùng validation. Protocol `configs/gemma_reviewed_protocol.json` đã khóa trước train, giới hạn tối đa một candidate và giữ test cũ không mở. Run thực `20261018T002705Z` đã hoàn tất 501/501 với learning rate 1e-5, LoRA 4 layers/rank 8/context 1024; `summary.json` ghi train loss cuối 0,006 và validation loss giảm từ 0,392 xuống 0,110 trên 31 mẫu validation mới; đây là loss, không phải accuracy hay extraction quality.

Đánh giá raw extraction đã hoàn tất trong `outputs/metrics/gemma_reviewed_v2/selection.json`. Trên validation mới, Skill F1 tăng 0,7272727 → 0,7849462, mean field 0,850806 → 0,858871, schema 1,0 → 0,935484 và score 0,843585 → 0,852016 (+0,008431). Trên legacy validation, F1 giảm 0,937562 → 0,902196, schema 0,958333 → 0,930556 và score 0,941685 → 0,922048; candidate fail cả ba legacy guards. JSON validity của cả hai tập là 1,0. Vì vậy `validation_passed=false`, giữ adapter web `20261017T105728Z`, không mở test 33 mẫu mới hay test cũ, và không train run trùng. Không suy diễn kết quả này thành cải thiện MAE lương.

Strict corpus 501/31/33 đạt; 79 tests và Ruff 59 file cũng đạt. Bản source copy tách biệt đã chạy lại 79 tests, kiểm tra frozen data, strict SFT mới/cũ, npm ci offline, Prettier và build frontend, tất cả exit 0; bằng chứng ở `outputs/metrics/gemma_reviewed_v2/source_export.json`. Báo cáo của vòng này ở `outputs/metrics/gemma_reviewed_v2/REPORT.md`; commit/push được xác nhận bằng lịch sử Git của nhánh source gọn.

## 16. Audit sửa tham chiếu nhãn Gemma v2.1.1

Audit các mẫu mới xác nhận một trường experience bị null và các skill ONNX/TensorRT/OpenVINO/BERT/DeepLearning bị bỏ sót. Scripts `refine_gemma_references.py` và `adjudicate_gemma_corrections.py` tạo diagnostic memory cho 137 train + 31 validation, không đụng test. Có 18 đề xuất, 17 được AI review chấp nhận (7 train, 10 validation), 1 bị parser bác bỏ; các quyết định đáng chú ý giữ 2 năm kinh nghiệm của TinixAI và giữ `AntDesignMobile` cụ thể.

`data/annotation/gemma_v2.1.1/` lưu manifest, adjudicated changes và cached diagnostic. v2.1.0 chỉ là draft audit đầu; builder snapshot/hash và old references/protocol/model/web/test được giữ. Cached prediction theo corrected reference cho F1 parent 0,805825 và candidate 0,857143. Đây là label-sensitivity diagnostic, không phải model improvement hay promotion; chưa tạo corpus/train mới và chưa mở test.

## 17. Corpus corrected v2.2.0 và run Gemma đang thực hiện

`scripts/prepare_gemma_corrected.py` đã tạo corpus `data/finetune_reviewed/v2.2.0` với 501/31/33 mẫu, giữ prompt và company split. Có 7 train và 10 validation label thay đổi; 33 test được rebuild bằng policy cố định suy ra từ train/validation, không dùng prediction/test để thêm alias, và chỉ 1 test label thay đổi. Đây là silver rule-based mù, chưa phải human review độc lập; test mới chưa được chấm model.

Protocol `configs/gemma_corrected_protocol.json` đã khóa: 501 mẫu, learning rate 2e-6, parent `105728Z`, một candidate trong vòng này, tối đa hai candidate tính cả vòng cũ trên 31 validation; old guards giữ nguyên và thêm guard experience không giảm. Run thật `20261018T051656Z` đang chạy ở session 54040; log tại `/private/tmp/gemma_corrected_training.log`, artifact tại `outputs/training_logs/gemma_20261018T051656Z/run.json`, validation loss ban đầu 0,343. Run chưa hoàn tất và chưa có metric mới; không ghi đây là hiệu quả hay promotion.

App worker đã thêm reuse exact duplicate text trong cùng request, đồng thời giữ index/hash/raw/error theo từng dòng; hai CPU tests đạt. GPU chưa kiểm chứng vì máy đang train.

Run corrected `20261018T051656Z` đã hoàn tất 501/501; validation loss giảm 0,343 → 0,183. Selection tại `outputs/metrics/gemma_corrected_v22/selection.json` không đạt: new Skill F1 0,805825 → 0,823529 nhưng score gain 0,004908 thấp hơn ngưỡng 0,005, experience giữ 0,709677; legacy F1 0,937562 → 0,919355, schema 0,958333 → 0,916667 và score 0,941685 → 0,920945. Không promote, không chấm test mới/cũ; đã hết hai candidate trên 31 validation.

Worker GPU duplicate test 3 cards/1 generation đạt 8,27 giây. CLI context 2048 đọc một source dài 1.211 tokens; lần đầu schema fail duplicate, retry tối đa một model call giữ raw attempts và schema đạt. Vẫn còn semantic errors generic functions và hallucinated Express/SQL; `app source_skill_evidence` đã thêm inventory literal từ mô tả để grounding, giữ raw Gemma và ưu tiên skills người dùng. 97 CPU tests đạt; GPU end-to-end grounding đang QA, chưa ghi là đạt. Availability probe dùng actual GPU lock cho eval/infer; frontend refresh metadata trước analyze và button kiểm tra lại GPU.

Demo provenance trước đó dùng v1 dù train v2 đã được sửa theo actual experiment. Server QA hiện ở session 96710 port 8000; source publication vòng này chưa xong.

QA cuối đã kiểm chứng browser JSON upload `data/examples/application_gemma_long_demo.json` → Gemma GPU context 2048 → source-grounded skill features → Ridge/RF → charts → download ZIP. Job `ad41c19476f642ce95b6e25dc7ce8004` có 3/3 dòng dự đoán, 1 trùng, 2 source và 0 nhãn thu nhập; ZIP tải thật qua UI tại `/Users/scara2906/Downloads/analysis.zip`, gồm 10 file đã verify hash. Evidence nằm ở `outputs/metrics/gemma_corrected_v22/serving_qa/`. Raw Gemma có Express implied và SQL từ MySQL nhưng không đưa vào features; literal MySQL được giữ. Unknown technology trong closed inventory có thể bị bỏ sót; chưa có MAE claim. 97 tests và Ruff đạt, docs serving/report đã đồng bộ. Publication final vẫn đang thực hiện; chưa có mẫu hoặc thông tin sinh viên cho báo cáo.

Bản source copy của mốc label audit đã vượt qua 84 tests, Ruff62, kiểm tra frozen/strict SFT và cài/build frontend offline; bằng chứng `data/annotation/gemma_v2.1.1/source_export.json`.

Mốc chuẩn bị corrected v2.2 cũng đã qua 89 tests/Ruff66 và source-copy install/build offline, bằng chứng `outputs/metrics/gemma_corrected_v22/source_export_preparation.json`. Nội dung kỹ thuật báo cáo ở `reports/BAO_CAO_NOI_DUNG.md` đã có; vẫn chưa phải báo cáo cá nhân đúng mẫu. Lượt train còn đang chạy, chưa có kết luận chất lượng.

Nghiệm thu source cuối đạt 97 tests, Ruff check/format70 file, frozen/strict SFT checks, npm ci offline, Prettier và production build từ bản copy tách biệt; bằng chứng `outputs/metrics/gemma_corrected_v22/source_export_final.json`. Commit/push được xác minh qua nhánh `publish/salary-gemma-prep`; báo cáo cá nhân còn chờ mẫu và thông tin sinh viên.

## 18. Bàn giao gói dữ liệu

Lệnh `make submission-data` đã tạo `outputs/submission/datasets.zip` gồm 42 file dữ liệu/provenance và MANIFEST, dung lượng 1.098.896 byte, SHA-256 `1726e1f2a0515f32ed30b48ffaca1d1456daada4d0fbad14ed71d0bd4e6dd6e3`. Gói đã được verify CRC, hash và số dòng theo `scripts/package_submission_data.py`; chi tiết trong `docs/DATASET_HANDOFF.md`, `outputs/submission/MANIFEST.json` và `outputs/submission/verification.json`.

Phạm vi gồm salary serving, Gemma SFT serving, corrected trial không đạt, review 214 dòng và provenance nguồn. Gói không bao gồm raw lớn, cache, trọng số model hoặc dữ liệu upload runtime. Việc tạo/kiểm tra gói không train mới và không cải thiện accuracy. Báo cáo cá nhân vẫn thiếu mẫu và thông tin sinh viên cần điền.

Bản copy tách biệt từ whitelist source đã tạo lại ZIP giống từng byte và vượt qua 97 unit tests; bằng chứng `outputs/submission/source_copy_verification.json`. Tạo lại local cho cùng SHA-256; thử sửa một thành viên ZIP bị bộ kiểm tra từ chối. Đây là kiểm chứng đóng gói, không phải đánh giá lại mô hình.

## 19. Demo nghề nghiệp và kịch bản báo cáo

Browser/API thật tại `localhost:8000` đã kiểm chứng hồ sơ Backend Junior, 3 năm, Hà Nội, Python/SQL: Ridge dự đoán 26.508.883 VND và RF 23.869.167 VND; median ITviec 30,1 triệu được hiển thị riêng. Gợi ý Rust ban đầu có chênh lệch +7.052.129 VND với 7 mẫu cùng role. Khi sửa kỹ năng, kết quả cũ được xóa; khi thêm Rust, dự đoán cập nhật 33,6 triệu/RF 26,1 triệu và Rust không còn được đề xuất lại.

Live API kiểm tra 8 roles đều phản hồi 200 với hai prediction dương; hồ sơ ML Engineer thử không có gợi ý vì thiếu bằng chứng đủ support. Accountant trả 422 và khu vực/kỹ năng chưa biết như Zig tạo warning. Bằng chứng nằm ở `outputs/app_verification/career_demo/live_api.json` và 4 ảnh JPEG thật. `docs/DEMO_SCRIPT.md` đã bổ sung kịch bản 7–10 phút; hai mô tả cũ trong app runbook/plan đã đồng bộ.

Đây là kiểm chứng UI/API và hành vi tư vấn, không phải train, thay model/nhãn hoặc claim MAE. Buổi báo cáo chưa được xác nhận; báo cáo cá nhân vẫn chờ mẫu và STT/tên/MSSV.

## 20. EDA salary v2 theo strict train

Notebook `notebooks/04_salary_v2_eda.ipynb` đã chạy 5 cell code và tạo 5 biểu đồ từ 79 mẫu strict train thuộc 69 nhóm công ty. Không trộn 1.078 weak labels vào các biểu đồ mô tả, cũng không dùng validation/test. Top demand là JavaScript 27, CSS 23, HTML 19, MySQL 17 và React 17; tương quan Pearson kinh nghiệm–lương là 0,3846. Các liên hệ kỹ năng Ridge trên scope 1.157 mẫu train gồm cả weak được ghi riêng và chỉ là quan hệ trong dữ liệu, không phải quan hệ nhân quả.

Source copy đã chạy lại toàn notebook; summary, bảng và hash 5 PNG giống nhau, 6 liên kết ảnh trong báo cáo resolve thành công (`outputs/eda/salary_v2_strict_train_042e3aa1a886/source_copy_verification.json`). Đây là EDA mô tả, không train, không đổi weights hay mở test; nhãn strict vẫn là silver. Báo cáo kỹ thuật có thêm các biểu đồ này và ảnh UI, nhưng báo cáo cá nhân vẫn thiếu mẫu và identity sinh viên.

## 21. Kiểm soát prediction ngoài miền giá trị

Người dùng đã loại báo cáo cá nhân khỏi phạm vi hiện tại. Khi kiểm tra hồ sơ ML Engineer Junior, 0 năm, Hà Nội, Python/scikit-learn/TensorFlow/Spark/Machine Learning, model Ridge thật trả `-210012.273` VND. Backend được sửa để coi prediction `<=0` hoặc nonfinite là invalid riêng dòng, giữ diagnostic riêng, không clamp/fallback, loại dòng đó khỏi charts/metrics, tiếp tục xử lý các dòng khác và cảnh báo coverage.

Hai test mới và full 99 tests cùng Ruff 71 đạt. Live API server mới trong `outputs/app_verification/prediction_domain/live_api.json` kiểm chứng 2 dòng: 1 predicted, 1 invalid, 0 labels; ZIP 9 file đã verify hash, job `5f57b51f901c4be9a3c8f1e444d8d48d`. Đây là sửa xử lý miền giá trị và bằng chứng serving, không train, không đổi weights/frozen metrics và không phải claim giảm MAE.

Bản xuất cuối của lượt sửa cũng giữ cảnh báo coverage trong report.md; job `e3be9a39b5594cec86d84380193d9ecc` xác minh checksum code đang chạy và 9 file trong ZIP. Source copy vượt 99 tests và tạo lại dataset ZIP giống từng byte; bằng chứng `outputs/app_verification/prediction_domain/source_copy_verification.json`.

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

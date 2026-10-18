# Các nguồn lương IT — kiểm tra ngày 17/10/2026

**Bổ sung ngày 18/10/2026:** SO2024, AIJobs và Level đã tải với revision/bytes/SHA trong `configs/open_salary_sources_20261018.json`. Xem [INTERNATIONAL_DATA.md](INTERNATIONAL_DATA.md) về vai trò từng nguồn, train thật, đơn vị và giấy phép. Không gộp thu nhập USD/năm với lương chào tuyển VND/tháng; ITviec đã bỏ khỏi tư vấn web và không dùng trong hai vòng train quốc tế mới.

Danh mục và phiên bản cố định ở `configs/data_sources.json`. File gốc được giữ
trong `data/raw/`, mỗi nguồn có `manifest.json` ghi URL hoặc đường dẫn đầu vào,
ngày nhận, số byte và SHA-256. Thống kê **đọc trực tiếp từ file** nằm trong
`outputs/data_quality/source_inventory.json`; các CSV lọc sơ bộ nằm ở
`data/processed/source_views/`.

## 1. File Vietnam IT Job Posts do người dùng cung cấp

- Bản gốc: `data/raw/user_vietnam_it_jobs/vietnam_it_job_posts.csv`.
- 6.779 dòng, 19 cột; có chức danh, công ty, lương dạng chuỗi, kinh nghiệm, kỹ năng,
  URL, nền tảng và các mốc thời gian.
- Nguồn tải bộ CSV và giấy phép: **chưa xác định**. Người dùng xác nhận không có link.
  URL từng tin trong file chưa chứng minh được tác giả và cách xây dựng cả bộ dữ liệu.
- `source_platform` gồm VietnamWorks, TopCV, CareerViet, ITviec, Ybox.
- Có 2.755 dòng ghi ngày đăng năm 2026, 2.256 dòng thiếu ngày đăng. Ngày đăng của
  toàn file trải từ 2018 đến 06/07/2026; đây là giá trị trong CSV, chưa được đối chiếu
  với lịch sử các trang tuyển dụng.

**Phát hiện cần rà soát:** 3.200 dòng có năm crawl 2018–2025, phân bố đúng 100 dòng
cho mỗi nền tảng TopCV/VietnamWorks/CareerViet/ITviec ở mỗi năm. Một số URL chứa mã
`hist201800001` hoặc ID có dạng năm + số thứ tự. Đây là dấu hiệu cần xác minh
nguồn gốc, chưa đủ căn cứ gọi là lịch sử thị trường thực. Không dùng khối này để
kết luận xu hướng tăng/giảm lương trước khi làm rõ cách tạo dữ liệu.

- Tập ngày đăng 2026: `user_vietnam_it_jobs_2026.csv` (2.755 dòng).
- Khối lịch sử cần xác minh: `user_vietnam_it_jobs_history_provenance_review.csv`
  (3.200 dòng); bản raw vẫn giữ đầy đủ.
- Có 30 URL trùng; phần lớn thiếu `requirements` (6.722 dòng).
- Có 2.107 dòng lương thỏa thuận/thương lượng; 14 chuỗi lương chứa đồng thời ký hiệu
  USD và thang đơn vị triệu/VND. Cần phân tích đơn vị trước khi tạo nhãn.
- Không biến lương thỏa thuận thành 0; không tự suy ra năm kinh nghiệm từ ô trống;
  không dựng mô tả tuyển dụng giả rồi coi là dữ liệu gốc để fine-tune Gemma.

## 2. DataForge: snapshot quốc tế 01/08/2026

Nguồn chính: [DataForge](https://data.zalize.com/datasets/tech-job-postings-salary-dataset),
[Hugging Face](https://huggingface.co/datasets/zalizedata/tech-job-postings-salary-dataset).
Snapshot trong catalog mới nhất kiểm tra được là **2026-08-01**;
repo HF cập nhật 14/08/2026. Không đồng nhất ngày cập nhật repo với ngày của tin.

- Gói đầy đủ công khai: `data/raw/dataforge_2026_08/jobs-tier1-L-2026-08-01.zip`.
- CSV: `data/raw/dataforge_2026_08/extracted/data/jobs.csv`.
- Có README, data dictionary, datasheet, license và Parquet đi kèm.
- Đã kiểm tra 394.300 dòng × 22 cột; checksum ZIP khớp công bố, kiểm tra CRC đạt.
- Có 107.030 dòng với hai đầu lương dương và đúng thứ tự. Tập lọc sơ bộ theo
  chức danh phần mềm + khoảng lương dương có 13.268 dòng; regex có thể còn lẫn vai trò,
  cần rà soát trước huấn luyện.
- `salary_currency` và `salary_period` đa dạng: năm/tháng/tuần/ngày/giờ. Không gộp
  trực tiếp vào một cột lương. Không quy đổi tiền tệ khi chưa có nguồn/ngày tỷ giá.
- `skills` trong CSV phân cách bằng `|`; trong Parquet là list.
- Bản công khai không có mô tả toàn văn và không có số năm kinh nghiệm dạng số.
  Phù hợp phân tích tin tuyển dụng/kỹ năng; không đủ để tạo cặp trích xuất toàn văn
  cho Gemma, hoặc mô hình đòi hỏi feature kinh nghiệm thật.
- Đây là snapshot các tin được thu thập, không phải thống kê toàn thị trường.
  `posted_at` có thể là ngày first-seen; số tin theo ngày trong một snapshot chịu
  ảnh hưởng của các tin còn tồn tại. Muốn kết luận xu hướng phải có thiết kế lấy mẫu
  và nhiều kỳ thu thập phù hợp.

**Điểm chưa thống nhất về điều khoản:** trang HF/site ghi CC BY-NC 4.0 cho lớp dữ
liệu biên tập, nhưng `extracted/LICENSE.md` chọn Tier 1 Internal Analytics và tách
quyền ML sang Tier 2. Đã giữ cả hai tài liệu; chưa coi điều kiện huấn luyện/phân phối
của nguồn này là được xác nhận. Ghi nguồn DataForge và backlink khi sử dụng.

## 3. VietJobs: tin tuyển dụng Việt Nam, công bố 2026

Nguồn tác giả: [VinNLP/VietJobs](https://github.com/VinNLP/VietJobs),
[dataset HF](https://huggingface.co/datasets/dinhieufam/VietJobs),
[bài báo](https://arxiv.org/abs/2603.05262).

- Raw: `data/raw/vietjobs_2025/VietJobs.csv`.
- Repo công bố phát hành 02/2026; commit dataset HF ngày 02/03/2026; bài báo ngày
  05/03/2026. **Dữ liệu là năm 2025**, không phải lương thị trường 2026.
- README nêu 07–10/2025, còn mục 3.1 bài báo nêu tháng 07/2025 trong một tuần.
  CSV không có ngày đăng từng tin, nên chưa giải quyết được khác biệt này.
- Có ngành nghề, chức danh, địa phương, kỹ năng, kinh nghiệm, mô tả, yêu cầu và
  lương. Đây là dữ liệu nhiều ngành, cần lọc nhóm CNTT trước khi xây mô hình ngành IT.
- Các trường có hỗ trợ trích xuất bằng GPT-4o/Gemini; cần kiểm tra nhãn trước khi
  dùng làm tập fine-tune chuẩn. Không coi toàn bộ trường được cấu trúc hóa là gold label.
- Đơn vị lương theo bài báo là **triệu VND/tháng**; không nhầm thành số đồng.
  Khi rà soát mẫu đã thấy chuỗi `9.4 - 12.0 triệu` đi cùng `salary_min=9`:
  số thập phân có thể đã mất trong cột số. Báo cáo inventory đếm các khoảng không
  khớp chuỗi gốc; không tự tin dùng cột số làm nhãn khi chưa xử lý vấn đề này.
- Mẫu lọc: `vietjobs_it_candidates.csv`, giữ cột nguồn và chỉ số dòng để truy vết.
- Đếm trực tiếp: 48.092 dòng gốc, 1.906 tin CNTT; 1.144 tin CNTT có hai đầu lương
  dương. Toàn bộ file có 385 dòng trùng hoàn toàn và 1.231 khoảng lương dạng chuỗi
  không khớp cột số theo kiểm tra pattern chặt; cần sửa trước khi chọn nhãn.
- Repo code ghi MIT; HF không có data card/giấy phép dataset riêng. Giữ ghi chú này
  khi bàn giao, không tự coi giấy phép code là xác nhận đầy đủ cho dữ liệu thu thập.

## 4. Stack Overflow Developer Survey 2025

Nguồn chính: [kho dữ liệu chính thức](https://github.com/StackExchange/Survey/tree/main/packages/archive/2025),
[kết quả khảo sát](https://survey.stackoverflow.co/2025/).

- Raw: `data/raw/stackoverflow_2025/survey_results_public.csv`.
- Có schema và README nguồn; CSV được đối chiếu SHA-256 và kích thước từ Git LFS
  của repo chính thức.
- Dùng `ConvertedCompYearly` làm thu nhập đã quy đổi **USD/năm** theo nhà công bố.
  Đây là total compensation tự khai, không phải lương chào tuyển hoặc lương cơ bản
  VND/tháng. `CompTotal` dùng đồng tiền ở `Currency`.
- Có `WorkExp`, vai trò, quốc gia, công nghệ đã dùng. `YearsCode` là số năm lập trình,
  không tự thay thế số năm kinh nghiệm nghề nghiệp.
- Tập có thu nhập dương xuất vào `stackoverflow_2025_salary_candidates.csv`.
  Chưa cắt ngoại lệ; chỉ chọn ngưỡng bằng train/validation, không dùng test để lọc.
- Đếm từ raw: 49.191 dòng; 23.947 có thu nhập quy đổi dương, trong đó 23.469 có
  `WorkExp`. Việt Nam có 145 phản hồi nhưng chỉ 57 có thu nhập quy đổi dương.
- Khảo sát kỹ năng người trả lời không đại diện trực tiếp cho nhu cầu tuyển dụng.
- Data: ODbL 1.0, nội dung từng ô: DbCL 1.0; giữ ghi công Stack Exchange/Stack Overflow.

Kết quả khảo sát 2026 đã có trên [trang chính thức](https://survey.stackoverflow.co/2026),
nhưng ngày 17/10/2026 đường dẫn CSV raw chính thức được kiểm tra trả HTTP 404.
Vì vậy không ghi nhãn bộ CSV 2025 tải về thành dữ liệu 2026.

## Dùng các nguồn cho đề tài

Giữ các bài toán riêng theo nguồn, loại nhãn, quốc gia và thời kỳ. Không nối tất cả
thành một bảng nhãn lương rồi train trực tiếp: lương chào tuyển trung điểm khác thu
nhập khảo sát; tiền tệ/kỳ lương khác nhau; một số nhãn hoặc xuất xứ còn cần rà soát.
Đây là các **tập ứng viên để làm sạch**, chưa phải `jobs_clean.csv` cuối cùng.

`source_views` chỉ lọc, giữ số tiền và trường gốc; không dùng như kết quả nghiên cứu
đã kiểm định. Khi chia train/valid/test, nhóm theo URL/hash/tin gần trùng để tránh
lọt cùng một tin sang nhiều tập. Không đưa cột lương hoặc mô tả chứa lương vào
features của mô hình dự đoán tiền lương.

Tải lại bằng `make data-fetch`; lập hồ sơ và tái xuất các tập ứng viên bằng
`make data-profile`. Với file do người dùng cung cấp, lệnh fetch cần bản gốc ở
đường dẫn đã ghi nếu chưa có bản raw trong dự án.

Một số CSV gốc lớn hơn giới hạn file GitHub thông thường. Khi đưa dự án lên Git,
dùng Git LFS hoặc bàn giao URL nguồn đã cố định commit + checksum + script tải lại;
không bỏ qua dataset bàn giao mà không có cách tải tái lập.

## Bổ sung 18/10/2026: TiniX / CareerPathKG

[TiniX Vietnamese Job Descriptions](https://huggingface.co/datasets/tinixai/vietnamese-job-descriptions), revision `679c3a17347ff6ce769d9bf510c122a087493cf6`: 606.878 tin nhiều ngành năm2022–2026, parquet khoảng280MiB, CC-BY-NC-4.0 theo dataset card. Ghi công Le et al., CareerPathKG, EACL Industry2026. Có title/company/salary/requirements/year nhưng không có URL/ngày chi tiết cho từng tin; không tuyên bố mọi tin đều mới ở thời điểm tải.

Chỉ dùng subset lập trình viên2025–2026 cho nghiên cứu salaryv2.1.0. Explicit-month holdout tách riêng khỏi nhãn train thiếu kỳ (giả định tháng, weight0,3). Raw/checksum tại `data/raw/tinixai_2026/`, frozen dẫn xuất và protocol tại `data/splits/v2.1.0/` và `configs/salary_v2_protocol.json`. Không trộn báo cáo ITviec/TopDev dạng trung vị nhóm thành nhãn cá nhân; tham chiếu riêng ở `data/references/`.

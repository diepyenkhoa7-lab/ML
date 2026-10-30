# Nghiên cứu chứng cứ nhãn lương mới — 29/10/2026

Kiểm duyệt sau nghiên cứu: LABEL_ADJUDICATION-2026-10-29.md ghi hai nhãn chấp nhận vào file riêng, 17 cần review, 7 bị loại trong 26 trường hợp. Pipeline canonical và gate training chưa đổi. Kết luận 0 ở phần nghiên cứu bên dưới là trạng thái trước kiểm duyệt; không dùng nó phủ nhận hai nhãn vừa được chấp nhận.

Cập nhật sau báo cáo: người dùng đã chọn giữ nhóm unknown gross/net riêng (ADR 0006), không trộn với gross/net đã xác nhận. Main kiểm lại checksum và số record của cả hai CSV mới, cùng câu tháng của Jaxtina trong raw được duyệt. Quyết định basis này không tự nhận các ứng viên thành canonical hoặc mở train; các khoảng trống nguồn/nhãn và policy khác bên dưới vẫn cần xử lý.

Kiểm tra trực tiếp ngày 29/10/2026, kết thúc khoảng 20:50 ICT. Phạm vi: nguồn mới trong catalog, raw mới và nguồn công khai bên ngoài. Chỉ ghi báo cáo này; không sửa catalog, dataset, gate, tracker, code hoặc model. Không đọc/dùng legacy `career_ai`, `career_web`, dataset hay artifact cũ. Công việc độc lập với nhánh sửa lỗi đang chạy song song.

## Kết quả và trạng thái gate

**Gate ML vẫn blocked; 0 nhãn được chấp nhận vào canonical trong lượt này.** Có chứng cứ mới đáng review, nên không diễn giải con số 0 thành “không có dòng nào chứa kỳ lương”.

- Raw `jobs-2023`: tìm thấy một tin phần mềm có khoảng lương, đồng và tháng ngay trong cùng dòng: Jaxtina, ID `35BB4811`. Hai tin YODY Data có kỳ thu nhập tháng và tiền tệ cùng dòng nhưng cần quyết định basis. Chưa cập nhật trạng thái chấp nhận.
- Hai trang nhà tuyển dụng mở trực tiếp công bố khoảng VND/month. Đây là hai tin riêng được kiểm chứng nội dung, chưa có giấy phép phân phối dataset, chưa xác nhận gross/net hoặc ngày đăng.
- CSV mới `SonPhatTranDeveloper/IT-Job-Posting`: đọc đủ **3.101 dòng**; bảng tuyển chọn bên dưới có **10 URL tin khác nhau** có khoảng lương và tiền tệ/kỳ rõ trong description. Một tin được đối chiếu lại trên trang ITviec. Đây là số ứng viên đã tuyển chọn, **không phải tổng số nhãn hợp lệ của dataset**; quyền phân phối chưa rõ.
- CSV mới VietJobs: đọc đủ **48.092 dòng**; có **1.906** dòng category IT của bên phát hành, **1.903** trong số đó có country `Việt Nam`. Không có cột định danh/URL tin hoặc công ty/ngày đăng; chưa đủ truy vết về tin gốc. Không nhận `salary_min/max/avg` làm target đã kiểm chứng.

Không cộng những nhóm trên thành số tin độc lập toàn bộ: chưa thực hiện entity/repost/leakage audit giữa các nguồn. Không huấn luyện, không tạo metric, không đặt ngưỡng readiness mới. ADR 0002/0003/0005 và M01 vẫn áp dụng: có một vài nhãn có chứng cứ không tự mở gate #42.

## 1. Chứng cứ trong raw mới đang được phép đọc

Đọc bằng `csv.DictReader`, UTF-8-SIG; số dòng dưới đây là **record 1-based sau header**, không phải số dòng vật lý vì CSV có trường nhiều dòng. HTML được bỏ tag và unescape để xem, không thay raw.

| Nguồn | Revision | Record đã đọc | SHA-256 CSV kiểm lại | Giấy phép bên phát hành, kiểm lại qua API chính chủ |
| --- | --- | ---: | --- | --- |
| jobs-2023 | Kaggle v2 | 2.056 | `8014c43996075240d309a137f11436c1e3af218afa7e823e83d67ac6f7c85a3c` | CC0: Public Domain |
| jobs-2026 | Kaggle v1 | 1.550 | `e78ff2b6ed521ad894a70271a3254fcf434813916fdade4f7d449bc4fdf34ef9` | Attribution 4.0 International (CC BY 4.0) |

Metadata được tải mới không cần tài khoản:

- [Kaggle metadata jobs-2023](https://www.kaggle.com/api/v1/datasets/view/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version): `currentVersionNumber=2`, `licenseName=CC0: Public Domain`; SHA-256 JSON `326fad5c445b55fb2409b66e5def2a5ed2ef98595350b7076df760d227dd7402`.
- [Kaggle metadata jobs-2026](https://www.kaggle.com/api/v1/datasets/view/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026): `currentVersionNumber=1`, `licenseName=Attribution 4.0 International (CC BY 4.0)`; SHA-256 JSON `d09724e65f7dbbcae057e0828546e8c38c022dcc836d139ae73bfb43b2ec12bf`.

Đây là khai báo giấy phép của người phát hành dữ liệu, không chứng minh quyền sở hữu toàn bộ nội dung của CareerBuilder/TopCV. CC BY cần ghi tác giả, nguồn, giấy phép và phần thay đổi khi bàn giao. ZIP không được tải lại trong lượt này; hash ZIP trong SOURCE_RECHECK chỉ là tham chiếu, không được gọi là kiểm ZIP mới.

### Các dòng cần review trước

| Record / ID | Tin gốc và dữ liệu cùng dòng | Chứng cứ kỳ, trường `job_requirements` | Kết luận nghiên cứu |
| --- | --- | --- | --- |
| 1479 / `35BB4811` | [Senior Developer — Jaxtina](https://careerbuilder.vn/vi/tim-viec-lam/senior-developer.35BB4811.html); `salary=Lương: 25 Tr - 45 Tr VND`; Hà Nội; announcement_date `19-02-2023` | `Mức lương: Tù 25.000.000đ - 45.000.000đ/tháng` | Chứng cứ trực tiếp trong snapshot mới: bounded, VND/MONTH, hai đầu khớp. Trung điểm toán học 35.000.000 VND/tháng chỉ là ứng viên target. JD có React Native/Android/iOS, ReactJs và backend: cần quyết định Mobile/Fullstack theo policy, giữ một entity; gross/net chưa xác định. |
| 975 / `35BB58E5` | [Data Analyst — YODY](https://careerbuilder.vn/vi/tim-viec-lam/data-analyst.35BB58E5.html); `salary=Lương: 20 Tr - 35 Tr VND`; Hải Dương và Hà Nội; `20-02-2023` | `Thu nhập 20 - 35tr/tháng` | Currency từ salary và period từ cùng tin, hai đầu khớp. Review Data/ML và basis “thu nhập”; không tự gọi gross hoặc lương cơ bản. |
| 978 / `35BB58DC` | [Data Engineer — YODY](https://careerbuilder.vn/vi/tim-viec-lam/data-engineer.35BB58DC.html); `salary=Lương: 25 Tr - 50 Tr VND`; Hà Nội và Hải Dương; `20-02-2023` | `Thu nhập 25 - 50tr/tháng` | Currency/period cùng tin; JD ETL, data warehouse và streaming xác nhận công việc dữ liệu. Review basis như trên. |
| 268 / `35BB74A6` | [Nhân viên IT — VACS](https://careerbuilder.vn/vi/tim-viec-lam/nhan-vien-it.35BB74A6.html); `salary=Lương: 8 Tr - 11 Tr VND` | `Mức lương: Từ 8 đến 11 triệu/tháng` | Có kỳ và currency cùng dòng nhưng JD helpdesk/phần cứng/mạng; không đưa vào bảy nhóm phần mềm chỉ vì có IT. |

Bốn ID trên mỗi ID xuất hiện đúng một lần trong raw 2023. Điều này chỉ xác nhận không lặp ID trong file, chưa chứng minh không repost. Ba URL CareerBuilder của Jaxtina/YODY đều không mở lại được bằng web fetch; chứng cứ là nội dung snapshot CSV có hash, không phải xác nhận trang đang tuyển ngày nay. Có thể review row-level evidence mà không cần gán `salary_period_confirmed=true` cho cả nguồn.

Trong **cột salary** của cả hai CSV, phép dò `/tháng`, `/month`, `per month`, `monthly`, `mỗi tháng`, `hàng tháng` không có hit. Kết quả này không áp dụng cho title/JD: chính Jaxtina/YODY là phản ví dụ.

`jobs-2026` record 13, TopCV ID `2000941`, có title nêu thu nhập 40–55 triệu/tháng và salary `40 - 55 triệu`. [Trang TopCV cùng ID](https://www.topcv.vn/viec-lam/senior-software-engineer-nodejs-5-nam-kinh-nghiem-thu-nhap-tu-40-55-trieu-thang/2000941.html) hiển thị lại title/range, nhưng phần nội dung kiểm được chưa cung cấp currency tường minh cho khoảng này. Không đổi “triệu” thành VND. Download HTML trực tiếp trả HTTP 403; không thử vượt chặn hay lấy hidden salary. ID `2000137` không fetch được. Không tăng accepted count.

## 2. Trang nhà tuyển dụng có khoảng VND/month trực tiếp

| Tin / primary URL | Trích ngắn chứng cứ | Diễn giải có giới hạn |
| --- | --- | --- |
| [Majorbird — Confirmed ERP Developer, job 10](https://majorbird.com/vi/jobs/confirmed-erp-developer-10) | `Salary: 15,000,000–25,000,000 VND/month, based on experience.` | HCM; Python/Odoo 1–3 năm; bonus dự án ghi riêng. Khoảng 15–25 triệu, trung điểm ứng viên 20 triệu VND/tháng. Backend/Fullstack cần mapping từ JD, không tự chấp nhận theo tên ERP. |
| [Salely AI — .NET Developer, careerjob 2](https://salely.ai/careerjob/net-developer/2) | `Salary: 20 – 35 million VND/month` | Hà Nội; JD .NET Core/ASP.NET MVC/Web API, 1–2 năm. Khoảng 20–35 triệu, trung điểm ứng viên 27,5 triệu VND/tháng. Cùng salary lặp trong phần benefits vẫn là một tin; “5 openings” không phải năm nhãn. |

Hai trang HTTP public tải thành công; không có revision cố định, không xác nhận ngày đăng hoặc gross/net. Hash HTML tải mới:

- `majorbird.html`: 72.398 bytes; SHA-256 `16af42b822c60a321f15f709495fae4dc015c699cbf778b5d70fb738285954e0`.
- `salely.html`: 13.068 bytes; SHA-256 `d0c986c3eea021bffc1ed23a5814aaf0bfc0f3a10a3a8356a393f5361ee24880`.

**Redistribution:** chưa thấy giấy phép mở cho nội dung tuyển dụng. Majorbird có copyright; Salely ghi all rights reserved. Công khai đọc được không đồng nghĩa cho phép đóng gói HTML/JD thành dataset. Chỉ ghi URL và trích chứng cứ ngắn trong báo cáo; chưa phê duyệt phân phối/train. VAON Junior Flutter có kết quả tìm kiếm nêu VND/month nhưng mở primary URL trả **410 Gone** ở cả web fetch và download; không tính làm tin được xác minh hiện tại.

## 3. Dataset mới có row-linked salary: IT-Job-Posting

Primary publisher: [SonPhatTranDeveloper/IT-Job-Posting](https://github.com/SonPhatTranDeveloper/IT-Job-Posting). [CSV public trực tiếp](https://raw.githubusercontent.com/SonPhatTranDeveloper/IT-Job-Posting/main/job_descriptions.csv), tải không credentials. Ref `main` có thể thay đổi; chưa xác minh commit SHA do GitHub tree API trả **403 rate limit**, vì vậy dùng hash byte đã tải làm dấu vết snapshot, không gọi main là revision bất biến.

- CSV: **11.087.006 bytes**, **3.101 records**, 11 cột; SHA-256 `68c70420d9a12381a5731f0dbee1cc2b4d2123a94882eb95bd0104a1201e8b69`.
- Cột: `title`, `company`, `company_image_url`, `location`, `description`, `site`, `job_url`, `it_role_type`, `main_programming_languages`, `key_technologies`, `city`.
- Có URL tin/employer/JD để review; không có cột ngày đăng. Không suy ngày đăng từ tracking timestamp hoặc thời điểm GitHub/download. Vai trò/kỹ năng có phần do LLM trích theo README, cần review lại bằng JD.
- [README chính chủ](https://github.com/SonPhatTranDeveloper/IT-Job-Posting/blob/main/README.md) chỉ giới hạn sử dụng giáo dục; không thấy LICENSE trong file listing. Không coi đây là CC0/MIT hoặc quyền phân phối đầy đủ. README tải: SHA-256 `99109bde90a75e0259ecaf635d5f15221e43f6d8d161752790906dab858c7a8e`.

### Mười ứng viên được kiểm tra bằng description cùng record

Các khoảng sau đều ghi rõ currency và period trong câu nói về salary. Đơn vị số ở cột khoảng là **triệu VND/tháng**. Gross/net chỉ ghi khi nguồn nêu; không trộn chúng thành một target chung. URL dưới đây bỏ riêng tracking query để dễ đối chiếu; raw URL vẫn giữ nguyên trong CSV /tmp.

| Record | Tin và primary posting URL | Khoảng / basis | Chứng cứ ngắn trong description |
| --- | --- | --- | --- |
| 301 | [Quang Trung — Senior .NET Core](https://itviec.com/it-jobs/net-developer-net-core-asp-net-mvc-english-quang-trung-software-development-2810) | 20–35; gross/net unknown | `Competitive Salary: 20 – 35 million VND/month.` |
| 308 | [DOL — Senior Front-end](https://itviec.com/it-jobs/senior-front-end-developer-reactjs-javascript-dol-english-0208) | 30–50; NET | `Lương: 30.000.000 - 50.000.000 VND/ tháng (Net)` |
| 367 | [DOL — Senior Java](https://itviec.com/it-jobs/senior-java-software-engineer-aws-mongodb-dol-english-0030) | 30–50; NET | `Lương: 30.000.000 - 50.000.000 VND/ tháng (Net)` |
| 472 | [Quang Trung — Senior Angular](https://itviec.com/it-jobs/frontend-developer-reactjs-next-js-angular-english-quang-trung-software-development-0329) | 20–35; unknown | `Competitive Salary: 20 – 35 million VND/month` |
| 751 | [PioneerX — AI & Workflow Automation](https://itviec.com/it-jobs/ai-workflow-automation-engineer-pyhton-javascript-cong-ty-tnhh-digital-marketing-va-e-commerce-pioneerx-1351) | 13–18; unknown | `Lương: 13 - 18 triệu VNĐ/tháng (thỏa thuận)` |
| 883 | [Infinity Innovations — Backend Programmer](https://itviec.com/it-jobs/backend-programmer-java-python-linux-english-cong-ty-tnhh-bpo-infinity-innovations-group-4048) | 20–40; unknown | `Salary range: 20,000,000 VND – 40,000,000 VND/month` |
| 1533 | [Manpower Vietnam — Lead Java](https://www.linkedin.com/jobs/view/4250139873/) | 80–120; base salary, gross/net unknown | `Base salary from 80.000.000 - 120.000.000 VND/month.` |
| 1997 | [XGame — Backend Technical Leader](https://www.topcv.vn/viec-lam/backend-technical-leader/1683894.html) | 35–50; unknown | `Lương: 35.000.000 - 50.000.000 VNĐ/tháng` |
| 2528 | [Viettel Construction — Java](https://www.topcv.vn/viec-lam/lap-trinh-vien-java-dev-middle-to-techlead/1722942.html) | 20–32; lương cứng, gross/net unknown | `Lương cứng tháng : 20.000.000 - 32.000.000 đồng/ tháng` |
| 2717 | [Logic Lab — PHP + React/NextJS](https://www.topcv.vn/viec-lam/fullstack-developer-php/1757483.html) | 15–30; unknown | `Ranges from 15,000,000 to 30,000,000 VND/month` |

Đây là **10 URL khác nhau trong bảng tuyển chọn**, có địa điểm Việt Nam theo raw (HCM/Hà Nội); chưa phải 10 leakage groups. Ba URL có bản sao trong cùng CSV: records **1997/2739**, **2528/2809**, **2038/2717**. Riêng bảng tuyển chọn vì vậy tương ứng 13 records raw, không phải 13 tin. Chưa dedup/finalize toàn bộ nguồn.

**Đối chiếu primary thành công:** trang [ITviec của record 301](https://itviec.com/it-jobs/net-developer-net-core-asp-net-mvc-english-quang-trung-software-development-2810) hiển thị trong “Why you'll love working here” đúng khoảng 20–35 million VND/month, cùng công ty, title và địa chỉ Gò Vấp/HCM. Dù header có nút đăng nhập để xem salary, câu benefits này đã hiển thị trong nội dung public được fetch; không đăng nhập hoặc vượt che chắn. Không biến “Posted 34 days ago” trong trang/cache thành ngày đăng tuyệt đối. Không có HTML download/hash cho trang này; corroboration là web read trong lượt này. DOL record 308 không mở lại được; các dòng còn lại dựa vào snapshot CSV mới, chưa kiểm live từng tin.

Để minh họa false positive: phép dò currency sát `/month`, `/tháng` hoặc `per month` trên description cho **151 occurrences trong 128 records**. Những con số này là regex hits, **không phải nhãn lương**: có phụ cấp ăn trưa, đi lại, học tiếng Anh, single-bound, CNC và nghề ngoài phạm vi. Ví dụ record 24 chỉ có lunch allowance 730.000 VND/month; record 202 là up to 30 triệu hoặc cao hơn; record 517 NET up to 30M. Không lấy chúng làm fixed/bounded target. Records 2869/3099 chung URL Wordpress nhưng khác role do bên phát hành gán: cần entity/role conflict review, không tin role column một cách máy móc.

**Đánh giá:** nguồn này đáng ưu tiên review hơn VietJobs vì có URL cùng description và nhiều câu salary trực tiếp. Vẫn blocked vì giấy phép phân phối, ngày nguồn, mapping nghề, basis, repost/leakage và acceptance policy chưa được giải quyết. Không import CSV vào canonical trong lượt nghiên cứu này.

## 4. VietJobs: đã kiểm đủ CSV, chưa giải quyết gate

Primary: [VinNLP/VietJobs](https://github.com/VinNLP/VietJobs), liên kết tới [Hugging Face dinhieufam/VietJobs](https://huggingface.co/datasets/dinhieufam/VietJobs).

- API metadata public xác nhận `private=false`, `gated=false`, revision **`ea140511b77935704e93d21c2973b72f46d48902`**, lastModified `2026-03-02T04:44:41.000Z`, `cardData=null`.
- [CSV tại revision cố định](https://huggingface.co/datasets/dinhieufam/VietJobs/resolve/ea140511b77935704e93d21c2973b72f46d48902/VietJobs.csv): **103.110.903 bytes**, SHA-256 **`85862b06fda4e814fe0c1d8622f173d189c92758345f77df16d1232d0c49d477`**, khớp LFS SHA-256 do HF tree API khai báo.
- Đếm thực tế: **48.092 rows**, **18 cột**. Cột `category=công_nghệ_thông_tin_kỹ_thuật_số` có **1.906** rows: **1.903** Việt Nam, 2 Nhật Bản, 1 Mỹ. Category rộng gồm sales, design, hardware; không gọi tất cả là bảy nghề phần mềm.
- Toàn bộ `salary` không có token currency `VND`, `VNĐ`, `đồng` và không có period theo phép dò nêu trên. **13.727** rows có salary `0.0 triệu`; đây không phải chứng cứ lương bằng 0.
- Không có các cột `job_url`, `job_id`, company/employer hoặc posting date. Có thể trỏ về record và hash CSV nhưng chưa trỏ về tin gốc để kiểm entity/ngày/bằng chứng bổ sung.

Các trường: `job_title`, `location`, `country`, `qualifications`, `technical_skills`, `soft_skills`, `languages_required`, `experience_required`, `salary`, `contract_type`, `working_hours`, `benefits`, `description`, `requirements_text`, `category`, `salary_min`, `salary_max`, `salary_avg`.

**Giấy phép:** [LICENSE của repo chính chủ](https://github.com/VinNLP/VietJobs/blob/main/LICENSE) ghi MIT, copyright 2025 VinNLP. File LICENSE tải từ main có SHA-256 `cba34d05e9684d44839d95d154abef3a85b82b3c4766f4a31e2468961bb84bfa`; điều kiện giữ copyright/license notice. Tuy nhiên HF tree chỉ có `.gitattributes` và CSV, không có card/license riêng. Chưa đủ để mặc nhiên xác nhận MIT cho quyền tái phân phối toàn bộ nội dung tin bên thứ ba; cần làm rõ phạm vi dataset với bên phát hành trước bàn giao.

Một số đối chứng đọc trực tiếp, record 1-based:

| Record | Chứng cứ và vấn đề |
| --- | --- |
| 17420 | Frontend ReactJS: salary `20.0 - 26.0 triệu`; “sinh nhật hàng tháng” trong benefits không chứng minh kỳ trả của salary. |
| 17506 | Data analyst: `0.0 triệu`, benefits `Lunch allowance 1,000,000 VND/month`; không phải lương 1 triệu. |
| 17660 | Project manager: salary `22.0 - 40.0 triệu` nhưng benefits chỉ offer up to 40 million VND/month + commission; không dùng lower bound 22 như đã được cùng câu offer xác nhận, và ngoài bảy nhóm nghề. |
| 17962 | Test Lead: salary_min=max `45`, nhưng benefits là upto 45m/month; single-bound không thành fixed, currency chưa rõ; QA Automation cũng chưa được xác nhận. |
| 18371 | TechLead NodeJS: structured salary 0, benefits up to 60m/month; không suy fixed hoặc VND. |
| 18576 | Software internship: range 2.0–2.4 triệu nhưng salary_min=max 2; allowance text `2.000000 VND/month` cần review notation/basis, không tự sửa hoặc làm tròn. |
| 18820 | Internship range 3–4 triệu, benefits up to 11.000.000 VND/tháng **sau** ký hợp đồng chính thức; không lấy mức tương lai cho range thực tập. |
| 18864 | salary 5–200 triệu xung đột với benefits lương cơ bản 7–12 triệu đồng/tháng; role triển khai chưa đủ nhận vào bảy nhóm. |
| 19213 | Trợ lý số & AI: description nêu thu nhập 7–10 triệu VND/tháng; có currency/period nhưng không chứng minh là nghề lập trình Data/ML, thiếu posting provenance. |

Có period trong một số description/benefits không có nghĩa cả dataset đã xác nhận period. Không gán monthly từ working_hours, 13th salary hoặc báo cáo tháng. Số nhãn đủ provenance/basis/role/license được chấp nhận từ VietJobs trong lượt này: **0**; không tuyên bố mọi dòng đều không có chứng cứ tháng.

## 5. Tái kiểm và bước tiếp theo có giới hạn

Download chỉ nằm trong `/tmp/ml-label-research-20261029/` (macOS có thể hiện `/private/tmp/...`), không phải artifact bàn giao bền vững. Giữ hash/primary URL trong báo cáo để tải lại; các HTML/ref main có thể đổi. Không có credentials, signup, giải CAPTCHA hoặc vượt 403/410/rate limit. Không dùng số liệu benchmark, salary report tổng hợp hay kết quả tìm kiếm thay cho row-linked label.

Quy trình tái kiểm bằng thư viện chuẩn Python, không chạy pipeline/fit:

```python
import csv, hashlib, re
from pathlib import Path

p = Path('/tmp/ml-label-research-20261029')
for name in ['VietJobs.csv', 'it-posting.csv']:
    b = (p / name).read_bytes()
    with (p / name).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    print(name, len(rows), hashlib.sha256(b).hexdigest())

with (p / 'it-posting.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
pattern = re.compile(
    r'(?:VND|VNĐ|đồng)\s*(?:/\s*(?:month|tháng)|per\s+month)', re.I
)
matches = [(i, m.group()) for i, row in enumerate(rows, 1)
           for m in pattern.finditer(row['description'])]
print('occurrences', len(matches), 'records', len({i for i, _ in matches}))
# 151 / 128 là số hit để đọc tiếp, không phải số accepted labels.
for i in [301, 308, 367, 472, 751, 883, 1533, 1997, 2528, 2717]:
    print(i, rows[i-1]['job_url'], rows[i-1]['description'])
```

Ưu tiên review Jaxtina `35BB4811` trên raw CC0 đã có hash, rồi quyết định basis của hai tin YODY; đây là hướng bổ sung evidence cùng tin mà không cần nguồn lớn mới. Với IT-Job-Posting, giải quyết phạm vi educational/redistribution trước import, rồi kiểm ngày và danh tính/repost, gross/net/base/total cùng role bằng JD. Trang employer là chứng cứ khả thi cho một tập tuyển chọn nhỏ nếu có quyền sử dụng phù hợp, không thay cho dataset đại diện thị trường.

Các bước trên là công việc tiếp theo được đề xuất, chưa thực hiện thay đổi canonical hoặc liên hệ publisher. Gate vẫn blocked cho training, đánh giá, dự đoán và tư vấn dựa trên model; không có lý do đổi gate chỉ từ số hit hoặc số URL tuyển chọn.

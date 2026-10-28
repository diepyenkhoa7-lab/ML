# Xuất xứ bản nhập T01 ngày 29/10/2026

Các CSV trong `raw/` được trích nguyên byte từ hai ZIP mới do main tải vào `/private/tmp/ml-data-20261029`. Không dùng file dữ liệu cũ. ZIP đã kiểm bằng `unzip -t` và SHA-256 trước khi trích. Không lưu lại ZIP trong repository.

| Source ID | Revision | Dòng thô | Cột | SHA-256 ZIP | SHA-256 CSV |
| --- | --- | --- | --- | --- | --- |
| jobs-2023 | Kaggle v2 | 2056 | 20 | ffaf1a9a06848036e25ed9d87836e6f5a4918237aa34d312298fdf9e24b59307 | 8014c43996075240d309a137f11436c1e3af218afa7e823e83d67ac6f7c85a3c |
| jobs-2026 | Kaggle v1 | 1550 | 7 | 29651eb3e85d4d5b0fb8e45f968e01585c51de95f038cb850dc72607352f0426 | e78ff2b6ed521ad894a70271a3254fcf434813916fdade4f7d449bc4fdf34ef9 |

Nguồn 2023: Nguyen Tran Huu Thinh (`lucaznguyenofficial`), *Vietnamese Job Posting - Vietnamese Version*, dữ liệu CareerBuilder theo bên phát hành; [Kaggle](https://www.kaggle.com/datasets/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version). Metadata khai báo CC0: Public Domain. Giữ nguyên nội dung, kể cả HTML, trường trống và nhiều địa điểm.

Nguồn 2026: Châu Gia Bảo (`baocgb`), *Vietnam IT Jobs – Raw Data from TopCV (2026)*; [Kaggle](https://www.kaggle.com/datasets/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026). Metadata khai báo [Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Giữ nguyên nội dung; không đổi URL có tham số tracking. Nguồn không có JD hoặc ID riêng.

Snapshot JSON do main cung cấp được sao chép nguyên byte vào `provenance/metadata-2023.json` và `metadata-2026.json`. Chúng ghi revision, tác giả, giấy phép và `lastUpdated` của dataset; `lastUpdated` không phải ngày đăng từng tin hoặc ngày tải. `announcement_date`/`date_posted` và `expiration_date` vẫn giữ đúng tên trường gốc. `imported_on` trong catalog là ngày nhập local, không thay thế thời gian nguồn.

Kỳ lương chưa được xác nhận ở cả hai nguồn. T01 chỉ hiển thị số dòng thô, không coi đó là số tin duy nhất, số tin thuộc nhóm nghề hoặc số nhãn lương hợp lệ.

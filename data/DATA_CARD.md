# Data card — các nguồn đã nhập ngày 17/10/2026

## Bộ dùng cho huấn luyện kế tiếp

Đã rà soát nhãn và đóng băng `data/splits/v1.0.1/`: bộ developer Việt Nam có
176 mẫu (123 train / 25 validation / 28 test); CNTT rộng có 375 mẫu. Khảo sát và
các tiền tệ quốc tế giữ riêng. 402 nhãn ứng viên cách ly, 4 bản trùng bị loại.
Xem [quy tắc và giới hạn](../docs/LABEL_REVIEW_AND_SPLITS.md) cùng
[báo cáo](../outputs/label_review/v1.0.1/REPORT.md). Mô hình lương và trial Gemma 100 bước đã train. Xem [runbook](../docs/TRAINING_RUNBOOK.md).

## Kết quả chuẩn hóa phiên bản 1.0.0

| Nguồn | Clean | Review/cách ly | Có nhãn số |
|---|---:|---:|---:|
| Vietnam IT Job Posts (file bạn gửi) | 885 | 5.218 | 153 |
| VietJobs 2025 | 578 | 823 | 317 |
| Stack Overflow 2025 | 35.103 | 10.528 | 18.660 |
| DataForge 08/2026 | 44.251 | 303.725 | 14.409 |

File sạch: `data/processed/cleaned/<source_id>/`; mỗi nguồn có `clean.csv`,
`review.csv`, `audit.csv`, `manifest.json` và thư mục `labels/` tách đơn vị.
Không cộng các nhãn khác loại/tiền tệ hoặc suy thành số tin duy nhất giữa nguồn.
Clean vẫn có thể thiếu lương; các file nhãn chỉ chứa dòng có target số hợp lệ.

[Kết quả và giới hạn](../outputs/data_quality/cleaning/REPORT.md) ·
[Quy tắc/lệnh chạy lại](../docs/DATA_CLEANING.md). Đây là kết quả giai đoạn làm sạch;
bộ chia sau rà soát nhãn được mô tả ở đầu tài liệu này.

## Bản lọc ứng viên trước khi làm sạch
| Nguồn | Số dòng raw | CSV ứng viên | Số dòng ứng viên |
|---|---:|---|---:|
| File Vietnam IT Job Posts người dùng gửi | 6.779 | `user_vietnam_it_jobs_2026.csv` | 2.755 |
| VietJobs — dữ liệu Việt Nam 2025, công bố 2026 | 48.092 | `vietjobs_it_candidates.csv` | 1.906 |
| Stack Overflow Developer Survey 2025 | 49.191 | `stackoverflow_2025_salary_candidates.csv` | 23.947 |
| DataForge — snapshot quốc tế 01/08/2026 | 394.300 | `dataforge_2026_08_software_salary_candidates.csv` | 13.268 |

Các CSV ứng viên nằm trong `data/processed/source_views/`. **Tiêu chí lọc khác nhau**:
file người dùng lọc ngày đăng năm 2026; VietJobs lọc category CNTT; Stack Overflow lọc
thu nhập quy đổi dương; DataForge lọc chức danh phần mềm bằng regex và hai đầu lương
dương. Các số dòng trên chưa phải số mẫu sạch cuối cùng và không được cộng thành
số tin IT duy nhất giữa các nguồn.

## Định nghĩa nhãn và phạm vi

- **File người dùng:** lương chào tuyển dạng chuỗi; có VND/USD, tháng/năm và thỏa thuận.
  Đã có bản chuẩn hóa riêng và nhãn trung điểm khi đủ đơn vị. Nguồn tải/giấy phép chưa xác định;
  3.200 dòng lịch sử có mẫu phân bố đều và URL cần xác minh, đã xuất riêng để rà soát.
- **VietJobs:** lương chào tuyển theo triệu VND/tháng. Có 1.144/1.906 tin IT có hai
  đầu lương dương; một số cột số làm mất phần thập phân so với chuỗi lương gốc.
  Bản sạch dựng lại nhãn theo chuỗi lương và ghi cờ sửa phần thập phân.
  Dataset toàn ngành có 385 dòng trùng hoàn toàn, đã loại trong bản sạch.
- **Stack Overflow:** total annual compensation trước thuế/khấu trừ theo schema,
  `ConvertedCompYearly` là USD/năm. Có 23.469 dòng có thu nhập dương và `WorkExp`,
  nhưng chỉ 57 dòng có thu nhập dương tại Việt Nam: không đủ để suy rộng mô hình
  toàn cầu thành mô hình lương riêng thị trường Việt Nam. Có giá trị rất lớn cần
  rà soát ngoại lệ; chưa cắt ngoại lệ ở bản ứng viên.
- **DataForge:** khoảng lương theo currency/period gốc. Không có mô tả toàn văn hoặc
  số năm kinh nghiệm dạng số trong gói miễn phí. Phần lớn là quốc tế, không dùng để
  suy ra mặt bằng VND/tháng của Việt Nam. Điều khoản trên trang nguồn và file license
  trong ZIP chưa thống nhất; xem hồ sơ nguồn trước khi chọn làm dữ liệu train/phân phối.

Gross/net của các nguồn tin tuyển dụng thường chưa được xác nhận. Không quy đổi
ngoại tệ; chưa có bảng tỷ giá. Giữ riêng nguồn, loại nhãn, quốc gia và tiền tệ.
Các nhãn lương chào tuyển được đưa về tháng khi có kỳ gốc rõ; khảo sát giữ USD/năm.

## Nguồn gốc, tái lập và kiểm tra

- [Hồ sơ nguồn chi tiết](../docs/DATA_SOURCES.md): URL, độ mới, phát hiện chất lượng,
  nguồn có thể dùng cho EDA/hồi quy/Gemma và giới hạn.
- `configs/data_sources.json`: URL tải cố định commit, kích thước và checksum nguồn.
- `data/raw/<source_id>/manifest.json`: bản đã tải, timestamp và SHA-256 từng file.
- `outputs/data_quality/source_inventory.json`: thống kê kiểm tra trực tiếp dữ liệu.
- `outputs/data_quality/source_summary.csv`: bảng tổng hợp ngắn, mở được bằng Excel.
- Tải lại: `make data-fetch`; xuất lại tập ứng viên: `make data-profile`.

Raw được giữ nguyên. File người dùng trong dự án khớp SHA-256 bản được cung cấp.
VietJobs và Stack Overflow khớp checksum Git LFS; ZIP DataForge khớp checksum catalog
và kiểm tra CRC. Checksum chứng minh tính toàn vẹn bản tải, không chứng minh độ chính
xác của các nhãn hoặc tính đại diện thị trường.

## Phần cần làm tiếp trước huấn luyện

Đã có pipeline chuẩn hóa vai trò, kỹ năng, kinh nghiệm, tiền tệ, kỳ lương và khử
trùng xác định. Tiếp tục kiểm tra xuất xứ/nhãn nghi vấn, rà soát ngữ nghĩa và nhóm
tin gần trùng giữa các nguồn. Bộ chia hiện hành đã đóng băng theo nhóm;
fit tiền xử lý trên train. Không dùng trực tiếp
`salary_min/max`, chuỗi salary hoặc nội dung chứa lương làm feature hồi quy.

`data/finetune/*.jsonl` đã có nhãn silver phiếu tin tuyển dụng 364/72/82,
chưa được duyệt thủ công độc lập. Xem manifest và runbook; đã
huấn luyện trial Gemma 100 bước sau xác nhận người dùng. `data/examples/` tiếp tục chỉ là mẫu giả lập kiểm tra kỹ thuật.

## Snapshot nghiên cứu mới v2.1.0 (18/10/2026)

Model đang phục vụ là Ridge `v2_042e3aa1a886`, RF đối chiếu; snapshot/metric v1 còn nguyên. Nguồn mới TiniX/CareerPathKG (CC-BY-NC-4.0) có606.878 tin nhiều ngành, chọn phần lập trình viên2025–2026. Final train79explicit+1078weak_month(weight0,3), valid25/test30explicit-month, company-disjoint và loại công ty holdoutv1. Target là trung điểm lương chào tuyển, chưa chắc gross/net; nhãn silver, không phải gold. Giá trị period thiếu được đánh dấu giả định, không dùng vào validation/test. Xem `docs/SALARY_V2_RUNBOOK.md` và `outputs/metrics/salary_v2_042e3aa1a886/REPORT.md`. Đối chiếu báo cáo khảo sát là sanity check khác quần thể; không phải accuracy mới.

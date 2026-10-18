# Bàn giao dữ liệu đề tài

Gói bên dưới dành cho mô hình tin Việt Nam và Gemma. Gói quốc tế riêng:
`make submission-open-data` → `outputs/submission/open_datasets.zip` (22 file
kèm manifest), gồm các bảng train/valid/test của SO2024 và AIJobs, nguồn/giấy phép.
SO2024: 10.261/2.368/3.158 dòng; AIJobs: 48.321/8.206/15.363 dòng, mục tiêu USD/năm.
Chi tiết tại [INTERNATIONAL_DATA.md](INTERNATIONAL_DATA.md). Hai gói không trộn
USD/năm với VND/tháng. ITviec trong gói cũ là tham chiếu lịch sử, đã bỏ khỏi tư vấn live.

Tạo gói bằng `make submission-data`. File kết quả là
`outputs/submission/datasets.zip`; giải nén giữ nguyên đường dẫn từ gốc dự án.
Không chạy huấn luyện khi tạo hoặc kiểm tra gói.

Gói chứa dữ liệu dẫn xuất thực sự dùng cho hai mô hình lương đang phục vụ,
corpus của adapter Gemma đang dùng và corpus của vòng thử nghiệm 214 dòng gần nhất.
Không phải bản sao mọi nguồn raw đã tải hoặc mọi thử nghiệm lịch sử. Các snapshot
nghiên cứu khác vẫn được lưu trong repo; raw lớn tải lại theo manifest nguồn.

| Thành phần trong ZIP | Vai trò và số dòng |
|---|---|
| `data/splits/v2.1.0/vn_developer/` | Salary train 79, weak train 1.078, validation 25, test 30; cùng dữ liệu cho Ridge và Random Forest |
| `models/salary/v2_042e3aa1a886/training_snapshot.csv` | Snapshot train thực tế mà app dùng để thống kê và tư vấn; không phải holdout |
| `data/finetune_full/v1.0.0/` | Gemma đang phục vụ: 364 train, 72 validation, 82 test; có biến thể thiếu trường nên không phải 518 tin độc lập |
| `data/splits/v1.0.1/vn_developer/` | Các CSV nguồn của corpus Gemma đang phục vụ |
| `data/processed/cleaned/` | Hai bảng sạch: user CSV 885 dòng và VietJobs 578 dòng; gồm cả dòng không đủ nhãn lương, không đồng nghĩa tất cả được train |
| `data/finetune_reviewed/v2.2.0/` | Thử nghiệm mới: 501 train (137 mới + 364 replay), 31 validation, 33 test; candidate không đạt, không dùng trên web |
| `data/annotation/gemma_v2.0.0/` | Quyết định AI rà soát 214 dòng: 201 chấp nhận, 13 loại; bản chỉnh nhãn cuối nằm trong `label_decisions.jsonl` của corpus v2.2.0 |
| `data/references/` | ITviec/TopDev: số liệu tổng hợp đối chiếu thị trường, không dùng làm nhãn train cá nhân |

Salary mục tiêu là trung điểm lương chào tuyển VND/tháng, khác thu nhập thực nhận.
Weak train thiếu kỳ lương được giả định tháng với trọng số 0,3, chỉ dùng trong
train. Validation/test salary dùng nhãn ghi rõ tháng, chia theo nhóm công ty.
Nhãn Gemma là silver từ nguồn/rà soát AI, chưa có gold do người kiểm chứng độc lập.
Test của vòng corrected chưa chạy suy luận vì candidate trượt validation; file test
được bàn giao để tái lập split, không dùng để tiếp tục chỉnh mô hình.

## Nguồn và quyền sử dụng

- TiniX: `tinixai/vietnamese-job-descriptions`, revision
  `679c3a17347ff6ce769d9bf510c122a087493cf6`; ghi công Le et al., CareerPathKG.
  Dataset card ghi CC-BY-NC-4.0, phục vụ nghiên cứu/học tập phi thương mại.
  Manifest và README nguồn đi kèm; gói không chứa parquet gốc khoảng 293 MB.
- VietJobs: VinNLP/VietJobs và `dinhieufam/VietJobs`, revision
  `ea140511b77935704e93d21c2973b72f46d48902`; dữ liệu tuyển dụng năm 2025.
  Giấy phép code MIT không tự chứng minh quyền phân phối dữ liệu thu thập.
  README, giấy phép repo và manifest tải được giữ nguyên.
- CSV người dùng: nguồn tải và giấy phép chưa xác định. Giữ chú thích này khi
  nộp bài; không gắn giấy phép mở mới cho phần dữ liệu này.
- ITviec/TopDev: trích số liệu tổng hợp từ báo cáo, đường dẫn và giới hạn so sánh
  ở `data/references/README.md`. Không gộp USD và VND hay biến trung vị thành hồ sơ.

Gói phục vụ bàn giao học phần theo dữ liệu đã cung cấp; không xác nhận quyền
thương mại/phân phối lại mọi nguồn. Chi tiết kiểm tra nguồn trong
`docs/DATA_SOURCES.md` và từng manifest. Báo cáo lịch sử không được đổi thành dữ
liệu thị trường mới chỉ vì tải vào năm 2026.

## Kiểm tra sau khi nhận

```bash
make submission-data
.venv/bin/python scripts/package_submission_data.py --verify outputs/submission/datasets.zip
```

`MANIFEST.json` bên trong ZIP ghi mục đích từng file, số dòng, dung lượng và SHA-256.
Lệnh tạo gói kiểm tra hash/số dòng so với các manifest cố định, kiểm tra adapter
và model salary vẫn là phiên bản đang phục vụ, sau đó kiểm tra CRC và hash mọi
thành viên ZIP. SHA-256 toàn ZIP nằm ở `outputs/submission/verification.json`.
Không cộng số dòng của các thư mục với nhau: nhiều file là cùng dữ liệu được
biến đổi hoặc replay. Trọng số model, dữ liệu người dùng upload vào app, cache
và các file raw lớn không nằm trong ZIP này.

# Nhãn và tập huấn luyện — v1.0.1

Bản đã vượt qua kiểm tra độc lập nằm ở `data/splits/v1.0.1/`.
Bộ chính **vn_developer** có 176 mẫu, nhãn `salary_monthly_vnd`: trung điểm lương
chào tuyển, chuẩn hóa về tháng, chưa rõ gross/net. Gồm 31 mẫu từ file người dùng và
145 mẫu VietJobs. Đây là dữ liệu cho thực nghiệm học phần, số mẫu còn nhỏ.

| Bộ | Train | Validation | Test | Vai trò |
|---|---:|---:|---:|---|
| `vn_developer` | 123 | 25 | 28 | Bộ chính: phát triển phần mềm, backend, frontend, full-stack, mobile, embedded, ML engineer, data engineer |
| `vn_it` | 261 | 55 | 59 | Bộ CNTT rộng hỗ trợ phân tích; bộ cha của developer |
| `so_survey` | 13.062 | 2.799 | 2.799 | Tổng thu nhập cá nhân USD/năm, giữ riêng với tin tuyển dụng |

DataForge được chuẩn bị theo từng tiền tệ riêng; các nhóm đủ số mẫu gồm USD, CAD,
EUR, GBP và PLN. 21 nhóm tiền tệ nhỏ chỉ xuất `insufficient_data.csv`, không tạo
test set quá nhỏ. Nguồn này thiếu số năm kinh nghiệm và có điều khoản chưa thống
nhất giữa trang tải/gói ZIP; xem [hồ sơ nguồn](DATA_SOURCES.md) trước khi lựa chọn
cho thực nghiệm. Không dùng số mẫu quốc tế để diễn giải lương thị trường Việt Nam.

## Những gì đã rà soát

- Kiểm tra toàn bộ **33.539 nhãn số ứng viên**: tính nhất quán với min/max, kỳ lương,
  tiền tệ, trạng thái, quốc gia và danh tính. Khảo sát được đối chiếu trực tiếp với
  `ConvertedCompYearly` và lựa chọn lập trình là nghề nghiệp chính trong raw.
- Ghi **69 quyết định rà soát trường nguồn bằng Codex** ở
  `configs/label_inspections.csv`, gồm 48 mẫu ngẫu nhiên theo nguồn và các trường
  hợp nhắm đích. Chức danh của bộ developer cũng đã được đọc để tìm nghề ngoài
  phạm vi; các ca máy phay, báo cháy, PLC/DDC, điều khiển chiếu sáng/BMS và làm ở
  Nhật đã được cách ly. Không coi các quyết định này là nhãn chuẩn do con người
  xác nhận hoặc xác minh độc lập với nhà tuyển dụng.
- **402 dòng cách ly**, **4 dòng trùng cùng danh tính/nhãn bị loại khỏi splits**;
  còn 33.133 dòng được chấp nhận theo quy tắc ở các nguồn/tiền tệ khác nhau.
  Các con số này không được cộng thành số tin duy nhất trên toàn thị trường.
- Riêng 470 nhãn Việt Nam ban đầu còn 375 mẫu CNTT rộng: 77 nhãn từ file người
  dùng và 14 từ VietJobs cần rà soát; 4 bản trùng VietJobs được loại. Trong số
  được giữ, 176 thuộc danh sách vai trò developer đã công bố.

Các vấn đề cụ thể: QC giày dép/xây dựng, IELTS tester và nghề tiếp thị mobile app
bị gán thành QA/developer; tin tuyển nhiều nghề; khoảng lương rộng trên 5 lần;
tin Ybox không có nội dung đối chứng cho khoảng lương; tin lương VND nhưng làm ở
Nhật. Chỉ cách ly nhãn, không tự sửa thành một con số được đoán là đúng.

Các quy tắc tự động luôn có ưu tiên hơn ghi chú `keep` của lượt đọc mẫu. `keep`
chỉ có nghĩa lượt đọc trường nguồn không bổ sung lý do loại; không bảo đảm một
dòng vượt qua mọi kiểm tra quốc gia, danh tính hoặc phạm vi nghề sau đó.

## Chia tập và chống rò rỉ

1. Xử lý trùng cùng danh tính trước khi chia. Nếu cùng danh tính nhưng nhãn/đơn vị
   mâu thuẫn thì cách ly cả nhóm, không lấy trung bình các nhãn mâu thuẫn.
2. Tạo `leakage_group_id` bằng thành phần liên thông từ ID/URL, nội dung gần trùng
   của các tin Việt Nam, và company + title + country + location của DataForge.
   Các cặp gần trùng chỉ được gom cùng tập, không tự xóa hoặc coi chênh lương là
   nhãn sai. Không gom các người khảo sát khác ID chỉ vì hồ sơ giống nhau.
3. Các ngưỡng tương đồng cố định trong `configs/label_review.json`. TF-IDF chỉ dùng
   tìm nhóm tin, không được dùng làm vectorizer cho mô hình dự đoán. Không dùng
   giá trị target để chọn seed hay phân bổ tập. Chưa tìm thấy cặp gần trùng qua
   nguồn bằng quy tắc hiện tại; điều này không chứng minh mọi tin trùng qua nguồn
   đã được phát hiện, nhất là khi VietJobs thiếu URL và tin kia thiếu mô tả.
4. Shuffle danh sách nhóm đã sắp xếp, **seed 42**, mục tiêu 70/15/15 theo số nhóm.
   Mỗi họ dữ liệu Việt Nam/khảo sát/DataForge chia riêng. Các tiền tệ DataForge
   dùng cùng ánh xạ nhóm để một nhóm không đổi tập giữa hai file tiền tệ.
5. Developer lọc từ bộ VN CNTT cha và giữ **đúng phân bổ của bộ cha**, nên tỷ lệ
   từng tập con không đúng tuyệt đối 70/15/15. Không chia ngẫu nhiên lại bộ con.
6. CSV huấn luyện chỉ chứa whitelist features, target và metadata. Loại ID, source,
   group ID và row index khỏi model; chúng chỉ dùng join/kiểm tra. Chọn một trong
   `skills`/`skills_json`, không vector hóa cùng thông tin hai lần. Không đưa
   chuỗi lương, min/max lương, chức danh hoặc mô tả có thể chứa lương vào features.

**Đây không phải chia theo thời gian.** VietJobs thiếu ngày đăng từng tin và nguồn
khác cũng thiếu ngày. Kết quả sau này đo tổng quát hóa sang các nhóm chưa thấy
trong snapshot hỗn hợp 2025–2026, không chứng minh dự đoán tốt thị trường tương lai.

## Chạy lại và kiểm tra

```bash
make test-data
make data-split
make data-verify
make lint
```

`make data-split` chạy `scripts/prepare_salary_splits.py --freeze`.
`FROZEN.json` ghi chữ ký code/chính sách/nhãn và checksum manifest. Chạy lại cùng
đầu vào tái lập cùng kết quả; đổi seed, chính sách, quyết định nhãn hoặc code sẽ
bị từ chối ghi vào phiên bản đã đóng băng. Tăng `version` trong
`configs/label_review.json` khi cần một thực nghiệm dữ liệu mới và ghi rõ thay đổi.
Không đổi tập test sau khi đã xem kết quả mô hình để tìm điểm số tốt hơn.

`configs/salary.yaml` trỏ đến bộ developer v1.0.1. Pipeline hồi quy và kết quả đã có;
xem [runbook](TRAINING_RUNBOOK.md).
Khi huấn luyện Ridge/Random Forest: dùng cùng bộ chia, fit imputer/encoder/scaler/
vectorizer chỉ trên train, chọn cấu hình bằng validation, đánh giá test một lần
bằng MAE/RMSE/R². Các vai trò hiếm chỉ có vài mẫu, một số không có trong validation;
không đủ để kết luận riêng theo vai trò hoặc xếp hạng tác động tăng lương của kỹ năng.

## Truy vết

- `data/processed/reviewed/v1.0.1/all_candidates.csv`: trạng thái/lý do cho từng nhãn.
- `quarantined.csv`, `duplicates.csv`: hai tập tách riêng trong cùng thư mục.
- `data/splits/v1.0.1/assignments.csv`: ID, nhóm và tập của mọi dòng được giữ.
  Dòng của cohort nhỏ chỉ có ánh xạ nhóm dự phòng; không được dùng làm holdout
  khi manifest của cohort ghi `split_prepared=false`.
- `data/splits/v1.0.1/<cohort>/{train,valid,test}.csv` và `manifest.json`.
- [Báo cáo kết quả](../outputs/label_review/v1.0.1/REPORT.md), manifest, validation và
  kiểm tra tái lập trong `outputs/label_review/v1.0.1/`.

Snapshot v1.0.0 là bản ứng viên không đạt kiểm tra quốc gia, có `validation.json`
ghi thất bại; được giữ để truy vết, **không dùng huấn luyện**. Bản hiện hành là v1.0.1.
Các file raw/bản sạch giai đoạn trước được giữ nguyên. Sau bước đóng băng đã train
mô hình lương và chuẩn bị SFT silver riêng; xem [runbook](TRAINING_RUNBOOK.md).
Không thay đổi membership hay nhãn của snapshot đã đóng băng.

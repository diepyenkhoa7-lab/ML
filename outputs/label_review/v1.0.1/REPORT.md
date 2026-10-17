# Kết quả rà soát nhãn và chia tập — v1.0.1

Đã kiểm tra 33.539 nhãn số ứng viên; giữ 33.133 dòng theo quy tắc, cách ly 402 dòng và bỏ 4 bản trùng cùng danh tính/nhãn. Giữ riêng loại thu nhập và tiền tệ. Không huấn luyện mô hình.

## Bộ dùng cho đề tài

| Bộ | Số mẫu | Nhóm | Train | Validation | Test |
|---|---:|---:|---:|---:|---:|
| vn_developer | 176 | 175 | 123 | 25 | 28 |
| vn_it | 375 | 368 | 261 | 55 | 59 |
| so_survey | 18.660 | 18.660 | 13.062 | 2.799 | 2.799 |
| dataforge_USD_month_unknown | 12.583 | 12.078 | 8.823 | 1.893 | 1.867 |
| dataforge_CAD_month_unknown | 283 | 280 | 199 | 37 | 47 |
| dataforge_EUR_month_unknown | 640 | 610 | 464 | 89 | 87 |
| dataforge_GBP_month_unknown | 350 | 303 | 256 | 40 | 54 |
| dataforge_PLN_month_unknown | 82 | 78 | 57 | 8 | 17 |

**Bộ chính: `vn_developer`.** Nhãn VND/tháng, lương chào tuyển, chưa rõ gross/net. Chỉ 176 mẫu từ 31 tin người dùng và 145 tin VietJobs; test 28 mẫu nên độ ổn định của metric còn hạn chế. Bộ developer là tập con của VN CNTT và giữ đúng cùng phân bổ; không cộng hai bộ như hai nguồn độc lập.

Bộ khảo sát là tổng thu nhập USD/năm. DataForge là lương chào tuyển tháng theo từng tiền tệ, thiếu kinh nghiệm dạng số và còn giới hạn nguồn/điều khoản; không trộn các nhãn này với VND/tháng. 21 cohort nhỏ chỉ xuất `insufficient_data.csv`.

## File bộ chính

- [train.csv](../../../data/splits/v1.0.1/vn_developer/train.csv)
- [valid.csv](../../../data/splits/v1.0.1/vn_developer/valid.csv)
- [test.csv](../../../data/splits/v1.0.1/vn_developer/test.csv)
- [manifest bộ chính](../../../data/splits/v1.0.1/vn_developer/manifest.json)
- [Ánh xạ ID/nhóm/tập](../../../data/splits/v1.0.1/assignments.csv)
- [Các dòng cách ly](../../../data/processed/reviewed/v1.0.1/quarantined.csv)

## Kết quả kiểm tra

- 69 quyết định đọc trường nguồn bằng Codex đã lưu, gồm 48 mẫu theo nguồn và các ca nhắm đích. Đây không phải nhãn chuẩn đã được con người/nhà tuyển dụng xác nhận.
- Loại/cách ly QC giày dép, QC xây dựng, IELTS tester, tiếp thị mobile app, tin không có nội dung đối chứng cho lương, máy phay/điều khiển công trình và công việc thực hiện ở Nhật.
- Các dòng cùng danh tính nhưng nhãn mâu thuẫn sẽ được cách ly. Không đoán lại mức lương hoặc tự gán tỷ giá.
- Không có record hoặc nhóm đã phát hiện xuất hiện ở nhiều tập. Grouping dùng ID/URL, nội dung và company/title/location; chưa bảo đảm nhận diện được mọi tin gần trùng qua nguồn thiếu URL/mô tả.
- Nhãn và đơn vị khớp dữ liệu đầu vào; mọi dòng của hai bộ VN có country=Vietnam.
- Chạy lại độc lập cho cùng manifest/checksum; đổi seed bị chặn khi phiên bản đã đóng băng.
- 16 bài kiểm tra đạt và Ruff đạt. Raw/bản sạch giai đoạn trước không đổi; các file SFT vẫn trống.

Bằng chứng: [validation.json](validation.json), [reproducibility.json](reproducibility.json), [manifest.json](manifest.json).

## Cách dùng tiếp

Cấu hình `configs/salary.yaml` trỏ đến bộ developer v1.0.1. Khi train Ridge và Random Forest, chỉ fit bước điền thiếu/mã hóa/vector hóa/scaling trên train; chọn cấu hình bằng validation và chỉ đánh giá test sau khi chốt. Không dùng ID, source, nhóm hoặc row index làm feature.

Chi tiết quy tắc, ngưỡng, danh sách vai trò, ý nghĩa nhãn và lệnh chạy lại: [LABEL_REVIEW_AND_SPLITS.md](../../../docs/LABEL_REVIEW_AND_SPLITS.md). Bộ này chia theo nhóm với seed 42; thiếu ngày đăng từng tin nên không phải kiểm thử dự báo tương lai.

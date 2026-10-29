# Kiểm duyệt ứng viên nhãn ngày 29/10/2026

Kiểm duyệt thủ công 26 trường hợp đã được tuyển chọn trong báo cáo nghiên cứu, không phải scan/chứng nhận toàn bộ các dataset.

| Kết quả | Số trường hợp |
| --- | ---: |
| accepted | 2 |
| needs_review | 17 |
| excluded | 7 |

- accepted_labels.csv: hai nhãn được chấp nhận, có nguồn/row/hash, hai đầu khoảng, trung điểm và bằng chứng từng trường.
- candidate_review.csv: bảng đối chiếu toàn bộ 26 quyết định và lý do.
- candidate_review.json: hồ sơ chi tiết, bao gồm bằng chứng/offset, trạng thái nguồn, nghề, loại thu nhập và mâu thuẫn phiên bản.
- manifest.json: số đếm, phạm vi, hash các file và lý do chưa đủ readiness.

## Hai nhãn được chấp nhận

| Tin / ID | Vai trò | Khoảng VND/tháng | Trung điểm VND/tháng |
| --- | --- | ---: | ---: |
| YODY Data Analyst / 35BB58E5 | Data/ML | 20.000.000–35.000.000 | 27.500.000 |
| YODY Data Engineer / 35BB58DC | Data/ML | 25.000.000–50.000.000 | 37.500.000 |

Nguồn jobs-2023, Kaggle v2: lucaznguyenofficial/Vietnamese Job Posting – Vietnamese Version, dữ liệu CareerBuilder; giấy phép CC0 do publisher khai báo. Raw trong datasets/raw có SHA-256 8014c43996075240d309a137f11436c1e3af218afa7e823e83d67ac6f7c85a3c. Các record 975 và 978 tính sau header, không phải dòng vật lý CSV. Tiền tệ và khoảng từ salary khớp câu thu nhập tháng trong job_requirements của đúng ID; không suy kỳ từ lịch làm việc hoặc thưởng. source_row_sha256 băm JSON compact, khóa sắp xếp, ensure_ascii=False của nguyên dòng csv.DictReader.

Hai nhãn thuộc compensation_scope=advertised_monthly_income và salary_basis=unknown theo ADR 0006/0007. Không gọi chúng là lương cơ bản, net hoặc gross; không cộng thưởng cuối năm. Cả hai được nguồn ghi ngày 20/02/2023, cùng một công ty, hai nhóm theo trường quan sát khác nhau. Không đại diện lương thị trường năm 2026 hoặc đủ dữ liệu cho mọi nghề.

## Trạng thái sử dụng

accepted nghĩa là được chấp nhận trong hồ sơ kiểm duyệt này, chưa phải model hoặc tập train hoàn tất. canonical_imported=false: chưa thêm logic bổ sung chứng cứ JD vào pipeline; raw, catalog và snapshot eda-v5 giữ nguyên, nên dashboard/base pipeline vẫn có 0 target từ cột salary. Một bước nhập có kiểm soát sau này phải kiểm lại hash/ID và không gán period cho toàn nguồn.

training_ready=false. Chỉ hai nhóm quan sát không tạo được ba tập train/validation/test không rỗng và không giao nhóm; policy đánh giá/hỗ trợ #4 còn mở. Gate #42 giữ nguyên. Chưa fit, không có metric hoặc model mới.

## Giới hạn nguồn khác

Jaxtina có chứng cứ 25–45 triệu VND/tháng nhưng nghề giao Mobile/Backend nên needs_review. VACS là helpdesk/phần cứng ngoài phạm vi. Không đưa phụ cấp, upper bound, lương sau thực tập hoặc structured range mâu thuẫn vào nhãn chính.

Mười ứng viên GitHub và hai trang employer giữ needs_review. Có chứng cứ salary không đồng nghĩa nguồn đã được dự án chấp nhận; quyền dùng cho học tập và quyền phân phối được ghi riêng. Thiếu gross/net hoặc ngày đăng riêng lẻ không tự làm sai chứng cứ tiền/kỳ. Không đóng gói thêm CSV/JD/HTML chưa có phạm vi phân phối rõ.

Hồ sơ external ghi source_row là số record, không phải job ID. posting_external_id từ URL chỉ hỗ trợ đối chiếu; posting_id đầy đủ là URL có namespace nguồn. Với employer HTML, source_row=null và hash theo bytes trang, không giả lập một CSV record.

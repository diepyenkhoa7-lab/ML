# Dataset dẫn xuất TensorFlow v1

Quốc tế: Stack Overflow Developer Survey 2024, thu nhập `ConvertedCompYearly` USD/năm; kinh nghiệm `WorkExp`. Công nghệ là công nghệ người trả lời đã sử dụng, không phải số tin tuyển dụng. Giữ 1.000–1.000.000 USD/năm, kinh nghiệm 0–80 năm, đủ vai trò/quốc gia. Xem `international_audit.csv` cho lý do loại từng dòng.

Việt Nam: TiniXAI Vietnamese Job Descriptions, trung điểm khoảng lương chào tuyển VND/tháng. Chỉ giữ kỳ tháng được ghi rõ trong chuỗi lương hoặc bằng chứng trong nội dung có số tiền khớp. Không dùng giả định tháng; không dùng lương thỏa thuận làm target. Xem `vn_audit.csv` cho các ứng viên thuộc phạm vi CNTT. `experience_kind` ghi rõ kinh nghiệm là số năm, cận dưới hay khoảng; cận dưới được dùng làm đặc trưng.

Chia nhóm công ty và nội dung tin đăng trùng trước khi tạo JSONL. Khảo sát nhóm theo hồ sơ đặc trưng giống nhau. Chia train/validation/test với seed42. Đây là nguồn từng được nghiên cứu; không coi chia lại là benchmark thu thập độc lập.

`source_id` là mã nguồn hoặc chỉ số dòng 0-based trong khảo sát. Các nhãn JSONL là **source-derived silver**, chưa có xác nhận người duyệt; không gọi chúng là human gold. Test không dùng chọn checkpoint. Manifest ghi checksum raw, bảng và JSONL.

Nguồn và giấy phép: [StackExchange/Survey](https://github.com/StackExchange/Survey) — ODbL-1.0 cho database, DbCL-1.0 cho contents; ghi công Stack Overflow. [tinixai/vietnamese-job-descriptions](https://huggingface.co/datasets/tinixai/vietnamese-job-descriptions) — CC-BY-NC-4.0 theo dataset card. Giữ điều kiện nguồn khi phân phối dataset dẫn xuất. URL phiên bản cố định và checksum nằm trong `configs/data_sources.json` ở gốc dự án.

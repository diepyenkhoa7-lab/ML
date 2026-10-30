# T01: Nhập một nguồn mới và xem dữ liệu gốc

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/15). Bằng chứng: job_market/docs/tdd/T01.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Mở ứng dụng Python mới, nhập một file nguồn mới được duyệt và xem bản ghi gốc kèm xuất xứ trong Streamlit.

## Công việc

- [x] Tạo điểm vào Python/Streamlit mới và hợp đồng bản ghi đầu vào tối thiểu.
- [x] Nhập một nguồn thật, giữ raw, ID/URL và metadata nguồn; hiển thị preview.
- [x] Thêm lệnh kiểm tra, lint và CI tối thiểu cho ứng dụng mới.

## Acceptance criteria

- [x] Có thể cài/chạy riêng bản mới và xem nguồn thật, số dòng cùng schema.
- [x] Raw không đổi; lỗi nguồn/schema được hiển thị rõ.
- [x] Không đọc dữ liệu/artifact cũ; không dùng dữ liệu giả thay nguồn thật.

## Blocked by

- [Chọn nguồn dataset Việt Nam mới có thể kiểm chứng](https://github.com/theihoz/ML/issues/3)

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


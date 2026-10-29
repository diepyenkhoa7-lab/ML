# T11: Đối chiếu chất lượng, nhóm trùng và xuất snapshot

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/25). Bằng chứng: job_market/docs/tdd/T11.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng xem bảng sạch/review/trùng theo nguồn và xuất snapshot EDA cùng snapshot đủ nhãn huấn luyện.

## Công việc

- [x] Gom nhóm tin trùng/đăng lại và lưu quan hệ với bản gốc.
- [x] Tổng hợp trạng thái chất lượng và lý do cho từng dòng.
- [x] Xuất các tập EDA/đủ nhãn/review cùng manifest/checksum.

## Acceptance criteria

- [x] Tổng raw/sạch/review/loại/trùng đối chiếu bằng ID được.
- [x] Tin thiếu lương vẫn có thể vào EDA nhưng không tự vào tập target.
- [x] Snapshot mới có nguồn/phiên bản/checksum, chạy lại tái lập được; không lẫn nguồn cũ.

## Blocked by

- T02 — Tải lại đúng phiên bản dataset và kiểm checksum
- T04 — Bổ sung Data/ML, DevOps và QA Automation
- T06 — Giữ nhiều địa điểm, tách Remote và đếm tin duy nhất
- T08 — Bổ sung framework, cơ sở dữ liệu và cloud
- T09 — Chuẩn hóa khoảng lương và đánh dấu nhãn hợp lệ
- T10 — Chuẩn hóa số năm và khoảng kinh nghiệm

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.


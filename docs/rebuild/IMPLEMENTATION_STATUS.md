# Trạng thái triển khai ngày 29/10/2026

## Cập nhật sửa audit trên dev/ml-development

Phần EDA đã push lên main tại 9ce0506. Follow-up A01–A09 đã sửa trên nhánh local dev/ml-development, chưa push. Bộ kiểm tra tích hợp cuối: 246 tests qua cùng Ruff; review hai trục không còn phát hiện cần sửa trong phạm vi các reproducers đã báo. Bằng chứng trong FIX_REVIEW-2026-10-29.md và job_market/docs/tdd/audit-normalization.md, audit-roles.md, audit-exports.md.

Snapshot eda-v5: 3.606 raw = 320 EDA + 556 role_review + 2.730 out_of_scope; 0 duplicate/ID lỗi và 0 target. TopCV có 293 tin EDA sau khi hai title QA thủ công chuyển review; 5 tin Remote trên toàn bộ raw không đồng nghĩa có 5 tin Remote trong EDA. Snapshot ID: 1ccf26a791b6875eaf5a789d45aca30dc0bb18414e866ef132798735e70382e5.

Spec ML và báo cáo nghiên cứu/kiểm duyệt trong docs/rebuild/ml giữ local. Kiểm duyệt 26 trường hợp: hai nhãn YODY được chấp nhận vào file riêng (27,5/37,5 triệu VND/tháng, thu nhập tháng chào tuyển, basis unknown), 17 needs_review và 7 excluded. Chưa nhập canonical, chưa train hoặc đổi các gate; xem LABEL_ADJUDICATION-2026-10-29.md và job_market/datasets/labels/2026-10-29/manifest.json. Phần dưới giữ lịch sử lần nghiệm thu EDA trước sửa audit.

## Lịch sử nghiệm thu EDA

Branch: dev/job-market-ml-from-scratch. Đã triển khai 14/27 ticket trong phạm vi EDA trước; toàn dự án còn chờ ML.

Ứng dụng mới ở job_market, dùng Python/Streamlit và hai nguồn mới. Không import hoặc đọc dataset/model/code cũ. Bộ kiểm tra gần nhất: Ruff và 203 tests qua; có CLI cài từ wheel và kiểm tra browser thực. Xem REVIEW.md và job_market/README.md.

| Công việc | Trạng thái | Bằng chứng / blocker |
| --- | --- | --- |
| [T01](https://github.com/theihoz/ML/issues/15) | Hoàn tất | job_market/docs/tdd/T01.md |
| [T02](https://github.com/theihoz/ML/issues/16) | Hoàn tất | job_market/docs/tdd/T02.md |
| [T03](https://github.com/theihoz/ML/issues/17) | Hoàn tất | job_market/docs/tdd/T03.md |
| [T04](https://github.com/theihoz/ML/issues/18) | Hoàn tất | job_market/docs/tdd/T04.md |
| [T05](https://github.com/theihoz/ML/issues/19) | Hoàn tất | job_market/docs/tdd/T05.md |
| [T06](https://github.com/theihoz/ML/issues/20) | Hoàn tất | job_market/docs/tdd/T06.md |
| [T07](https://github.com/theihoz/ML/issues/21) | Hoàn tất | job_market/docs/tdd/T07.md |
| [T08](https://github.com/theihoz/ML/issues/22) | Hoàn tất | job_market/docs/tdd/T08.md |
| [T09](https://github.com/theihoz/ML/issues/23) | Hoàn tất | job_market/docs/tdd/T09.md |
| [T10](https://github.com/theihoz/ML/issues/24) | Hoàn tất | job_market/docs/tdd/T10.md |
| [T11](https://github.com/theihoz/ML/issues/25) | Hoàn tất | job_market/docs/tdd/T11.md |
| [T12](https://github.com/theihoz/ML/issues/26) | Hoàn tất | job_market/docs/tdd/T12.md |
| [T13](https://github.com/theihoz/ML/issues/27) | Hoàn tất | job_market/docs/tdd/T13.md |
| [T14](https://github.com/theihoz/ML/issues/28) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T15](https://github.com/theihoz/ML/issues/29) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T16](https://github.com/theihoz/ML/issues/30) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T17](https://github.com/theihoz/ML/issues/31) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T18](https://github.com/theihoz/ML/issues/32) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T19](https://github.com/theihoz/ML/issues/33) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T20](https://github.com/theihoz/ML/issues/34) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T21](https://github.com/theihoz/ML/issues/35) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T22](https://github.com/theihoz/ML/issues/36) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T23](https://github.com/theihoz/ML/issues/37) | Hoàn tất | job_market/docs/tdd/T23.md |
| [T24](https://github.com/theihoz/ML/issues/38) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T25](https://github.com/theihoz/ML/issues/39) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T26](https://github.com/theihoz/ML/issues/40) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |
| [T27](https://github.com/theihoz/ML/issues/41) | Bị chặn | Gate nhãn lương/đánh giá/tư vấn hoặc các bước ML phụ thuộc |

## Dữ liệu thực và giới hạn

3.606 dòng thô đối chiếu thành 322 tin EDA, 454 tin review vai trò và 2.830 ngoài bảy nhóm nghề; không có bản sao cùng URL hoặc ID lỗi trong hai file hiện tại. Có nhóm cùng trường quan sát để rà soát/chia tập về sau, không tự gộp các URL khác.

Nhãn VND/tháng đủ chứng cứ: n=0. Gate #42 còn mở; chưa có model, metric, dự đoán hoặc tư vấn dựa trên model. T14–T22, T24–T27 tiếp tục bị chặn. Hai nguồn không đủ cơ sở kết luận xu hướng nhiều năm.

## Cách triển khai và kiểm tra

Ban đầu dùng implementer/merger worktree riêng. Khi agent phụ hết quota, main kiểm kê worktree, tiếp nhận phần chưa commit và tiếp tục trực tiếp; không đổi model hoặc giả vờ đã có review độc lập. Bằng chứng T03/T07 phân biệt code tiếp nhận với vòng đỏ thực quan sát. Các bước còn lại chạy TDD tại seam MarketService đã duyệt, smoke CLI/UI và kiểm tra browser.

GitHub Issues là tracker chính; task-graph.json giữ đối chiếu trạng thái. Triage không áp dụng lại cho ticket đã tạo từ spec. Các file AGENTS, docs/agents và docs/research có sẵn của người dùng được giữ nguyên.

Đã đọc lại trạng thái GitHub: 14 ticket và F01/F02 đóng; spec tổng thể #6, gate #42 và các quyết định #4/#5 còn mở. Triage không có issue mới needs-triage. CI của code commit 4bff8f7 thành công: https://github.com/theihoz/ML/actions/runs/40828270329 . Worktree triển khai đã dọn sau khi xác minh merge/sạch.


# Sửa audit EDA trước ML

Baseline cố định: main tại 9ce05066cab052129405d73ac4a37cf6fa01b429. Nhánh làm việc local: dev/ml-development. Các commit code: 5776d94, 00ed6b0 và 1b15a01. Dùng git diff main...HEAD; chưa push hoặc thay main, chưa sửa tracker/gate.

## Phạm vi và bằng chứng

| Audit | Kết quả sửa | Test hành vi |
| --- | --- | --- |
| A01/A02 | Không nhân scale vào đầu khoảng đã viết đầy đủ; giữ shared suffix dạng thường/nhóm số; nhận đ sát số | test_audit_salary.py |
| A03 | Giữ query định danh/chưa rõ; bỏ tracking chỉ định, riêng TopCV theo hostname | test_audit_identity.py |
| A04/A05 | QA thủ công không thành Mobile developer; nghề Backend không bị loại bởi lĩnh vực sản phẩm | test_audit_roles.py |
| A06/A07 | Trang địa điểm dùng chuẩn hóa chung; Remote là bằng chứng hình thức, không phải remote sensing/RPC | test_audit_work_modes.py |
| A08 | Giữ bằng chứng bổ sung và raw rows; cách ly mâu thuẫn; nhóm/reasons không tùy dòng đầu; giữ ranh giới JD | test_audit_identity.py |
| A09 | CSV/PNG có nguồn/revision/kỳ quan sát/bộ lọc/n/đơn vị; CSV rỗng có record_type=metadata | test_audit_exports.py |

Các test trên ở job_market/tests; ghi chép vòng đỏ/xanh trong job_market/docs/tdd/audit-normalization.md, audit-roles.md và audit-exports.md. Các chuỗi tổng hợp chỉ kiểm logic, không đi vào dữ liệu thị trường hoặc training.

## Standards

Agent Standards phát hiện hai vấn đề ở commit đầu: shared suffix bốn chữ số bị mất và entity còn review_reasons của dòng thiếu bằng chứng. Đã tái hiện đỏ, sửa và kiểm tra lại độc lập tại 00ed6b0: không còn vi phạm chuẩn có thể hành động trong phạm vi đó; không có smell cần thêm abstraction. Ghi nhận này giữ riêng trục Standards, không gộp hoặc xếp hạng lại với Spec.

## Spec

Agent Spec phát hiện sáu trường hợp ở commit đầu: suffix, bổ sung nghề bị coi mâu thuẫn, company phụ thuộc thứ tự, Engineer in Test bị coi Mobile, Customer Service Platform bị loại và RPC bị gán Remote. Sau sửa, review tiếp phát hiện hai biến thể còn lại: grouped suffix và ghép JD làm heading Requirements che nhiệm vụ của quan sát khác. Cả hai đã có vòng đỏ/xanh và sửa tại 1b15a01. Kết quả xác nhận cuối được ghi khi reviewer hoàn tất; không coi suite xanh là tự thay review.

Xác nhận cuối tại 1b15a01: agent Spec kiểm lại cả tám reproducer và tích hợp liên quan, tất cả đã đóng; 34 focused tests qua (deselect một test dữ liệu thật trong lượt focused). Không còn phát hiện cần sửa trong phạm vi này. Main sau đó chạy đầy đủ **246 tests passed in 49.51s**, Ruff check và format check đều qua. Đây là kiểm tra local; chưa chạy hosted CI cho các commit chưa push.

Kết quả cuối theo trục: Standards 0 phát hiện cần sửa còn lại trong phạm vi review; Spec 0 phát hiện cần sửa còn lại trong phạm vi review.

## Snapshot và dữ liệu

Snapshot hiện tại eda-v5: 1ccf26a791b6875eaf5a789d45aca30dc0bb18414e866ef132798735e70382e5. Raw không thay đổi: 3.606 dòng = 320 EDA + 556 role_review + 2.730 out_of_scope; 0 duplicate, 0 ID lỗi, 0 target. Hai title QA thủ công giải thích mức giảm 322 → 320; TopCV 295 → 293. Không coi toàn bộ 320 tin là đã được review thủ công.

Snapshot đã được tạo lại trong datasets/processed; file này bị ignore và tái tạo bằng CLI chuẩn bị dữ liệu. Trình duyệt thực đã kiểm dashboard 293/124/0 và bộ lọc Remote trang Địa điểm: TopCV 1.550 raw, 5 tin Remote. Năm tin này thuộc raw, không phải năm tin trong EDA. Đã xem PNG mới n=293 có footnote đầy đủ sau khi đợi lệnh sinh file hoàn tất.

## ML và quyết định người dùng

ADR 0006 ghi lựa chọn giữ unknown gross/net riêng, không trộn gross/net. Nghiên cứu nhãn trong docs/rebuild/ml/LABEL_RESEARCH-2026-10-29.md tìm được ứng viên cùng tin và nguồn mới; chưa nhập canonical hoặc tự nhận là nhãn được chấp nhận. Main kiểm lại hash/số dòng hai CSV mới và câu kỳ lương Jaxtina. ML vẫn chưa fit, không có model/metric/dự đoán mới. Gate #42 và phần còn lại của #4/#5 giữ nguyên.

S01 trong audit gốc là nhận định thiết kế về phép chiếu nguồn, chưa triển khai refactor. Heuristic nghề/Remote, reconciliation bảo thủ và nhóm repost theo trường quan sát vẫn có giới hạn; không chứng nhận mọi cách viết tin tự do hoặc chống near-duplicate ML đã hoàn tất.

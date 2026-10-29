# Sửa chuẩn hóa trước ML — 29/10/2026

Seam được kiểm tra: MarketService, CLI và Streamlit đã được duyệt trước đó. Fixture chỉ kiểm logic, không đưa vào dataset hoặc training. Không thay raw/catalog, không tự mở gate #42.

## Vòng đỏ → xanh

- A01: `tests/test_audit_salary.py` có 4 case notation trộn, cả bốn đỏ. Case `20 triệu - 30.000.000 VND/tháng` cho upper 30.000.000.000.000. Đối chứng hai số riêng lẻ và khoảng viết tắt đều đúng, xác định nguyên nhân kế thừa suffix chứ không phải dấu nhóm số hoặc tiền tệ. Chỉ số viết tắt mới kế thừa scale; chạy cùng test lương cũ: 17 passed.
- A02: thêm `test_adjacent_dong_symbol_is_currency_evidence`, đỏ vì currency/target đều null. Cho phép ký hiệu đ sát chữ số; 18 case lương mới+cũ qua.
- A03: `test_identity_query_separates_distinct_jobs_but_tracking_does_not` đỏ với 1 tin/2 duplicate thay vì 2/1. Giữ query chưa rõ, chỉ bỏ UTM/click tracking được chỉ định; thêm vòng đỏ → xanh cho tracking TopCV ta_source/u_sr_id theo hostname. Các fixture cũ dùng query a/q không có chứng cứ tracking đã đổi sang utm_source; không giữ giả định bỏ mọi query.
- A08: test bằng chứng HCM/Java và HN/Python cùng ID đỏ vì chỉ giữ HCM. Hợp nhất địa điểm/kỹ năng tương thích, giữ từng raw và evidence_row_ids. Test đảo thứ tự, thiếu nhãn ở một bản ghi, mâu thuẫn lương và nhóm repost bảo vệ provenance. Test nhóm đầu tiên đỏ vì hai bản bổ sung không chung group; sau sửa, group được tính từ bằng chứng hợp nhất. Mâu thuẫn lương/nghề/ngày/công ty/tiêu đề/kinh nghiệm cách ly entity_review, không vào EDA/targets.
- A07: `test_remote_sensing_is_not_a_remote_work_arrangement` đỏ vì gán Remote. Loại ngữ cảnh remote sensing và phủ định Remote; bằng chứng location vẫn giữ độc lập.
- A06: test đối chiếu location_report với canonical raw rows đỏ vì report trả 0 thay vì 5 ID Remote. Report dùng chuẩn hóa từ preparation, giữ raw alias counts và bộ lọc; 32 tests địa điểm/Remote qua.

Lệnh tập trung từ job_market:

```sh
.venv/bin/python -m pytest tests/test_audit_salary.py tests/test_audit_identity.py tests/test_audit_work_modes.py -q
```

A04/A05 và A09 có ghi chép riêng trong audit-roles.md và audit-exports.md. Test export đã chuyển vào job_market/tests để bộ CI hiện có thực sự chạy chúng; các lệnh lịch sử trong ghi chép của agent phản ánh vị trí trước khi tích hợp.

## Kiểm tra tích hợp

- Full suite sau tích hợp: **235 passed in 49.07s**; Ruff check và format check qua. Hai assertion UI cập nhật sau khi đối chiếu đúng hai title QA thủ công mất nhãn Mobile, không xóa test lỗi.
- `rules_version=eda-v3`. Đã xuất lại datasets/processed bằng service: snapshot `1668971031f38427c461a2cccc7981ed9ee035ffeda589f5faabb777b4f458e1`.
- Raw 3.606 = 320 EDA + 556 role_review + 2.730 out_of_scope; duplicate và invalid_identity đều 0. Salary targets vẫn 0. Không coi đây là kiểm toán thủ công mọi title hoặc bằng chứng đủ nhãn train.
- Kiểm browser thực: dashboard TopCV hiện 293 tin, 124 có kỹ năng, 0 nhãn; caption có revision và kỳ 2025-12-18–2026-01-15. Trang Địa điểm đọc dữ liệu chuẩn chung. Kiểm tra CLI/service: 5 tin Remote trên toàn bộ raw TopCV; không nhầm chúng với tập EDA.

## Giới hạn

Reconciliation bảo thủ: khác câu lương có thể cần review dù hai cách viết tương đương; không tự giải quyết các phiên bản tin có nội dung xung đột. Nhóm repost chỉ dựa trường quan sát, chưa là thuật toán near-duplicate hoàn chỉnh cho ML. Chuẩn hóa nghề/Remote là quy tắc có bằng chứng và cần tiếp tục review trường hợp tự do. Gate dữ liệu và quyết định đánh giá/tư vấn vẫn chưa đóng.

## Follow-up từ review độc lập

Hai lượt review phát hiện biến thể chưa được các test đầu khóa: shared suffix bốn chữ số/nhóm nghìn, stale review_reasons, role/company được bổ sung ở bản ghi khác, Mobile Engineer in Test, Customer Service Platform, Remote Procedure Call và section Requirements trong một JD che nhiệm vụ ở JD khác khi ghép chuỗi. Mỗi trường hợp được tái hiện bằng test đỏ tại seam service rồi sửa; bổ sung test invalid_identity ở dòng đầu giữ schema group cho export. Entity giữ role evidence của từng quan sát đã phân giải độc lập thay vì nối JD qua ranh giới section.

Snapshot cuối dùng eda-v5, ID 1ccf26a791b6875eaf5a789d45aca30dc0bb18414e866ef132798735e70382e5; số partition/target không đổi so với lần tạo v3 nêu trên. Kết quả tổng hợp và giới hạn nằm trong docs/rebuild/FIX_REVIEW-2026-10-29.md.

Bộ kiểm tra cuối trên code 1b15a01: 246 passed in 49.51s; Ruff check và format check toàn job_market qua. Hai reviewer xác nhận lại các phát hiện đã sửa ở phạm vi tương ứng. Không push hoặc chạy hosted CI trong lượt này.

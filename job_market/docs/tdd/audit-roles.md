# A04/A05 — phân nhóm vai trò

Ngày 29/10/2026, branch `dev/ml-development`. Phạm vi sửa chỉ gồm `roles.py`,
`tests/test_audit_roles.py` và ghi chép này. Đọc AGENTS, GLOSSARY, năm ADR cùng
`docs/rebuild/AUDIT-2026-10-29.md`; kiểm thử qua seam đã được yêu cầu là
`MarketService.classify_role`, không mock hàm nội bộ.

## Đỏ rồi xanh

Tất cả lệnh dưới đây chạy từ `job_market`, bằng `.venv` của thư mục này.

1. Thêm test A04 với nguyên tiêu đề Mobile Game Tester (QA) trong audit.
   `PYTHONPATH=src .venv/bin/pytest -q tests/test_audit_roles.py` trả **1 failed**:
   thực tế `(Mobile, matched)`, kỳ vọng `(None, review)`. Chỉ sau vòng đỏ mới
   sửa quy tắc để nền tảng trong chức danh kiểm thử không thành nghề Mobile.
   Chạy lại trả **1 passed**.
2. Thêm test A05 với `Backend Developer - Marketing Platform`. Cùng lệnh trả
   **1 failed, 1 passed**: thực tế `(None, out_of_scope)`, kỳ vọng
   `(Backend, matched)`. Sau đó cho phép lĩnh vực sản phẩm xuất hiện sau một
   nghề phần mềm rõ ràng; vẫn loại PLC, hardware và các nghề ngoài phạm vi.
   Bộ mới cùng `tests/test_roles.py` trả **50 passed**.
3. Bổ sung các ca bảo vệ manual QA, QA Automation, yêu cầu kỹ năng, lĩnh vực
   Sales/Marketing và chức danh đa nghề. Chạy file audit trả **1 failed,
   11 passed**: guard QA ban đầu làm `Mobile Developer / QA Automation Engineer`
   thành QA Automation. Giới hạn guard khi Mobile chỉ là nền tảng, giữ bằng
   chứng Mobile Developer/Engineer rõ ràng để chức danh đa nghề tiếp tục review.
   `PYTHONPATH=src .venv/bin/pytest -q tests/test_audit_roles.py tests/test_roles.py`
   trả **60 passed** (12 ca audit và 48 ca cũ, gồm Streamlit AppTest trang Vai trò).

`.venv/bin/ruff check src/career_market/roles.py tests/test_audit_roles.py` qua;
`.venv/bin/ruff format --check src/career_market/roles.py tests/test_audit_roles.py`
qua sau khi định dạng file test mới. Diff file triển khai không có lỗi whitespace.

Chạy tích hợp một lần bằng `PYTHONPATH=src .venv/bin/pytest -q`:
**219 passed, 3 failed in 39.06s** trên checkout dùng chung đang được sửa đồng thời:

- `test_demand.py::test_dashboard_filters_real_postings_and_exposes_csv_and_png_exports`:
  metric thực tế 293, assertion cũ 295.
- `test_preparation.py::test_quality_page_shows_real_reconciliation_and_blocked_ml`:
  EDA thực tế 320, assertion cũ 322.
- `test_audit_identity.py::test_duplicate_evidence_survives_input_order_and_retains_raw_rows`:
  hợp nhất địa điểm trả HCM thay vì HCM/HN; thuộc phần identity/preparation ngoài phạm vi.

Đối chiếu chỉ đọc các title từ nguồn đã duyệt, so hàm tại HEAD với hàm đang sửa,
xác nhận đúng hai tin mất nhãn Mobile matched: tiêu đề A04 và
`Kiểm Thử Viên Chất Lượng (QA Tester) - Chuyên Về Mobile & Web`. Cả hai nay review,
phù hợp mức giảm hai tin trong các assertion UI. Các title QA/Tester khác trước đó
out_of_scope có thể chuyển sang review, nhưng không được đưa vào EDA hay gán
QA Automation. Không đổi assertion đếm hoặc file identity của agent khác để làm suite xanh.

## Hành vi và giới hạn

Manual QA hoặc Tester thiếu bằng chứng automation được giữ ở review. Từ
Automation trong requirements không tự tạo nghề QA Automation. QA Automation
rõ ràng trên nền tảng Mobile vẫn nhận QA Automation; Mobile Developer giao với
QA Automation vẫn review. Backend Developer cho Marketing/Sales Platform giữ
nghề Backend và bằng chứng title nguyên văn. Các kiểm thử vai trò cũ tiếp tục qua.

Đây là sửa heuristic cho A04/A05, không phải kiểm toán toàn bộ nghề trong dữ liệu.
Ngoài tiêu đề A04 được trích từ audit, các chuỗi kiểm thử là fixture kiểm tra logic;
không tạo dữ liệu thị trường, target hoặc model. Chưa chứng minh mọi cách viết chức
danh tự do đều được phân giải. Không thay dataset, tracker, commit hay push; các
thay đổi ngoài ba file được giao thuộc phiên làm việc đồng thời và không bị hoàn tác.

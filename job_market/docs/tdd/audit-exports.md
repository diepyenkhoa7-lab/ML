# A09 — provenance trong export nhu cầu kỹ năng

Khi tích hợp, test và tài liệu được chuyển vào job_market/tests/test_audit_exports.py và job_market/docs/tdd/audit-exports.md để CI hiện có thu thập. Từ job_market, chạy `.venv/bin/python -m pytest tests/test_audit_exports.py -q`; các đường dẫn bên dưới giữ lịch sử lần chạy của agent trước khi chuyển.

Phạm vi: `MarketService.skill_demand` và bytes CSV/PNG trả về. Chỉ sửa
`job_market/src/career_market/analysis.py`, `tests/test_audit_exports.py` và tài liệu này.
Giữ chữ ký service, các khóa kết quả và cấu trúc `table` hiện có. Không sửa service,
dataset, tracker; không commit/push. Đọc AGENTS, GLOSSARY, ADR 0001–0005 và
`docs/rebuild/AUDIT-2026-10-29.md` trước khi triển khai.

## Hợp đồng artifact

- CSV giữ bốn cột thống kê cũ, thêm `record_type` và `export_metadata` (JSON).
  Mỗi dòng kỹ năng có metadata độc lập, không cần UI hoặc file bên cạnh để hiểu phạm vi.
- Nếu bảng kỹ năng rỗng, CSV vẫn có một dòng `record_type=metadata`, tên kỹ năng và
  số tin nhắc kỹ năng để trống. `sample_size` giữ đúng n, kể cả khi n > 0 nhưng không
  có bằng chứng kỹ năng. Người đọc CSV chỉ lấy `record_type=skill` để phân tích kỹ năng.
- Metadata chứa catalog nguồn đã duyệt (ID, revision, URL, giấy phép, checksum và
  attribution), kỳ quan sát tổng và riêng từng nguồn, số ngày đăng thiếu, bộ lọc role/
  locations/work_mode/source_ids/limit, n và đơn vị đếm/tỷ lệ.
- Revision lấy từ catalog `sources.json` cùng package, không suy từ tên dataset.
  Với source ID không có trong catalog, revision là null/chưa rõ; giữ tương thích
  caller cũ và không gán revision của nguồn khác.
- Kỳ quan sát chỉ dùng ngày ISO hợp lệ có `date_kind=posting` của các tin sau lọc
  và khử trùng theo seam hiện có. Không thay bằng ngày tải, imported_on, deadline hoặc
  năm trong tên nguồn. Ngày thiếu/không hợp lệ được ghi nhận; không có ngày thì null.
- PNG có footnote nhìn thấy được: từng nguồn/revision/kỳ quan sát, phạm vi ngày đăng
  chung, số thiếu ngày, toàn bộ bộ lọc, Top, n và đơn vị. Chừa chiều cao theo số dòng
  footnote. PNG cũng lưu cùng nội dung trong trường Description để đọc lại tự động.
  Kỳ quan sát là độ phủ ngày đăng, không phải bằng chứng lấy mẫu liên tục hoặc xu hướng.
- Không cần thêm download hay sidecar: bytes CSV/PNG mà caller đang tải đã tự chứa
  provenance. Không đổi phép đếm hoặc cấu trúc bảng đang hiển thị.

## Red → green từng lát

| Lát | Test | Red thực tế | Green |
| --- | --- | --- | --- |
| CSV có dữ liệu | `test_skill_demand_csv_retains_source_revision_period_filters_and_units` | `KeyError: export_metadata` | Thêm cột JSON chứa provenance trên từng dòng; 1 passed |
| PNG | `test_skill_demand_png_carries_its_visible_provenance_footnote` | Description rỗng, không có `jobs-2026 (revision 1)` | Footnote có revision/ngày/bộ lọc/n/đơn vị và Description cùng nội dung; 2 passed |
| Bảng rỗng | `test_empty_demand_exports_retain_requested_source_and_scope` | CSV chỉ header, 0 dòng thay vì 1 | Dòng metadata giữ nguồn yêu cầu, revision, n=0 và ngày chưa rõ; 3 passed |
| Nhiều nguồn | `test_mixed_source_exports_keep_each_sources_observed_period` | `KeyError: observed_period` trong metadata riêng từng nguồn | CSV và footnote gắn kỳ riêng với từng nguồn/revision; 4 passed |

Sau bốn lát, bổ sung kiểm tra hồi quy (đều xanh ngay, không tuyên bố là lát red–green):

- `test_undated_exports_never_substitute_import_year_or_deadline`: ba case ngày thiếu,
  ngày không hợp lệ và deadline. Dùng bản sao có kiểm soát của một tin nguồn mới,
  không ghi ngược dataset hoặc xem những biến thể này là quan sát thị trường thật.
- `test_postings_without_skills_still_export_their_nonzero_sample`: sao chép một tin
  nguồn mới, bỏ kỹ năng để kiểm n=1 trong dòng metadata khi bảng rỗng.

Fixture chính đọc qua `MarketService.prepare()` từ hai nguồn mới đã duyệt:
CareerBuilder `jobs-2023` revision 2 và TopCV `jobs-2026` revision 1. Không dùng dữ liệu
cũ của ứng dụng trước. Kỳ Backend tại HCM/HN đối chiếu bằng literal đã đọc từ nguồn:
2023-02-16–2023-02-21 và 2025-12-18–2026-01-15; không khóa n vào số đếm nghề có thể
thay đổi khi agent khác sửa phân loại.

## Kiểm chứng

Chạy từ repository root:

```sh
MPLCONFIGDIR=/tmp/ml-a09-mpl PYTHONPATH=job_market/src job_market/.venv/bin/python -m pytest tests/test_audit_exports.py job_market/tests/test_demand.py::test_demand_filters_distinct_postings_and_exports_matching_chart_and_table -q
job_market/.venv/bin/ruff check job_market/src/career_market/analysis.py tests/test_audit_exports.py
job_market/.venv/bin/ruff format --check job_market/src/career_market/analysis.py tests/test_audit_exports.py
git diff --check -- job_market/src/career_market/analysis.py
```

Kết quả: 9 passed (8 case export + 1 hợp đồng demand có sẵn); Ruff sạch.
Đã mở và xem PNG xuất thực tế cho Backend/HCM/HN gồm hai nguồn và trường hợp n=0:
footnote hiển thị đủ nội dung, không đè biểu đồ hoặc cắt chữ. Kiểm thử PNG đọc
Description, không OCR; kiểm chứng hiển thị là bước xem ảnh riêng. Không chạy toàn
bộ suite hay nhận định về UI đang được sửa đồng thời.

# T10: Chuẩn hóa số năm và khoảng kinh nghiệm

Trạng thái: đã triển khai và kiểm tra trong đợt EDA ngày 29/10/2026. [GitHub Issue](https://github.com/theihoz/ML/issues/24). Bằng chứng: job_market/docs/tdd/T10.md. ML giữ gate riêng theo EDA_FIRST.md.

## What to build

Người dùng xem kinh nghiệm đã chuẩn hóa, khoảng/cận hoặc trạng thái thiếu, và lọc/xuất để rà soát.

## Công việc

- [x] Phân tích kinh nghiệm dạng số, khoảng, cận và không yêu cầu.
- [x] Giữ min/max/kind, phân biệt thiếu với không yêu cầu kinh nghiệm.
- [x] Thêm đối chiếu UI/export và kiểm tra các định dạng thực.

## Acceptance criteria

- [x] Thiếu kinh nghiệm không bị gán 0.
- [x] Khoảng/cận và bằng chứng raw được giữ.
- [x] Giá trị bất hợp lý có trạng thái/lý do review, không tự sửa không dấu vết.

## Blocked by

- T01 — Nhập một nguồn mới và xem dữ liệu gốc

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.

## Hợp đồng triển khai T10

`MarketService.normalize_experience(raw)` trả dictionary có đúng năm khóa:

| Khóa | Ý nghĩa |
| --- | --- |
| `experience_min` | Cận dưới theo năm, `float` hoặc `None`. |
| `experience_max` | Cận trên theo năm, `float` hoặc `None`. |
| `experience_kind` | `exact`, `range`, `greater_than`, `less_than`, `at_least`, `at_most`, `no_experience`, `missing` hoặc `unknown`. |
| `experience_status` | `ok`, `missing` hoặc `review`. |
| `experience_reason` | `None` khi hợp lệ; mã lý do khi thiếu hoặc cần rà soát. |

Số đơn lẻ mặc định là năm; số thập phân dùng dấu chấm hoặc phẩy. Tháng chia 12,
giữ số thực, không làm tròn thành năm nguyên. Khoảng giữ hai cận, không tính
trung điểm. `Trên`/`Dưới` là cận mở (`greater_than`/`less_than`); `Từ` hoặc dấu `+`
là `at_least`, `Tối đa` là `at_most`. Cận chưa biết luôn là `None`, không tự gán 0
hoặc 60. Khoảng cho phép dấu gạch nối, gạch ngang hoặc `từ … đến …`; một đơn vị
ghi ở một đầu áp dụng cho đầu chưa ghi đơn vị. Hai đầu có đơn vị riêng được
chuyển đổi độc lập.

`None`, NaN dạng số, chuỗi rỗng/chỉ có khoảng trắng và các dấu thiếu `N/A`, `NA`,
`null`, `None`, `NaN` có trạng thái/kind `missing`, lý do `missing_experience`.
Các nhãn rõ nghĩa `Chưa có kinh nghiệm`, `Không yêu cầu kinh nghiệm`,
`Không yêu cầu`, `Không có kinh nghiệm` có hai cận `0.0`, kind `no_experience`.
Số 0 ghi trực tiếp vẫn là `exact`; không suy 0 từ cấp bậc hoặc nhãn tốt nghiệp.

Giá trị âm, đảo cận hoặc vượt 60 năm có trạng thái `review`, hai cận sạch là
`None`, giữ kind đã phân tích; các lý do tương ứng là `negative_experience`,
`inverted_experience_range`, `experience_over_60_years`. Chuỗi sai định dạng hoặc
cấp bậc (`Nhân viên`, `Senior`, `Mới tốt nghiệp`…) có kind `unknown`, trạng thái
`review`, lý do `unrecognized_experience`. Không trích số tùy tiện từ chuỗi lỗi.

`MarketService.experience_report(source_id, status=None, kind=None)` trả dictionary:

- `rows`: danh sách dictionary gồm `source_id`, `job_id`, `job_url`,
  `experience_raw` nguyên văn và năm khóa chuẩn hóa ở trên.
- `total_count`: số dòng của nguồn đã kiểm schema/checksum, trước lọc.
- `filtered_count`: số dòng thỏa đồng thời bộ lọc trạng thái và kind.
- `csv`: chuỗi CSV của chính các dòng đang lọc, có header cả khi không có dòng;
  `None` được xuất thành ô rỗng. Bộ lọc dùng giá trị chính xác của hợp đồng trên;
  `None` nghĩa là tất cả.

Nguồn 2023 dùng cột `exp`, nguồn 2026 dùng `experience`; report không sửa raw,
ID hoặc URL. Đây là đối chiếu số dòng thô trước lọc nghề/khử trùng, không phải
thống kê thị trường. Page độc lập: `job_market/pages/6_Kinh_nghiem.py`, mở từ
sidebar của app hoặc chạy trực tiếp bằng Streamlit. Page gọi MarketService,
lọc trạng thái/kind và xuất CSV UTF-8 BOM để đọc tiếng Việt. Không huấn luyện,
không tạo target hay đọc mã/dữ liệu/model cũ. Bằng chứng tại
`job_market/docs/tdd/T10.md`.


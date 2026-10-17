# Làm sạch dữ liệu — phiên bản 1.0.0

Pipeline áp dụng quy tắc lên bốn nguồn thật, giữ nguyên `data/raw/` và kiểm tra
SHA-256 trước/sau. Đây là bản chuẩn hóa tự động có nhật ký; phân loại nghề bằng
regex và nhãn nguồn vẫn có thể sai, chưa phải dữ liệu đã được con người gán nhãn lại.

## Chạy lại

```bash
make test-data
make data-clean
make lint
# Chạy một nguồn khi sửa quy tắc:
.venv/bin/python scripts/clean_data.py --source user_vietnam_it_jobs
```

Mã xử lý ở `scripts/data_cleaning.py`; công cụ xuất file ở `scripts/clean_data.py`;
chính sách ở `configs/cleaning.json`. Ngày chặn dữ liệu tương lai cố định là
17/10/2026 theo giờ Việt Nam. Khi đổi quy tắc, đổi version/chính sách và chạy lại
cả bốn nguồn để bản tổng hợp thống nhất. Báo cáo một nguồn không ghi đè báo cáo
`all_sources`. Các CSV nhãn cũ do lần chạy trước quản lý được xóa nếu không còn
thuộc kết quả mới; không xóa file raw hoặc các bản `source_views`.

## Đầu ra

Mỗi nguồn có thư mục `data/processed/cleaned/<source_id>/`:

| File | Ý nghĩa |
|---|---|
| `clean.csv` | Dòng trong phạm vi CNTT được quy tắc chấp nhận; có thể thiếu lương/kinh nghiệm/kỹ năng |
| `review.csv` | Dòng chưa rõ nghề, đơn vị lương, ngoại lệ, ngày sai hoặc xuất xứ cần xác minh |
| `audit.csv` | Một dòng cho mỗi dòng raw, có chỉ số hàng gốc, quyết định và lý do |
| `labels/*.csv` | Chỉ các dòng clean có nhãn số hợp lệ; tách tiền tệ, gross/net và nguồn |
| `manifest.json` | Số dòng, thống kê, checksum đầu vào và từng file đầu ra |

`source_row_index` tính từ 0, không tính header CSV. `record_id` là ID nguồn hoặc
chỉ số hàng trong snapshot cố định. `group_id` dùng URL chuẩn hóa, hoặc chức danh +
địa điểm + mô tả khi nguồn không có URL; thiếu cả mô tả thì chỉ dùng ID nguồn.

`outputs/data_quality/cleaning/all_sources.csv` là bảng đếm ngắn;
`all_sources.json` chứa chính sách, hash code, hash dữ liệu và chi tiết từng nguồn.
Một dòng có thể có nhiều lý do review nên không cộng các lý do để tính số dòng.

## Quy tắc

1. **Chuỗi:** chuẩn Unicode NFC và khoảng trắng; giữ cột raw để đối chiếu.
   Kỹ năng đọc bằng JSON/literal an toàn, chuẩn alias (`JS` → `JavaScript`,
   `NodeJS` → `Node.js`…), loại lặp. Phân biệt Java/JavaScript, C/C++/C#.
   Không dùng LLM sinh thêm kỹ năng thiếu.
2. **Trùng:** VietJobs bỏ dòng trùng hoàn toàn; khảo sát bỏ `ResponseId` lặp;
   nguồn tuyển dụng có URL bỏ bản lặp URL, giữ bản cập nhật gần nhất, hòa thì giữ
   dòng cuối. URL bỏ fragment, dấu `/` cuối và tham số `utm_*`.
3. **Nghề:** chuẩn hóa vai trò từ chức danh; lọc rõ nghề ngoài phạm vi. Những
   chức danh không đủ rõ chuyển review. CNC/CAM, bán hàng phần mềm và QC ngành gỗ
   không coi là lập trình viên. Không loại tin chỉ vì có tiền tố “tuyển dụng”.
   DataForge là corpus toàn ngành: các nghề QA/support/management/BA/design còn
   cần dấu hiệu CNTT trong chức danh, department hoặc kỹ năng; nếu thiếu thì review.
   Tin có dấu `/` và nhiều tên vai trò rõ ràng được chuyển review thay vì gán chung
   một mức lương cho một vai trò. Quy tắc này có thể bắt cả vị trí kết hợp hợp lệ.
4. **Địa điểm:** chuẩn Hà Nội, TP.HCM, Đà Nẵng và giữ nhiều địa điểm; giữ địa danh
   khác dưới dạng nguồn. Remote nhận từ chuỗi địa điểm và cờ nguồn DataForge.
   Quốc gia trống của file Việt Nam chỉ được gán Vietnam nếu không có dấu hiệu
   quốc tế/nước ngoài; chưa chuẩn hóa đầy đủ tên/ISO của mọi quốc gia.
5. **Kinh nghiệm:** đổi tháng thành năm; thiếu giữ null; “không yêu cầu” mới là 0.
   Khoảng `2–4 năm` giữ cả hai đầu, cột đại diện là cận dưới 2 và ghi
   `experience_kind=range_lower_bound`; không diễn giải là số năm chính xác.
   “Dưới 1 năm” chỉ có cận trên, không gán thành 0. Trên 80 năm chuyển review.
6. **Lương:** đọc riêng số tiền, tiền tệ, kỳ lương, gross/net và trạng thái.
   Chuỗi `9.4 - 12.0 triệu` được giữ phần thập phân. Riêng VietJobs dùng quy ước
   triệu VND/tháng đã công bố trong nguồn; sửa cột số bị làm tròn theo chuỗi và
   đánh dấu `salary_text_corrected_numeric`, giữ cột số nguồn để kiểm tra.
   Với file người dùng, thiếu kỳ lương hoặc chỉ có `$` thì review, không đoán USD
   hay tháng. `$18tr–22tr` là mâu thuẫn tiền tệ, không tạo nhãn.
7. **Nhãn:** khoảng đủ hai đầu hợp lệ lấy trung điểm; lương năm chia 12 khi xuất
   lương tháng **cùng tiền tệ**. Không có tỷ giá nên không đổi USD thành VND.
   Lương giờ/ngày/tuần giữ nguyên kỳ và không tự nhân số giờ làm việc.
   “Từ/tới” một đầu giữ cận nhưng không tạo nhãn điểm. Thỏa thuận, thiếu hoặc
   `0.0 triệu` không biến thành lương 0.
8. **Rà soát ngoại lệ:** lương tháng VND ngoài 1–500 triệu, USD ngoài 100–100.000;
   USD/năm ngoài 1.000–1.000.000, lương năm của tiền tệ khác dưới 1.000 đơn vị
   nguồn đều chuyển review. VND/năm dùng giới hạn tháng ×12. Đây là ngưỡng kiểm tra
   thô trong config, có thể loại cả trường hợp hợp lệ; không phải kết luận về mặt
   bằng thị trường. Không winsorize, không tự nhân 1.000 khi thấy thiếu scale,
   không học phân vị từ toàn bộ dữ liệu. Mức cao/thấp ở các tiền tệ khác vẫn cần
   kiểm tra theo thị trường trước khi huấn luyện.
9. **Ngày và xuất xứ:** ngày lỗi/tương lai chuyển review; không sinh ngày cho
   nguồn thiếu ngày. Riêng 3.200 dòng file người dùng có crawl trước 2026 được
   cách ly vì mẫu phân bố lịch sử cần xác minh; không khẳng định đó là dữ liệu giả.

## Dùng nhãn đúng mục tiêu

- File người dùng và VietJobs: `labels/VND_month_unknown.csv` chứa
  `salary_monthly_vnd`, là trung điểm lương chào tuyển, chưa rõ gross/net.
  Các currency/basis khác xuất file riêng nếu có mẫu hợp lệ.
- DataForge: `labels/<currency>_month_<basis>.csv`, đa số là quốc tế, không có
  kinh nghiệm dạng số. Cột `salary_monthly_native` mang tiền tệ trong tên file.
  Không gộp các CSV khác tiền tệ để hồi quy chung một nhãn.
- Stack Overflow: `labels/USD_year_gross.csv` chứa `compensation_annual_usd`;
  chỉ lấy người chọn “I am a developer by profession”. Đây là tổng thu nhập
  trước thuế do người trả lời khai báo và nguồn quy đổi USD/năm, bao gồm các khoản
  ngoài lương, không trộn với lương chào tuyển. Kinh nghiệm là `WorkExp`.

Các file nhãn chỉ xuất whitelist features ghi trong báo cáo JSON. ID nguồn/nhóm/
chỉ số hàng là metadata cho join/chia tập, **không đưa vào model**. Features không
chứa `salary_min/max`, chuỗi salary, tiêu đề hoặc mô tả có thể chứa lương.
`skills` và `skills_json` biểu diễn cùng một danh sách; chọn một để vector hóa.

Bước làm sạch này không chia train/validation/test hoặc điền dữ liệu thiếu.
Bước tiếp theo đã tạo bộ chia v1.0.1, xem [nhãn và tập huấn luyện](LABEL_REVIEW_AND_SPLITS.md).
Trước khi mở rộng hoặc thay bộ train cần chốt
vai trò lập trình viên hay CNTT rộng, rà soát mẫu nhãn theo từng nguồn và nhóm
tin gần trùng giữa các nguồn. Hiện chỉ khử trùng theo danh tính/đúng toàn dòng;
`group_id` chưa bảo đảm phát hiện tin đăng lại có nội dung thay đổi hoặc VietJobs
trùng nguồn khác mà không có URL. Fit imputer/encoder/scaler trên train; không
dùng thời điểm crawl thay ngày đăng để kết luận xu hướng tuyển dụng.

Giới hạn nguồn vẫn giữ nguyên: VietJobs là dữ liệu 2025 dù công bố 2026; khảo sát
không đo nhu cầu tuyển dụng; DataForge thiếu toàn văn và còn mâu thuẫn điều khoản
giữa trang nguồn/gói ZIP; file người dùng chưa có link gốc. Chi tiết trong
[hồ sơ nguồn](DATA_SOURCES.md). Không tạo nhãn SFT hoặc huấn luyện Gemma trong bước này.

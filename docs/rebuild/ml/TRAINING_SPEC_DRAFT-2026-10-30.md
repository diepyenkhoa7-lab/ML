# Spec triển khai huấn luyện ML

Ngày: 30/10/2026. Trạng thái: bản nháp tổng hợp để triển khai sau khi đủ dữ liệu và khóa policy. Tài liệu này không mở gate huấn luyện, không thay đổi các quyết định đã duyệt trong M01–M08 hoặc trạng thái GitHub Issues.

## Problem Statement

Ứng dụng cần hai mô hình tự huấn luyện dự đoán lương chào tuyển từ hồ sơ nghề nghiệp, có đánh giá trên công ty chưa xuất hiện trong train. Metric phải truy được về nhãn thật, phân hoạch và cấu hình; số lượng tin dùng cho EDA không đồng nghĩa số nhãn đủ điều kiện train.

## Solution

Một quy trình Python chạy ngoại tuyến: kiểm readiness → khóa snapshot/cohort → chia train/validation/test theo nhóm công ty → fit preprocessing trên train → fit Ridge và Linear Regression → chọn bằng validation → đánh giá cuối trên test → lưu run → chỉ kích hoạt model đạt tiêu chí. Streamlit đọc kết quả và model đã lưu.

## User Stories

1. Là người huấn luyện, tôi muốn biết số nhãn, công ty và nhóm độc lập trong từng cohort để hiểu vì sao được hoặc chưa được train.
2. Là người kiểm duyệt, tôi muốn truy ngược mỗi nhãn đến tin nguồn và bằng chứng đơn vị/kỳ trả lương để kiểm tra tính hợp lệ.
3. Là người huấn luyện, tôi muốn tách unknown/gross/net và phạm vi thu nhập để không trộn các mục tiêu khác nghĩa.
4. Là người đánh giá, tôi muốn các tin cùng công ty, trùng hoặc đăng lại ở cùng tập để tránh rò rỉ dữ liệu.
5. Là người đánh giá, tôi muốn xem số mẫu và tỷ lệ thực của ba tập để nhận biết sai lệch so với mục tiêu.
6. Là người huấn luyện, tôi muốn hai mô hình dùng chung dữ liệu và đặc trưng để so sánh công bằng.
7. Là người đánh giá, tôi muốn MAE và RMSE theo đơn vị gốc để giải thích sai số trong báo cáo.
8. Là người huấn luyện, tôi muốn chọn model bằng validation và giữ test cho đánh giá cuối để tránh chọn theo kết quả test.
9. Là người demo, tôi muốn tải lại pipeline đã lưu và nhận cùng dự đoán để chứng minh model hoạt động độc lập với phiên train.
10. Là người dùng, tôi muốn ứng dụng giải thích khi hồ sơ thiếu hỗ trợ thay vì đưa mức lương thiếu căn cứ.
11. Là người trình bày, tôi muốn so sánh model với baseline và biết phạm vi dữ liệu để không diễn giải quá mức.
12. Là người vận hành, tôi muốn run lỗi không thay thế model đang dùng để demo ổn định.

## Implementation Decisions

### 1. Readiness và hợp đồng nhãn

- Một tin tuyển dụng chuẩn hóa là một quan sát; nhiều kỹ năng hoặc địa điểm không làm tăng số quan sát.
- Chỉ lấy nhãn đã được chấp nhận, có nguồn/revision/hash và bằng chứng tiền tệ/kỳ trả lương. Khoảng hợp lệ giữ hai cận và trung điểm; thỏa thuận, một cận hoặc thiếu đơn vị không tự thành target chính xác.
- Phân cohort theo thị trường, tiền tệ, kỳ trả, basis gross/net và phạm vi thu nhập. Unknown giữ riêng; thu nhập tháng chào tuyển không tự trở thành lương cơ bản.
- Policy có phiên bản phải xác định cách xử lý kinh nghiệm thiếu/khoảng/cận, outlier, số mẫu và số nhóm tối thiểu, hỗ trợ theo hồ sơ, cấu hình mô hình và phạm vi tìm tham số. Những con số chưa chốt phải báo thiếu cấu hình, không dùng giá trị mặc định ngầm.
- Ít nhất ba nhóm độc lập là điều kiện cấu trúc để có ba tập không rỗng, chưa phải bằng chứng đủ mẫu hoặc đủ chất lượng thống kê.
- Readiness trả trạng thái, reason codes, số mẫu/công ty/nhóm theo cohort và hash policy/snapshot. Trạng thái blocked không được gọi fit.

### 2. Train / validation / test

| Tập | Tỷ lệ mục tiêu | Mục đích |
| --- | ---: | --- |
| Train | 70% | Học preprocessing, vocabulary, tham số hai model và baseline |
| Validation | 15% | Chọn cấu hình trong phạm vi đã khóa và chọn model bằng MAE |
| Test | 15% | Đánh giá cuối và kiểm tiêu chí phát hành |

- Seed 42. Tỷ lệ tính theo số quan sát, phân bổ nguyên nhóm; lưu tỷ lệ thực, không cắt nhóm để ép đủ phần trăm.
- Chuẩn hóa danh tính công ty có bằng chứng. Liên kết công ty và tin trùng/đăng lại tạo nhóm liên thông; toàn bộ nhóm vào cùng tập. Recruiter/khách hàng hoặc quan hệ công ty chưa rõ phải review.
- Lưu membership từng quan sát và số mẫu/công ty/nhóm/vai trò/nguồn/thời gian mỗi tập cùng hash snapshot, nhóm, cohort và policy.
- Không đổi seed/split để tìm metric đẹp. Không đủ phân hoạch hợp lệ thì blocked, không chuyển sang random split theo dòng.

### 3. Đặc trưng và preprocessing

- Allowlist: vai trò, biểu diễn kinh nghiệm, kỹ năng chuẩn, địa điểm chuẩn và hình thức làm việc. Remote độc lập với HCM/HN.
- Không đưa target, hai cận lương, raw title/JD, ID/URL, công ty hoặc nguồn vào model. Các trường này chỉ phục vụ bằng chứng, nhóm và audit.
- Vocabulary, encoder, imputer và scaler chỉ fit train. Giữ missing indicator và loại khoảng/cận kinh nghiệm; thiếu không tự thành 0 năm.
- Catalog alias tĩnh có phiên bản. Category/skill chỉ xuất hiện ở validation/test hoặc hồ sơ mới không được bổ sung vào vocabulary đã fit.
- Cả hai model dùng cùng feature schema, split và đơn vị target. Transform target nếu có phải khóa trước, prediction/metric trả về VND/tháng cho cohort Việt Nam tương ứng.

### 4. Huấn luyện và lựa chọn

- Khởi tạo mới Ridge với alpha dương và Linear Regression (OLS); không dùng model pretrained hoặc artifact cũ làm điểm khởi đầu.
- Baseline dự đoán trung vị target train trong cùng cohort; không tính là một trong hai model bắt buộc.
- MAE chính, RMSE phụ. Chọn validation MAE chưa làm tròn nhỏ nhất; bằng nhau chọn Linear Regression.
- Khóa lựa chọn trước khi đánh giá cuối trên test. Không đổi model, tham số hoặc split sau khi thấy test. Không tự refit train + validation.
- Chỉ promote model đã chọn khi MAE thấp hơn baseline trên cả validation và test của cùng phân hoạch. Nếu không đạt, lưu run/báo cáo và không kích hoạt cho tư vấn.
- Không hứa trước một mức MAE cụ thể khi chưa có dữ liệu thật đủ điều kiện.

### 5. Artifact và demo

- Run lưu hai pipeline, baseline, config/seed, version thư viện/catalog/schema/policy, hash dữ liệu/split, membership, prediction và metric kèm đơn vị/số mẫu.
- Tách lưu run khỏi kích hoạt model. Run lỗi/ngắt/chưa hoàn tất không thay model đang active.
- Một tiến trình mới phải tải lại pipeline và dự đoán nhất quán trong dung sai được ghi rõ. CLI và Streamlit dùng chung nghiệp vụ kiểm readiness, chuẩn hóa hồ sơ và suy luận.
- Hồ sơ ngoài phạm vi hoặc dưới ngưỡng hỗ trợ trả lý do và không trả lương/tư vấn. Dashboard/upload không khởi chạy training.

## Testing Decisions

Dùng các seam đã duyệt của dự án: MarketService cho hành vi nghiệp vụ, CLI cho luồng ngoại tuyến, smoke test Streamlit và nạp lại artifact trong tiến trình mới. Kiểm đầu vào → đầu ra; tránh test chỉ lặp lại helper nội bộ.

| Mã | Tiêu chí nghiệm thu | Bằng chứng cần có |
| --- | --- | --- |
| TR01 | Thiếu nhãn/policy/nhóm thì blocked trước fit | Kết quả service và CLI có reason codes, không có model/metric giả |
| TR02 | Không giao công ty hoặc nhóm trùng/repost giữa ba tập | Đối chiếu membership và giao tập bằng rỗng |
| TR03 | Cùng snapshot/policy/seed tái lập phân hoạch | Membership và hash giống nhau, tỷ lệ thực được ghi |
| TR04 | Held-out không ảnh hưởng preprocessing đã fit | Skill chỉ ở held-out không vào vocabulary; đổi held-out không đổi preprocessing train |
| TR05 | Hai model học trên cùng train/schema | Metadata run và prediction từ fit thật sau gate |
| TR06 | MAE/RMSE và baseline đúng đơn vị/cohort | Đối chiếu phép tính từ target/prediction xuất ra |
| TR07 | Tie chọn OLS; test fail không đổi model | Kiểm logic lựa chọn/phát hành với các kết quả metric kiểm soát |
| TR08 | Lưu/nạp không làm đổi prediction | Fresh-process reload trên nhãn thật sau gate |
| TR09 | Run lỗi không phá model active | Trạng thái active trước/sau và lỗi rõ ràng |
| TR10 | Demo không train; hồ sơ thiếu hỗ trợ không có lương | Smoke test UI và kết quả service/CLI nhất quán |

Fixture tổng hợp chỉ kiểm logic hợp đồng/chia nhóm/lựa chọn, không dùng làm dataset train hoặc báo metric chất lượng. Fit/save/reload thật phải dùng nhãn thật được duyệt sau khi gate mở.

## Out of Scope

- Thực hiện training chỉ vì tài liệu đã được viết; tự đóng gate hoặc thay ngưỡng chưa duyệt.
- Dùng dữ liệu/model cũ, pretrained embedding, LLM suy diễn nhãn hay giả định tiền tệ/kỳ trả.
- Trộn khảo sát quốc tế vào cohort tin tuyển dụng Việt Nam; diễn giải lương chào tuyển thành lương thực nhận.
- Xem chênh lệch dự đoán khi thêm kỹ năng là bằng chứng tăng thu nhập có quan hệ nhân quả.

## Further Notes

### Trạng thái dữ liệu đã đối chiếu ngày 30/10/2026

Ledger accepted hiện có hai tin Data/ML của YODY, cùng một công ty, basis unknown và phạm vi advertised_monthly_income; trung điểm 27,5 và 37,5 triệu VND/tháng. Chưa thể chia ba tập công ty độc lập. Đây là số nhãn được chấp nhận trong ledger, không phải tổng tin EDA hoặc tổng ứng viên đang review.

Nghiên cứu ML04 có thêm ứng viên nhưng chưa chấp nhận nguồn/nhãn; số tên công ty trong shortlist chưa phải số nhóm độc lập đủ điều kiện train. Cần review nguồn, vai trò, danh tính, phiên bản tin và cohort trước khi tính readiness.

### Thứ tự công việc

1. ML01/ML02/ML04: nhãn có bằng chứng, danh tính/nhóm và mở rộng dữ liệu.
2. Chốt policy số mẫu/hỗ trợ/cấu hình từ dữ liệu mở rộng; ML05 xuất readiness.
3. ML06 khóa split và kiểm leakage; không fit trước bước này.
4. ML07/ML08 fit Ridge và OLS; ML09 chọn/đánh giá/phát hành theo quy tắc trên.
5. ML10 lưu/nạp/kích hoạt; ML11 suy luận và kiểm hỗ trợ; ML12 báo cáo đánh giá.

Tài liệu này bổ sung bản hướng dẫn huấn luyện cho các ticket hiện có, không tạo luồng công việc hoặc ticket trùng. Chưa đăng/sửa issue, chưa chạy fit và chưa push code trong phạm vi soạn tài liệu này.

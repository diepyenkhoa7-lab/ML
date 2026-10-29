# Review đợt EDA ngày 29/10/2026

Mốc so sánh: 710270a. Phạm vi nghiệm thu: T01–T13 và T23 theo quyết định EDA trước; các ticket ML giữ chặn bởi gate nhãn lương, đánh giá và tư vấn. Đây là review trực tiếp theo hai trục sau khi agent phụ hết quota, không phải hai đánh giá độc lập chạy song song.

## Standards

Đối chiếu AGENTS, glossary/ADRs và baseline code smells. Một điểm đóng gói cần sửa: force-include cả datasets có thể mang cache/snapshot sinh ra vào wheel. Đã giới hạn raw và provenance, kiểm tra danh sách file wheel thực. Các quy tắc domain nằm sau MarketService; CLI/UI dùng cùng chuẩn hóa và đếm tin. Không thấy thay đổi ngoài phạm vi trong code cũ hoặc file cấu hình người dùng chưa được theo dõi.

Không còn phát hiện Standards cần sửa sau vòng này. Kiểm tra Ruff trên toàn bộ ứng dụng mới qua.

## Spec

Hai thiếu sót được phát hiện và sửa bằng test hồi quy đỏ → xanh: nhãn chuẩn Data/ML chưa được bộ phân nhóm tin nhận dù preview hồ sơ nhận được; Flutter/Unity có trong nguồn thật nhưng còn thiếu danh mục kỹ năng. Đã bổ sung alias/công nghệ có bằng chứng; rules_version tăng eda-v2. Điều hướng dùng tên tiếng Việt và trang chính tập trung EDA.

Đối chiếu raw–clean, nhiều địa điểm/Remote, đơn vị lương, kinh nghiệm, bản sao, mẫu số kỹ năng, độ phủ thời gian và mapping CSV. Snapshot nguồn thật tái lập, 3.606 dòng thô → 322 tin EDA; nhãn lương n=0. Chưa có model, metric hay dự đoán giả; toàn dự án chưa hoàn tất vì các mục ML/tư vấn/bàn giao cuối còn chờ.

Không còn phát hiện Spec cần sửa trong phạm vi đợt EDA. Các yêu cầu ML bị chặn được giữ nguyên trên tracker.

## Bằng chứng

- make check: Ruff lint/format và 203 tests qua, gồm nghiệp vụ, CLI và AppTest.
- Wheel cài ngoài thư mục dự án đọc được jobs-2026 đúng 1.550 dòng/revision 1; raw/provenance có trong wheel, processed/archives không có. Bản eda-v2 được đóng gói lại sau lần bổ sung công nghệ cuối.
- Trình duyệt thực: dashboard TopCV 295 tin/124 tin có chứng cứ kỹ năng; chọn Backend còn 72 tin; biểu đồ PNG hiển thị và bảng giữ n tương ứng.
- Browser CSV dùng File tổng hợp trong bộ nhớ: 2 hồ sơ, 1 hợp lệ/1 lỗi; ghép sai cột nghề đổi thành 0 hợp lệ/2 lỗi, sửa mapping phục hồi 1/1. Không ghi fixture vào dataset hoặc model.
- Kiểm tra viewport thực 500px không tràn chiều rộng trang. Công cụ browser từ chối đường dẫn file cục bộ và lưu screenshot; vì vậy không khẳng định đã kiểm thử hộp chọn file của hệ điều hành hoặc có screenshot được lưu bởi connector.
- Biểu đồ xuất thật đã được xem lại tại job_market/reports/skill-demand-topcv.png. Snapshot nguồn thật nằm ở job_market/datasets/processed, kèm manifest.

Kết quả: Standards 1 phát hiện đã sửa; Spec 2 phát hiện đã sửa; chưa có phát hiện mở trong phạm vi EDA. Hosted CI của code commit 4bff8f7 đã thành công: https://github.com/theihoz/ML/actions/runs/40828270329 . Các thay đổi sau mốc này chỉ ghi nhận tài liệu nghiệm thu.

## Destination

Chốt được nguồn dataset mới và các quyết định đánh giá, tư vấn cần thiết để hoàn thiện spec xây mới ứng dụng Python/Streamlit phân tích tuyển dụng CNTT Việt Nam và dự đoán lương. Đầu ra của bản đồ là quyết định có bằng chứng và đường đi sang spec, công việc triển khai.

## Notes

- Theo luồng ask-matt: wayfinder → to-spec → to-tickets; retro rà soát môi trường làm việc của phiên hiện tại.
- Các quyết định người dùng đã chốt nằm trong glossary và ADR của repo: làm mới hoàn toàn, dataset mới, Việt Nam là chính, nhóm vai trò riêng, nhãn chuẩn HCM/HN, nhiều địa điểm, Remote độc lập, trung điểm lương, huấn luyện bằng lệnh, dashboard dùng model lưu và có CSV/XLSX.
- Tất cả quyết định bổ sung trong bản spec nháp được phân biệt với yêu cầu đã xác nhận.
- Nguồn có sẵn trong dự án và các bản tải lại của cùng nguồn cũ không thuộc tập ứng viên cho bản mới.
- Map và các quyết định chỉ dùng nhãn wayfinder; các ticket triển khai sẽ được đăng riêng sau khi duyệt cách chia việc.
- Bản canonical của map là GitHub Issue. Bản Markdown này là bản soạn nội dung trước khi đăng.

## Decisions so far

Chưa có decision ticket nào của bản đồ được giải quyết; các yêu cầu đã xác nhận trước khi lập bản đồ được dẫn trong Notes.

## Not yet specified

- Ngưỡng tối thiểu về độ phủ vai trò, địa điểm và kỹ năng chỉ xác định được sau khi kiểm tra các nguồn mới.
- Kỳ thời gian so sánh và việc cần nguồn bổ sung chỉ xác định được sau kiểm toán ngày đăng và tính đại diện của nguồn.
- Định dạng gói dữ liệu bàn giao phụ thuộc vào khả năng tải và điều kiện phân phối của dataset được chọn.

## Out of scope

- Triển khai ứng dụng hoặc huấn luyện model trong phiên lập bản đồ.
- Dùng lại dữ liệu, artifact hoặc model của ứng dụng cũ.
- Mô hình pretrained, fine-tune, tạo nhãn lương giả, cam kết mức tăng lương nhân quả.
- Deploy cloud, tài khoản người dùng, thanh toán hoặc mua dataset.

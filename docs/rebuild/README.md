# Kế hoạch xây mới ứng dụng CNTT và lương lập trình viên

Branch làm việc: `dev/job-market-ml-from-scratch`. Đây là tài liệu kế hoạch; chưa triển khai ứng dụng hoặc dùng dataset mới để huấn luyện.

## Đọc theo mục đích

- Phạm vi toàn dự án: [Spec tổng thể](SPEC.md).
- Quyết định còn mở: [Bản đồ GitHub](https://github.com/theihoz/ML/issues/2).
- Bằng chứng nguồn mới: [Khảo sát bốn dataset](https://github.com/theihoz/ML/blob/411f1dbf43fea51b47677356b10f7cb3f5955190/docs/research/new-vietnam-datasets-20261028.md). Chưa chọn được nguồn đủ điều kiện.
- Chi tiết từng tính năng: [Danh mục tính năng và công việc](PLAN.md).
- Làm việc qua tracker: [Spec và 27 công việc trên GitHub](GITHUB.md).
- Triển khai hiện tại: [EDA trước](EDA_FIRST.md), [trạng thái từng công việc](IMPLEMENTATION_STATUS.md).
- Cải thiện môi trường làm việc: [Retro phiên hiện tại](RETRO.md).
- Thuật ngữ dùng chung: [Glossary](../../GLOSSARY.md). Các ADR trong repo ghi những quyết định người dùng đã xác nhận.

## Trạng thái

Người dùng đã duyệt 8 spec tính năng, 27 công việc và phạm vi kiểm thử; sau đó chọn triển khai EDA trước từ các nguồn Kaggle mới đã kiểm tra. Nguồn được nhận cho EDA không đồng nghĩa có nhãn đủ chứng cứ để huấn luyện; ML vẫn chờ gate riêng. Nguồn cũ, model cũ và mã triển khai cũ nằm ngoài bản xây mới.

GitHub Issues là tracker chính. Spec tổng thể, 8 spec tính năng và 27 công việc đã được đăng và đọc lại kiểm chứng; xem [danh mục GitHub](GITHUB.md). File github-issues.json lưu đối chiếu issue ID, URL và kết quả kiểm tra; quan hệ phụ thuộc nguồn dữ liệu vẫn giữ theo bản đồ quyết định.

## Phân biệt ba đầu ra

Map chứa câu hỏi cần quyết định và bằng chứng để chốt. Spec mô tả hành vi và nghiệm thu của sản phẩm. Ticket chia spec thành phần việc chạy được, mỗi phần có đầu ra kiểm tra riêng và phụ thuộc rõ.


# F01: Nguồn dữ liệu mới và xuất xứ

Trạng thái: đã triển khai nguồn EDA mới theo quyết định người dùng, kiểm tra ngày 29/10/2026. [Spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/7). Bằng chứng T01/T02 trong job_market/docs/tdd. Nguồn huấn luyện vẫn chờ gate nhãn lương riêng.

## Problem Statement

Người phân tích cần biết dataset mới đến từ đâu, có gì và có được phép dùng/bàn giao không trước khi đưa vào phân tích.

## Solution

Một luồng tải/nhập nguồn đã được duyệt, tạo hồ sơ phiên bản và hiển thị bản ghi cùng báo cáo tổng quan trong dashboard.

## User Stories

1. Là người dùng dự án, tôi muốn xem nguồn, revision, checksum, thời gian và điều kiện phân phối để giải thích dataset.
2. Là người dùng dự án, tôi muốn xem số dòng thô, số tin duy nhất và trường thiếu để đánh giá khả năng sử dụng.
3. Là người dùng dự án, tôi muốn tải lại đúng phiên bản nguồn mới để tái lập kết quả.
4. Là người dùng dự án, tôi muốn nhận lỗi rõ khi nguồn thay đổi hoặc không đủ trường để tránh dùng dữ liệu không kiểm chứng.

## Implementation Decisions

- Chỉ nhận nguồn mới trong danh mục được nghiên cứu và chấp nhận; giữ raw bất biến cùng chứng cứ nguồn.
- Phân biệt ngày đăng, cập nhật, hạn nộp và tải; nguồn metadata khác dữ liệu đã thực đọc.
- Lệnh tải và màn hình dữ liệu cùng dùng hồ sơ nguồn; luồng demo chỉ cần artifact local.

## Testing Decisions

- Tải/nhập một nguồn mới có thật tạo được hồ sơ và bảng xem trước, kiểm tra lại checksum.
- Nguồn không đủ điều kiện được gắn trạng thái cùng lý do; không tự dùng thư mục dữ liệu cũ làm fallback.
- Lệnh kiểm tra của ứng dụng mới chạy độc lập với runtime cũ.

## Out of Scope

Chọn hoặc mua nguồn thương mại; coi bản tải lại nguồn cũ là nguồn mới.

## Further Notes

Yêu cầu xử lý dữ liệu và bàn giao dataset. Công việc T01–T02 đã hoàn tất cho hai nguồn EDA mới; xem EDA_FIRST.md và IMPLEMENTATION_STATUS.md.


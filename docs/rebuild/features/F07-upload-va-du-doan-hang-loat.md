# F07: Upload CSV/XLSX và dự đoán hàng loạt

Trạng thái: đã được người dùng duyệt và đăng [spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/13) ngày 28/10/2026. Các quyết định phụ thuộc dataset vẫn chờ chốt qua wayfinder.

## Problem Statement

Người dùng có bảng hồ sơ cần chuẩn hóa và dự đoán mà vẫn giữ các lỗi theo dòng để sửa.

## Solution

Chọn file, ghép cột, xem trước raw–clean/lỗi, chạy dự đoán bằng model đã lưu và tải kết quả theo đúng thứ tự đầu vào.

## User Stories

1. Là người dùng dự án, tôi muốn ghép tên cột của file với trường hồ sơ để dùng file đang có.
2. Là người dùng dự án, tôi muốn xem lỗi từng dòng và giá trị chuẩn để sửa dữ liệu.
3. Là người dùng dự án, tôi muốn dự đoán các dòng hợp lệ mà không mất dòng lỗi để đối chiếu.
4. Là người dùng dự án, tôi muốn tải file kết quả có lương, đơn vị và trạng thái để sử dụng lại.

## Implementation Decisions

- Chỉ nhận định dạng dữ liệu được hỗ trợ; giới hạn file/dòng được cấu hình và thông báo trước.
- Không tự cắt dòng, không thực thi nội dung file; upload không thay training snapshot/model.
- Dùng cùng chuẩn hóa, validation và inference của hồ sơ đơn.
- Giữ row ID/thứ tự, lỗi có mã và giải thích; export được toàn bộ dòng và trạng thái.

## Testing Decisions

- Một CSV và XLSX có dòng đúng/sai cho cùng kết quả logic, đủ số dòng và đúng thứ tự.
- Ghép sai cột, file rỗng/quá giới hạn hoặc cấu trúc không hợp lệ có thông báo rõ.
- Snapshot/artifact trước và sau upload không đổi; prediction khớp form đơn.

## Out of Scope

Huấn luyện qua upload; nạp model tùy ý do người dùng tải lên; thêm hệ thống tài khoản.

## Further Notes

Yêu cầu người dùng bổ sung cho ứng dụng demo. Công việc T23–T25.


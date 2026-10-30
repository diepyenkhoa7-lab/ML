# M07 — Dự đoán hàng loạt CSV/XLSX

## Problem Statement

Người dùng cần dự đoán file hồ sơ mà không mất dòng lỗi hoặc tạo kết quả khác form đơn.

## Solution

Mở rộng preview CSV hiện có sang suy luận từ model đã lưu và XLSX tương đương, giữ mapping/raw/row ID/thứ tự cùng trạng thái từng dòng.

## User Stories

1. Là người dùng, tôi muốn chọn sheet/ghép cột/xem lỗi, để biết file sẽ được xử lý ra sao.
2. Là người dùng, tôi muốn dòng lỗi vẫn có trong kết quả, để sửa và chạy lại.
3. Là người dùng, tôi muốn hồ sơ tương đương ở CSV/XLSX/form đơn cho cùng prediction, để tin vào quy trình.

## Implementation Decisions

- Tái dùng chuẩn hóa và inference của M05, không xây encoder riêng cho upload. Row preview hợp lệ vẫn phải qua support/artifact checks của model.
- Giữ giới hạn CSV 5 MiB/10.000 dòng; XLSX cũng có giới hạn hữu hạn công bố trước và chọn sheet tường minh. Không tự cắt dòng hoặc âm thầm lấy sheet đầu khi có nhiều sheet.
- Phân biệt lỗi toàn file với lỗi từng hồ sơ; preserve mọi dòng đọc được và ordinal/source row, raw/mapping, lỗi/cảnh báo. File cấu trúc không thể đọc được bị từ chối rõ, không xuất kết quả một phần như đã hoàn tất.
- Mỗi dòng có status, prediction hoặc null, đơn vị/basis, model/run/snapshot và reason. Model không sẵn sàng thì không tạo con số cho bất kỳ dòng nào.
- Không thực thi macro/formula, không nạp model từ file, không sửa dataset/model/snapshot hoặc tự fit. File rỗng/quá giới hạn trả thông báo rõ.

## Testing Decisions

CSV/XLSX cùng hồ sơ, alias, số liệu/khoảng kinh nghiệm và dòng lỗi cho cùng trạng thái/prediction/thứ tự. Kiểm malformed, nhiều sheet, sai mapping, quá giới hạn, model hỏng và OOV; kết quả khớp form đơn. Test inference cần artifact từ dữ liệu thật sau gate, không dùng model giả.

## Out of Scope

Huấn luyện từ file upload, model upload hoặc xử lý bảng tính bằng thực thi nội dung.

## Further Notes

F07, T24/T25; kế thừa T23 đã triển khai. Không đánh dấu batch hoàn tất chỉ vì preview CSV đang chạy được.

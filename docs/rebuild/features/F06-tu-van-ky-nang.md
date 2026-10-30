# F06: Tư vấn kỹ năng có bằng chứng

Trạng thái: đã được người dùng duyệt và đăng [spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/12) ngày 28/10/2026. Các quyết định phụ thuộc dataset vẫn chờ chốt qua wayfinder.

## Problem Statement

Người dùng cần biết học thêm kỹ năng nào, nhưng chênh lệch lương trong dữ liệu không tự chứng minh hiệu quả học kỹ năng.

## Solution

Gợi ý kỹ năng người dùng chưa có, kèm vai trò liên quan, số tin hỗ trợ và bằng chứng lương/nhu cầu, hoặc thông báo chưa đủ dữ liệu.

## User Stories

1. Là người dùng dự án, tôi muốn nhận kỹ năng chưa có phù hợp nghề để ưu tiên học.
2. Là người dùng dự án, tôi muốn xem lý do và số mẫu để đánh giá gợi ý.
3. Là người dùng dự án, tôi muốn phân biệt quan sát trong tin với chênh lệch dự đoán để hiểu kết luận.
4. Là người dùng dự án, tôi muốn nhận thông báo thiếu bằng chứng khi chưa đủ dữ liệu thay vì danh sách cố định.

## Implementation Decisions

- Nguồn xếp hạng chỉ từ train; không dùng test để chọn kỹ năng.
- Đề xuất tối đa ba kỹ năng, phối hợp nhu cầu quan sát và chênh lệch dự đoán; cần chốt cách xếp hạng/ngưỡng.
- Giữ nguyên hồ sơ nền khi thử bổ sung từng kỹ năng; định danh/alias kỹ năng nhất quán.
- Không khuyến nghị lại kỹ năng đã có; nêu rõ bằng chứng liên hệ, không cam kết nhân quả.

## Testing Decisions

- Hồ sơ có alias kỹ năng không nhận gợi ý trùng; hồ sơ thiếu hỗ trợ trả trạng thái phù hợp.
- Điểm số/tin hỗ trợ truy được về train; không dùng công thức cố định giả làm prediction.
- Save/reload và chạy lại cùng hồ sơ giữ được thứ tự gợi ý nếu bằng chứng không đổi.

## Out of Scope

Sinh lời khuyên bằng LLM/pretrained; hứa học một kỹ năng sẽ tăng một số tiền chắc chắn.

## Further Notes

Yêu cầu III.3 và III.4. Công việc T21–T22. Chờ quyết định bằng chứng tư vấn.


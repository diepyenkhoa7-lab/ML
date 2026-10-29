# M06 — Tư vấn kỹ năng bằng bằng chứng

## Problem Statement

Danh sách kỹ năng phổ biến không tự là lời khuyên cá nhân; liên hệ với lương không chứng minh việc học kỹ năng gây tăng thu nhập.

## Solution

Gợi ý tối đa ba kỹ năng chưa có, phù hợp vai trò, có số tin hỗ trợ và phân biệt từng loại bằng chứng; thiếu hỗ trợ thì trả lý do.

## User Stories

1. Là người dùng, tôi muốn không bị gợi ý lại alias của kỹ năng đã có, để danh sách có ích.
2. Là người dùng, tôi muốn thấy n và tín hiệu xếp hạng, để cân nhắc gợi ý.
3. Là người dùng, tôi muốn biết delta model khác tác động nhân quả, để không kỳ vọng tăng lương chắc chắn.

## Implementation Decisions

- Candidate và thống kê xếp hạng chỉ từ train của run đã khóa, cùng role/phạm vi hỗ trợ. Số tin EDA toàn bộ không được đổi tên thành số mẫu train hoặc số nhãn lương.
- Chuẩn hóa/loại kỹ năng đã có trước khi xếp hạng; giữ hồ sơ nền khi thử thêm một kỹ năng, không tự tăng kinh nghiệm hoặc đổi địa điểm.
- Hiển thị riêng nhu cầu quan sát, thống kê lương có hỗ trợ và delta dự đoán nếu được phép. Không trộn thành một “% tăng lương” khó truy nguồn.
- Cách phối hợp tín hiệu, threshold và tie-break chờ #5. Không dùng test để tối ưu ranking; không sinh danh sách cố định/LLM hoặc tự giới thiệu kỹ năng không có trong train.
- Feature importance để giải thích model được ghi rõ tập/định nghĩa/phương pháp, không tự chuyển thành lợi ích thu nhập cá nhân. Kỹ năng thiếu hỗ trợ hoặc không có candidate hợp lệ trả insufficient_evidence.

## Testing Decisions

Test logic alias/loại kỹ năng/tie-break bằng fixture nhỏ, không tạo model/metric giả. Sau gate, candidate/n/prediction truy được về train và artifact thật; snapshot/hash không đổi; reload tái lập thứ tự. Thêm kỹ năng không được làm đổi các trường nền.

## Out of Scope

Khẳng định nhân quả, lời hứa tăng lương, LLM/pretrained, dùng test hoặc khảo sát sử dụng công nghệ thay nhu cầu tuyển dụng.

## Further Notes

F06, T21/T22; phụ thuộc M05 và quyết định #5. Chưa có model/nhãn hỗ trợ thì UI không hiện danh sách tư vấn giả.

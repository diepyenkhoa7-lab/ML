# M01 — Nhãn lương và điều kiện mở ML

## Problem Statement

Nhãn đủ số tiền chưa chắc đúng tiền tệ, kỳ hoặc thực thể tin; một nhãn sai lớn có thể làm hỏng toàn bộ so sánh model.

## Solution

Báo cáo readiness kiểm toán snapshot, chứng cứ nhãn, nhóm tin và policy. Chỉ dataset được chấp nhận mới có thể dùng để fit; EDA vẫn giữ các bản ghi chưa đủ nhãn.

## User Stories

1. Là người kiểm toán, tôi muốn truy target về raw và chứng cứ nguồn, để kiểm tra cách chuẩn hóa.
2. Là người huấn luyện, tôi muốn thấy số nhãn/thực thể/nhóm theo nghề và basis, để quyết định phạm vi train.
3. Là người huấn luyện, tôi muốn thấy lý do blocked, để không sửa gate bằng cách tự điền dữ liệu.

## Implementation Decisions

- Giữ nguồn, revision/hash, raw ID/URL, raw số tiền và chứng cứ tiền tệ/kỳ/basis cho từng nhãn. Chứng cứ bổ sung phải thuộc cùng tin và có xuất xứ; không suy MONTH từ lịch làm việc hoặc thưởng tháng 13.
- Basis unknown giữ riêng theo quyết định người dùng ngày 29/10; không gộp với gross/net hoặc tự quy đổi. Chấp nhận một basis không có nghĩa đủ số nhóm/nhãn để mở training.
- Phân biệt fixed/bounded/single-bound/negotiable/missing/invalid; chỉ fixed/bounded đủ chứng cứ mới xét target. Kiểm tra riêng hai đầu khi notation trộn số đầy đủ và triệu/k; không nhân scale đã có hai lần.
- Danh tính tin giữ tham số định danh, bỏ tracking có quy tắc; có quan hệ row → entity → leakage group. Bằng chứng bổ sung tương thích được giữ; lương/đơn vị/nghề mâu thuẫn được review, không tùy thứ tự dòng.
- Readiness có trạng thái blocked/needs_review/ready, số mẫu thực và mã lý do, phiên bản policy và snapshot. n>0 hoặc issue đóng không tự đủ để ready; phải qua kiểm toán, policy #4 và các kiểm tra bắt buộc.
- Gate #42 còn mở với dữ liệu hiện tại. Lỗi audit liên quan label/identity/role/Remote là điều kiện phải xử lý trước chấp nhận snapshot ML. Không hardcode 322/295 như chuẩn dữ liệu đúng.

## Testing Decisions

Test qua readiness/chuẩn hóa chung: notation trộn scale, ký hiệu tiền sát số, thiếu kỳ/tiền tệ, hai ID khác chỉ khác query, bản sao bổ sung địa điểm/kỹ năng và xung đột nhãn. Thay thứ tự dòng không làm tùy tiện đổi quan sát dùng train. Khi chưa ready, mọi lệnh fit bị từ chối mà không tạo artifact thành công.

## Out of Scope

Chọn nguồn thương mại, suy đơn vị thiếu, train hoặc công bố metric để chứng minh readiness.

## Further Notes

Liên quan gate #42, F02 và T09/T11; sửa lỗi phát hiện sau nghiệm thu là công việc follow-up, không coi checklist EDA cũ là bằng chứng label đã được chấp nhận.

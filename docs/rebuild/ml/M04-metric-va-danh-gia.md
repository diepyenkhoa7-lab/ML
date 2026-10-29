# M04 — Báo cáo metric và vùng dữ liệu hỗ trợ

## Problem Statement

Một metric tổng không cho biết model sai ở nghề/khu vực nào; metric thiếu số mẫu/đơn vị dễ bị đọc sai.

## Solution

Bảng và biểu đồ đánh giá từ y_true/prediction đã lưu, có split, nguồn/thời gian, n, đơn vị/basis và giới hạn từng nhóm.

## User Stories

1. Là người đánh giá, tôi muốn ít nhất MAE/RMSE cho cả hai model, để hiểu sai số cùng đơn vị.
2. Là người đánh giá, tôi muốn xem validation tách test, để biết model được chọn như thế nào.
3. Là người dùng, tôi muốn thấy lỗi và n theo nhóm, để biết mức hỗ trợ của ước tính.

## Implementation Decisions

- Đã chốt MAE là metric chính, RMSE là metric phụ; cả hai theo VND/tháng trên cùng split. Lưu nhãn và prediction cùng row/entity/group/model/split ID để tính lại; không ghi sẵn model thắng hoặc metric.
- Nhóm rỗng có metric null/lý do; nhóm ít mẫu có n và trạng thái hỗ trợ, không dùng điểm nhóm nhỏ làm bằng chứng chất lượng. NaN/Inf không bị lặng lẽ xóa để làm đẹp điểm; prediction âm được báo là output không hợp lệ theo nghiệp vụ, không clip để che lỗi đánh giá.
- Báo theo role, kinh nghiệm, nguồn, địa điểm và work mode khi đủ hỗ trợ. Một tin thuộc nhiều nhóm địa điểm nhưng tổng đánh giá vẫn theo quan sát duy nhất; nhóm chồng lắp không được cộng thành n tổng.
- Tiêu chí phát hành đã chốt: model được chọn bằng validation MAE phải tốt hơn baseline trung vị train theo MAE trên cả validation và test. Không chọn lại model hoặc chỉnh tham số theo test. Threshold hỗ trợ bằng số còn phải khóa từ dữ liệu mở rộng trước fit. Không suy khoảng tin cậy từ RMSE hoặc dùng nhóm quá nhỏ để khẳng định chất lượng.
- UI và bảng/ảnh xuất có đơn vị, basis, model/run/snapshot, split, bộ lọc, n, nguồn và kỳ dữ liệu. Không để provenance chỉ nằm ở trang đang mở mà mất khi tải file.

## Testing Decisions

Metric kiểm bằng ví dụ tính tay nhỏ là test logic, không phải chất lượng model. Sau gate, recompute từ prediction thật; bảng/ảnh/export khớp cùng bộ lọc và metadata. Test nhóm rỗng/một mẫu/chồng địa điểm và output không hữu hạn.

## Out of Scope

Dùng test để chọn champion, điền metric giả, công bố khoảng tin cậy hoặc bảo đảm accuracy khi chưa có bằng chứng.

## Further Notes

F04/F05, T18/T19. Thống kê lương quan sát trong F03/T14–T16 được phân biệt rõ với sai số dự đoán và phân tích ảnh hưởng của model.

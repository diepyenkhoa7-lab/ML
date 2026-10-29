# M08 — Demo offline và bàn giao ML

## Problem Statement

App trên máy phát triển chưa chứng minh gói nộp chứa đúng dữ liệu, model và các luồng chạy độc lập.

## Solution

Gói Python mới có manifest, dữ liệu được phép phân phối, artifact đã đánh giá và kịch bản nghiệm thu từ môi trường sạch.

## User Stories

1. Là người báo cáo, tôi muốn cài theo hướng dẫn và nạp model, để demo trên máy khác.
2. Là người báo cáo, tôi muốn dự đoán/tư vấn/upload khi tắt mạng, để không phụ thuộc nguồn ngoài.
3. Là người nhận bàn giao, tôi muốn đối chiếu model/dataset/metric với manifest, để tái lập kết quả.

## Implementation Decisions

- Gói chỉ lấy code, raw/label/snapshot, config/split, model/preprocessing và báo cáo thuộc bản mới; không gom toàn bộ cache hoặc artifact của workspace cũ.
- Dataset phải kèm attribution, điều kiện phân phối, revision/hash và chứng cứ label. Link tải không thay file dataset bắt buộc của đề bài.
- Ghi Python/library/platform versions, lệnh kiểm tra/train/chạy, đơn vị, basis, n từng split và metric thực. Cài dependencies có thể chuẩn bị trước; luồng demo đã chuẩn bị không gọi mạng để suy luận.
- Nghiệm thu đủ hai model/ít nhất hai metric, biểu đồ lương khi đủ nhãn, form đơn, support, tư vấn, CSV/XLSX và export từ artifact trong gói. Lệnh startup hoặc wheel CLI một mình không thay nghiệm thu toàn ứng dụng.
- Nếu data gate hoặc release policy chưa đạt thì gói mang trạng thái chưa hoàn tất ML, không đổi tên bản EDA thành bản nộp đủ đề bài.

## Testing Decisions

Cài vào môi trường mới từ gói thật, kiểm checksum, nạp model ở tiến trình mới, chạy kịch bản browser/CLI khi ngắt mạng và so probe/metric/exports. Kiểm gói thiếu nguồn/model/schema và không lẫn dataset cũ. Không mock luồng demo để tuyên bố offline thành công.

## Out of Scope

Deploy cloud, mua dataset hoặc công bố đạt chất lượng khi chưa có đánh giá thật.

## Further Notes

F08, T26/T27; chỉ hoàn tất sau M01–M07 và các phần F03 còn phụ thuộc nhãn. Đây là nghiệm thu toàn bộ sản phẩm, khác với kiểm tra gói Python của đợt EDA.

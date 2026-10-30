# Danh mục spec ML

Nhánh ổn định EDA: main tại 9ce0506. Nhánh soạn thảo/phát triển ML: dev/ml-development, bắt đầu từ cùng mốc; chưa push code ML, sẽ push sau khi hoàn tất theo yêu cầu người dùng. Ngày 30/10 đã đăng 23 ticket ML sau khi người dùng duyệt bản chia; các spec/audit chi tiết vẫn được lưu trong nhánh local, không tự tạo một spec parent mới trùng #6.

Đặc tả phát triển ngày 29/10/2026. Các nguyên tắc #4/#5 đã được người dùng xác nhận; ngưỡng hỗ trợ bằng số và cấu hình phụ thuộc dữ liệu cần khóa trước fit. Chưa đổi dependency, huấn luyện, mở gate #42 hoặc đóng issue từ xa. Ranh giới kiểm thử MarketService/CLI/Streamlit đã được duyệt và được tái sử dụng.

- [Spec tổng ML](SPEC.md)
- [26 tiêu chí nghiệm thu theo chức năng](ACCEPTANCE.md)
- [23 ticket ML đã duyệt và đăng GitHub](TICKET_PLAN.md)
- [Audit bổ sung trước ML](../AUDIT-2026-10-29.md)
- [Nghiên cứu ứng viên nhãn lương mới](LABEL_RESEARCH-2026-10-29.md)
- [Kết quả kiểm duyệt 26 ứng viên](LABEL_ADJUDICATION-2026-10-29.md)

| Spec | Đầu ra | Truy vết công việc hiện có |
| --- | --- | --- |
| [M01](M01-nhan-va-readiness.md) | Nhãn có chứng cứ và readiness | F02; T09/T11; gate #42 |
| [M02](M02-split-va-features.md) | Snapshot/split/features không leakage | F04; T17; #4 |
| [M03](M03-huan-luyen-va-chon-model.md) | Hai model tự train và champion | F04; T17/T18 |
| [M04](M04-metric-va-danh-gia.md) | Metric, lỗi nhóm và provenance export | F04/F05; T18/T19 |
| [M05](M05-artifact-va-du-doan-don.md) | Artifact, reload và suy luận có support | F05; T17/T20 |
| [M06](M06-tu-van-ky-nang.md) | Gợi ý kỹ năng bằng train evidence | F06; T21/T22; #5 |
| [M07](M07-batch-csv-xlsx.md) | Dự đoán CSV/XLSX giữ mọi dòng | F07; T24/T25 |
| [M08](M08-demo-va-ban-giao.md) | Gói nộp và demo offline thật | F08; T26/T27 |

Có thể phát triển trước cổng kiểm tra, schema/config, trạng thái không có model và test logic tại seam đã duyệt. Fit/save/reload với model thật, báo cáo chất lượng và nghiệm thu dự đoán phải chờ nhãn thật/chính sách được chấp nhận. Fixture tổng hợp không dùng cho training hay công bố metric.

Quyết định bổ sung ngày 29/10: giữ riêng nhóm unknown gross/net, không trộn với gross/net đã xác nhận; đã ghi ADR 0006. Các phần khác của #4/#5 và gate #42 vẫn mở, chưa có model được train.

Kiểm duyệt tiếp theo chấp nhận hai nhãn YODY vào file riêng, 17 trường hợp cần review và 7 trường hợp bị loại. ADR 0007 giữ phạm vi thu nhập tháng chào tuyển riêng. Chưa nhập hai nhãn vào base pipeline, chưa mở training; dữ liệu và manifest trong job_market/datasets/labels/2026-10-29.

Quyết định #4/#5: chia công ty và nhóm trùng, tỷ lệ mục tiêu 70/15/15 seed 42; Ridge + Linear Regression, MAE chính/RMSE phụ, chọn validation MAE, bằng nhau chọn Linear Regression. Chỉ promote khi MAE tốt hơn trung vị train trên cả validation và test; không đạt thì giữ báo cáo, không đổi/chỉnh model theo test. Hồ sơ thiếu hỗ trợ không nhận lương/tư vấn. Gợi ý tối đa ba kỹ năng đủ hỗ trợ có delta dương, xếp theo delta rồi n train và tên chuẩn. Ngưỡng hỗ trợ cần dữ liệu mở rộng để khóa trước fit; ADR 0008/0009 ghi các lựa chọn này.

Ngày 30/10, người dùng duyệt bản chia 23 lát cắt ML. Đã đăng các issue con với ready-for-agent, 23 liên kết parent native và 33 blocker native; đọc lại xác minh body/labels/relationships và parent cũ không đổi nội dung/trạng thái/nhãn. Graph triển khai cho phần ML là ticket-graph.json; ticket-publication.json ghi ánh xạ và bằng chứng publication. Các issue parent cũ là đầu mục tổng hợp, không triển khai thêm một bản trùng với child.

Frontier hiện có: ML01/#43, ML02/#44, ML03/#45, ML04/#46 và ML20/#63. Các bước fit giữ #42/readiness; policy số còn chờ #4/#5. Không đóng gate, train hoặc push code trong lượt publication. Graph 27 ticket cũ giữ nguyên như lịch sử/đầu mục tổng hợp.

Các ticket T14–T16 về lương quan sát giữ spec F03, chi tiết trong ML16–ML18; không đồng nhất chúng với metric hoặc tác động kỹ năng của model. Preview XLSX ML20 có thể làm trước prediction ML21 theo dependency mới đã được người dùng duyệt.

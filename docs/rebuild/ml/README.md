# Danh mục spec ML

Nhánh ổn định EDA: main tại 9ce0506. Nhánh soạn thảo/phát triển ML: dev/ml-development, bắt đầu từ cùng mốc. Theo yêu cầu người dùng, spec/audit ML mới hiện chỉ ở local; chưa push nhánh ML hoặc đăng một spec mới lên tracker. Push phần ML sau khi hoàn tất, tách khỏi lần push EDA.

Đặc tả phát triển ngày 29/10/2026. Giữ các yêu cầu đã duyệt; chưa đổi dependency, chốt các đề xuất #4/#5, huấn luyện hoặc gỡ gate nhãn lương #42. Ranh giới kiểm thử MarketService/CLI/Streamlit đã được duyệt và được tái sử dụng.

- [Spec tổng ML](SPEC.md)
- [26 tiêu chí nghiệm thu theo chức năng](ACCEPTANCE.md)
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

Các ticket T14–T16 về lương quan sát giữ spec F03; không đồng nhất chúng với metric hoặc tác động kỹ năng của model. Chia nhỏ lại ticket nếu cần là bước to-tickets riêng, không tự thay 27 công việc cũ trong lần viết đặc tả này.

# GitHub Issues của bản kế hoạch đã duyệt

Ngày duyệt: 28/10/2026. Branch: `dev/job-market-ml-from-scratch`. Bộ kế hoạch v2 gồm 1 spec tổng thể, 8 spec tính năng và 27 công việc.

Trạng thái đồng bộ: đã đăng và đọc lại kiểm chứng đủ 36 issue, 35 quan hệ cha–con, 51 quan hệ phụ thuộc. Spec tổng thể và 27 công việc có nhãn ready-for-agent; các decision ticket giữ nguyên trạng thái mở. Chưa triển khai ứng dụng hoặc chấp nhận dataset mới.

[Spec tổng thể](https://github.com/theihoz/ML/issues/6) · [Bản đồ quyết định](https://github.com/theihoz/ML/issues/2).

## Spec tính năng

| Tính năng | Số công việc |
| --- | ---: |
| [F01 — Nguồn dữ liệu mới và xuất xứ](https://github.com/theihoz/ML/issues/7) | 2 |
| [F02 — Chuẩn hóa dữ liệu và nhãn có chứng cứ](https://github.com/theihoz/ML/issues/8) | 9 |
| [F03 — Phân tích tuyển dụng và trực quan hóa lương](https://github.com/theihoz/ML/issues/9) | 5 |
| [F04 — Tự huấn luyện và so sánh ít nhất hai mô hình](https://github.com/theihoz/ML/issues/10) | 2 |
| [F05 — Dự đoán lương và giải thích giới hạn](https://github.com/theihoz/ML/issues/11) | 2 |
| [F06 — Tư vấn kỹ năng có bằng chứng](https://github.com/theihoz/ML/issues/12) | 2 |
| [F07 — Upload CSV/XLSX và dự đoán hàng loạt](https://github.com/theihoz/ML/issues/13) | 3 |
| [F08 — Bàn giao và demo tái lập trên máy](https://github.com/theihoz/ML/issues/14) | 2 |

## Công việc và phụ thuộc

| Công việc | Tính năng | Bị chặn bởi |
| --- | --- | --- |
| [T01 — Nhập một nguồn mới và xem dữ liệu gốc](https://github.com/theihoz/ML/issues/15) | [F01](https://github.com/theihoz/ML/issues/7) | [Chọn nguồn dataset Việt Nam mới có thể kiểm chứng](https://github.com/theihoz/ML/issues/3) |
| [T02 — Tải lại đúng phiên bản dataset và kiểm checksum](https://github.com/theihoz/ML/issues/16) | [F01](https://github.com/theihoz/ML/issues/7) | [T01](https://github.com/theihoz/ML/issues/15) |
| [T03 — Phân nhóm Backend, Frontend, Fullstack và Mobile](https://github.com/theihoz/ML/issues/17) | [F02](https://github.com/theihoz/ML/issues/8) | [T01](https://github.com/theihoz/ML/issues/15) |
| [T04 — Bổ sung Data/ML, DevOps và QA Automation](https://github.com/theihoz/ML/issues/18) | [F02](https://github.com/theihoz/ML/issues/8) | [T03](https://github.com/theihoz/ML/issues/17) |
| [T05 — Chuẩn hóa HCM/HN và xem bảng alias](https://github.com/theihoz/ML/issues/19) | [F02](https://github.com/theihoz/ML/issues/8) | [T01](https://github.com/theihoz/ML/issues/15) |
| [T06 — Giữ nhiều địa điểm, tách Remote và đếm tin duy nhất](https://github.com/theihoz/ML/issues/20) | [F02](https://github.com/theihoz/ML/issues/8) | [T05](https://github.com/theihoz/ML/issues/19) |
| [T07 — Bóc tách ngôn ngữ lập trình có bằng chứng](https://github.com/theihoz/ML/issues/21) | [F02](https://github.com/theihoz/ML/issues/8) | [T01](https://github.com/theihoz/ML/issues/15) |
| [T08 — Bổ sung framework, cơ sở dữ liệu và cloud](https://github.com/theihoz/ML/issues/22) | [F02](https://github.com/theihoz/ML/issues/8) | [T07](https://github.com/theihoz/ML/issues/21) |
| [T09 — Chuẩn hóa khoảng lương và đánh dấu nhãn hợp lệ](https://github.com/theihoz/ML/issues/23) | [F02](https://github.com/theihoz/ML/issues/8) | [T01](https://github.com/theihoz/ML/issues/15) |
| [T10 — Chuẩn hóa số năm và khoảng kinh nghiệm](https://github.com/theihoz/ML/issues/24) | [F02](https://github.com/theihoz/ML/issues/8) | [T01](https://github.com/theihoz/ML/issues/15) |
| [T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot](https://github.com/theihoz/ML/issues/25) | [F02](https://github.com/theihoz/ML/issues/8) | [T02](https://github.com/theihoz/ML/issues/16), [T04](https://github.com/theihoz/ML/issues/18), [T06](https://github.com/theihoz/ML/issues/20), [T08](https://github.com/theihoz/ML/issues/22), [T09](https://github.com/theihoz/ML/issues/23), [T10](https://github.com/theihoz/ML/issues/24) |
| [T12 — Xem top nhu cầu kỹ năng theo bộ lọc](https://github.com/theihoz/ML/issues/26) | [F03](https://github.com/theihoz/ML/issues/9) | [T11](https://github.com/theihoz/ML/issues/25) |
| [T13 — Xem xu hướng khi đủ thời gian nguồn](https://github.com/theihoz/ML/issues/27) | [F03](https://github.com/theihoz/ML/issues/9) | [T11](https://github.com/theihoz/ML/issues/25) |
| [T14 — Xem tương quan kinh nghiệm và lương](https://github.com/theihoz/ML/issues/28) | [F03](https://github.com/theihoz/ML/issues/9) | [T11](https://github.com/theihoz/ML/issues/25), [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4) |
| [T15 — So sánh lương theo vai trò và khu vực](https://github.com/theihoz/ML/issues/29) | [F03](https://github.com/theihoz/ML/issues/9) | [T11](https://github.com/theihoz/ML/issues/25), [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4) |
| [T16 — Xếp hạng kỹ năng theo lương có số mẫu](https://github.com/theihoz/ML/issues/30) | [F03](https://github.com/theihoz/ML/issues/9) | [T11](https://github.com/theihoz/ML/issues/25), [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4) |
| [T17 — Huấn luyện model đầu tiên và dự đoán một hồ sơ](https://github.com/theihoz/ML/issues/31) | [F04](https://github.com/theihoz/ML/issues/10) | [T11](https://github.com/theihoz/ML/issues/25), [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4) |
| [T18 — Huấn luyện model thứ hai và so sánh metric](https://github.com/theihoz/ML/issues/32) | [F04](https://github.com/theihoz/ML/issues/10) | [T17](https://github.com/theihoz/ML/issues/31) |
| [T19 — Xem sai số theo nhóm nghề và dữ liệu](https://github.com/theihoz/ML/issues/33) | [F05](https://github.com/theihoz/ML/issues/11) | [T18](https://github.com/theihoz/ML/issues/32), [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4) |
| [T20 — Cảnh báo hồ sơ chưa đủ hỗ trợ khi dự đoán](https://github.com/theihoz/ML/issues/34) | [F05](https://github.com/theihoz/ML/issues/11) | [T18](https://github.com/theihoz/ML/issues/32), [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4) |
| [T21 — Gợi ý kỹ năng còn thiếu theo nhu cầu nghề](https://github.com/theihoz/ML/issues/35) | [F06](https://github.com/theihoz/ML/issues/12) | [T20](https://github.com/theihoz/ML/issues/34), [Chốt bằng chứng và cách xếp hạng kỹ năng nên học](https://github.com/theihoz/ML/issues/5) |
| [T22 — Bổ sung bằng chứng lương cho kỹ năng nên học](https://github.com/theihoz/ML/issues/36) | [F06](https://github.com/theihoz/ML/issues/12) | [T21](https://github.com/theihoz/ML/issues/35), [Chốt bằng chứng và cách xếp hạng kỹ năng nên học](https://github.com/theihoz/ML/issues/5) |
| [T23 — Upload CSV, ghép cột và xem lỗi chuẩn hóa](https://github.com/theihoz/ML/issues/37) | [F07](https://github.com/theihoz/ML/issues/13) | [T11](https://github.com/theihoz/ML/issues/25) |
| [T24 — Dự đoán hàng loạt CSV và xuất toàn bộ kết quả](https://github.com/theihoz/ML/issues/38) | [F07](https://github.com/theihoz/ML/issues/13) | [T23](https://github.com/theihoz/ML/issues/37), [T20](https://github.com/theihoz/ML/issues/34) |
| [T25 — Hỗ trợ cùng quy trình upload với XLSX](https://github.com/theihoz/ML/issues/39) | [F07](https://github.com/theihoz/ML/issues/13) | [T24](https://github.com/theihoz/ML/issues/38) |
| [T26 — Tạo gói mã nguồn, dataset và artifact có manifest](https://github.com/theihoz/ML/issues/40) | [F08](https://github.com/theihoz/ML/issues/14) | [T12](https://github.com/theihoz/ML/issues/26), [T13](https://github.com/theihoz/ML/issues/27), [T14](https://github.com/theihoz/ML/issues/28), [T15](https://github.com/theihoz/ML/issues/29), [T16](https://github.com/theihoz/ML/issues/30), [T19](https://github.com/theihoz/ML/issues/33), [T22](https://github.com/theihoz/ML/issues/36), [T25](https://github.com/theihoz/ML/issues/39) |
| [T27 — Cài mới và kiểm tra trọn demo offline](https://github.com/theihoz/ML/issues/41) | [F08](https://github.com/theihoz/ML/issues/14) | [T26](https://github.com/theihoz/ML/issues/40) |

## Cách lấy việc

GitHub là tracker chính. Chọn công việc có mọi blocker đã hoàn tất, đọc spec cha và checklist của công việc đó rồi mới triển khai. Nhãn `ready-for-agent` chỉ xác nhận nội dung đã được chuẩn bị; không thay thế quan hệ phụ thuộc.

Quyết định chọn dataset mới, cách đánh giá và bằng chứng tư vấn vẫn đang mở. Không dùng lại dataset/model/code cũ để mở khóa các công việc.


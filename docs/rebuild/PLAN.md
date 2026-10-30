# Danh mục tính năng và công việc

Trạng thái: bản v2 gồm 27 công việc thuộc 8 spec tính năng đã được người dùng duyệt và đăng GitHub ngày 28/10/2026, thay bộ 13 công việc ban đầu. Mỗi việc có đầu ra xem/demo được, checklist và nghiệm thu. Xem [danh mục issue GitHub](GITHUB.md).

## Điểm kiểm thử đã được duyệt

Kiểm thử chủ yếu qua một giao diện nghiệp vụ chung mà cả CLI và Streamlit sử dụng. Thêm smoke UI cho form, biểu đồ và upload; kiểm tra artifact bằng nạp lại model trong tiến trình mới. Các ví dụ tổng hợp nhỏ chỉ kiểm thử logic, tách khỏi dữ liệu huấn luyện và báo cáo chất lượng.

## Spec từng tính năng

- [F01 — Nguồn dữ liệu mới và xuất xứ](features/F01-nguon-du-lieu-moi.md)
- [F02 — Chuẩn hóa dữ liệu và nhãn có chứng cứ](features/F02-chuan-hoa-va-chat-luong.md)
- [F03 — Phân tích tuyển dụng và trực quan hóa lương](features/F03-phan-tich-thi-truong.md)
- [F04 — Tự huấn luyện và so sánh ít nhất hai mô hình](features/F04-huan-luyen-va-so-sanh.md)
- [F05 — Dự đoán lương và giải thích giới hạn](features/F05-du-doan-va-do-ho-tro.md)
- [F06 — Tư vấn kỹ năng có bằng chứng](features/F06-tu-van-ky-nang.md)
- [F07 — Upload CSV/XLSX và dự đoán hàng loạt](features/F07-upload-va-du-doan-hang-loat.md)
- [F08 — Bàn giao và demo tái lập trên máy](features/F08-ban-giao-va-demo-local.md)

## Công việc và phụ thuộc

1. **[T01 — Nhập một nguồn mới và xem dữ liệu gốc](tickets/T01-nguon-moi-preview.md)** (F01). Bị chặn bởi: Chọn nguồn mới. Đầu ra: Mở ứng dụng Python mới, nhập một file nguồn mới được duyệt và xem bản ghi gốc kèm xuất xứ trong Streamlit.

2. **[T02 — Tải lại đúng phiên bản dataset và kiểm checksum](tickets/T02-tai-lai-va-checksum.md)** (F01). Bị chặn bởi: T01. Đầu ra: Người dùng tải đúng revision nguồn mới bằng lệnh, rồi thấy phiên bản và kết quả kiểm tra toàn vẹn trong dashboard.

3. **[T03 — Phân nhóm Backend, Frontend, Fullstack và Mobile](tickets/T03-vai-tro-phan-mem.md)** (F02). Bị chặn bởi: T01. Đầu ra: Người dùng xem/lọc bốn nhóm nghề phát triển phần mềm cạnh chức danh gốc và xuất các tin thuộc từng nhóm.

4. **[T04 — Bổ sung Data/ML, DevOps và QA Automation](tickets/T04-vai-tro-chuyen-biet.md)** (F02). Bị chặn bởi: T03. Đầu ra: Người dùng phân biệt đủ bảy nhóm nghề, gồm ba nhóm chuyên biệt, khi lọc bảng và xuất dữ liệu.

5. **[T05 — Chuẩn hóa HCM/HN và xem bảng alias](tickets/T05-dia-diem-hcm-hn.md)** (F02). Bị chặn bởi: T01. Đầu ra: Người dùng thấy tên địa điểm chuẩn HCM/HN cạnh chuỗi gốc, lọc và xuất theo tên thống nhất.

6. **[T06 — Giữ nhiều địa điểm, tách Remote và đếm tin duy nhất](tickets/T06-nhieu-dia-diem-remote.md)** (F02). Bị chặn bởi: T05. Đầu ra: Người dùng lọc một tin ở cả HCM/HN, lọc Remote riêng và thấy tổng số tin không tăng vì tách địa điểm.

7. **[T07 — Bóc tách ngôn ngữ lập trình có bằng chứng](tickets/T07-ky-nang-ngon-ngu.md)** (F02). Bị chặn bởi: T01. Đầu ra: Người dùng xem các ngôn ngữ lập trình trích từ tin, đoạn bằng chứng và bảng lọc/xuất theo kỹ năng.

8. **[T08 — Bổ sung framework, cơ sở dữ liệu và cloud](tickets/T08-ky-nang-framework-cloud.md)** (F02). Bị chặn bởi: T07. Đầu ra: Người dùng lọc/xuất các kỹ năng framework, database và cloud đã thống nhất alias, đồng thời xem bằng chứng nguồn.

9. **[T09 — Chuẩn hóa khoảng lương và đánh dấu nhãn hợp lệ](tickets/T09-nhan-luong.md)** (F02). Bị chặn bởi: T01. Đầu ra: Người dùng xem khoảng lương, trung điểm và đơn vị cạnh chuỗi gốc; tin chưa đủ nhãn được giữ với lý do.

10. **[T10 — Chuẩn hóa số năm và khoảng kinh nghiệm](tickets/T10-kinh-nghiem.md)** (F02). Bị chặn bởi: T01. Đầu ra: Người dùng xem kinh nghiệm đã chuẩn hóa, khoảng/cận hoặc trạng thái thiếu, và lọc/xuất để rà soát.

11. **[T11 — Đối chiếu chất lượng, nhóm trùng và xuất snapshot](tickets/T11-chat-luong-snapshot.md)** (F02). Bị chặn bởi: T02, T04, T06, T08, T09, T10. Đầu ra: Người dùng xem bảng sạch/review/trùng theo nguồn và xuất snapshot EDA cùng snapshot đủ nhãn huấn luyện.

12. **[T12 — Xem top nhu cầu kỹ năng theo bộ lọc](tickets/T12-top-nhu-cau.md)** (F03). Bị chặn bởi: T11. Đầu ra: Người dùng lọc nhóm nghề/địa điểm, xem top kỹ năng trong tin cùng bảng và tải PNG/CSV.

13. **[T13 — Xem xu hướng khi đủ thời gian nguồn](tickets/T13-xu-huong-thoi-gian.md)** (F03). Bị chặn bởi: T11. Đầu ra: Người dùng xem thay đổi theo kỳ thời gian so sánh được, hoặc thấy lý do nguồn chưa đủ để kết luận xu hướng.

14. **[T14 — Xem tương quan kinh nghiệm và lương](tickets/T14-kinh-nghiem-thu-nhap.md)** (F03). Bị chặn bởi: T11, Chốt đánh giá. Đầu ra: Người dùng xem scatter/tương quan kinh nghiệm–lương theo nhóm và tải bảng/ảnh có đơn vị.

15. **[T15 — So sánh lương theo vai trò và khu vực](tickets/T15-luong-vai-tro-khu-vuc.md)** (F03). Bị chặn bởi: T11, Chốt đánh giá. Đầu ra: Người dùng so sánh phân bố lương giữa bảy nhóm nghề và các khu vực với số mẫu hỗ trợ.

16. **[T16 — Xếp hạng kỹ năng theo lương có số mẫu](tickets/T16-luong-theo-ky-nang.md)** (F03). Bị chặn bởi: T11, Chốt đánh giá. Đầu ra: Người dùng xem kỹ năng có lương quan sát cao trong phạm vi dữ liệu, kèm n và giới hạn diễn giải.

17. **[T17 — Huấn luyện model đầu tiên và dự đoán một hồ sơ](tickets/T17-ridge-va-du-doan-don.md)** (F04). Bị chặn bởi: T11, Chốt đánh giá. Đầu ra: Người dùng train model đầu tiên bằng lệnh rồi nhập một hồ sơ trên Streamlit để dự đoán từ artifact đã lưu.

18. **[T18 — Huấn luyện model thứ hai và so sánh metric](tickets/T18-rf-va-so-sanh.md)** (F04). Bị chặn bởi: T17. Đầu ra: Người dùng train model thứ hai, xem bảng so sánh hai model và model được chọn bằng validation.

19. **[T19 — Xem sai số theo nhóm nghề và dữ liệu](tickets/T19-sai-so-phan-nhom.md)** (F05). Bị chặn bởi: T18, Chốt đánh giá. Đầu ra: Người dùng xem sai số và số mẫu theo nhóm để hiểu model hoạt động ở đâu.

20. **[T20 — Cảnh báo hồ sơ chưa đủ hỗ trợ khi dự đoán](tickets/T20-ho-tro-ho-so.md)** (F05). Bị chặn bởi: T18, Chốt đánh giá. Đầu ra: Người dùng nhập hồ sơ và nhận prediction hoặc trạng thái/cảnh báo theo mức dữ liệu hỗ trợ.

21. **[T21 — Gợi ý kỹ năng còn thiếu theo nhu cầu nghề](tickets/T21-tu-van-nhu-cau.md)** (F06). Bị chặn bởi: T20, Chốt tư vấn. Đầu ra: Người dùng nhận kỹ năng chưa có phù hợp nhóm nghề, kèm số tin yêu cầu và chứng cứ.

22. **[T22 — Bổ sung bằng chứng lương cho kỹ năng nên học](tickets/T22-tu-van-luong.md)** (F06). Bị chặn bởi: T21, Chốt tư vấn. Đầu ra: Người dùng xem thêm liên hệ lương và chênh lệch dự đoán của kỹ năng theo cách xếp hạng đã chốt.

23. **[T23 — Upload CSV, ghép cột và xem lỗi chuẩn hóa](tickets/T23-csv-mapping-preview.md)** (F07). Bị chặn bởi: T11. Đầu ra: Người dùng chọn CSV, ghép cột và xem raw–clean cùng lỗi từng dòng trước khi dự đoán.

24. **[T24 — Dự đoán hàng loạt CSV và xuất toàn bộ kết quả](tickets/T24-csv-batch-prediction.md)** (F07). Bị chặn bởi: T23, T20. Đầu ra: Từ CSV đã ghép cột, người dùng dự đoán dòng hợp lệ và tải kết quả của mọi dòng theo thứ tự gốc.

25. **[T25 — Hỗ trợ cùng quy trình upload với XLSX](tickets/T25-xlsx-full-flow.md)** (F07). Bị chặn bởi: T24. Đầu ra: Người dùng tải XLSX, ghép cột, rà lỗi, dự đoán và xuất kết quả tương đương CSV.

26. **[T26 — Tạo gói mã nguồn, dataset và artifact có manifest](tickets/T26-goi-ban-giao.md)** (F08). Bị chặn bởi: T12, T13, T14, T15, T16, T19, T22, T25. Đầu ra: Người báo cáo nhận gói dự án mới có đủ dữ liệu được phép phân phối, model, metric và hướng dẫn.

27. **[T27 — Cài mới và kiểm tra trọn demo offline](tickets/T27-demo-moi-truong-sach.md)** (F08). Bị chặn bởi: T26. Đầu ra: Người báo cáo cài từ gói nộp và demo biểu đồ, model, dự đoán, tư vấn, upload/export trên máy khi nguồn mạng bị tắt.

## Thứ tự làm

1. Cách chia việc đã được duyệt; đăng issue triển khai và giữ các bước phụ thuộc nguồn ở trạng thái bị chặn đến khi quyết định nguồn đủ dùng được chốt.
2. Mở ứng dụng mới với một nguồn đã kiểm chứng.
3. Có thể làm độc lập các lát cắt nhóm nghề, địa điểm, kỹ năng, lương/kinh nghiệm sau khi hợp đồng đầu vào chung đã ổn định.
4. Biểu đồ tuyển dụng có thể đi trước phần huấn luyện khi dữ liệu kỹ năng/nghề/địa điểm đã đạt. Biểu đồ lương và huấn luyện cần thêm nhãn lương cùng quyết định đánh giá.
5. Huấn luyện model đầu tiên → model thứ hai/so sánh → dự đoán có trạng thái hỗ trợ.
6. Tư vấn và upload có thể làm song song sau phần dự đoán; tư vấn còn cần quyết định bằng chứng.
7. Kiểm tra trọn gói bàn giao sau khi các nhánh biểu đồ, tư vấn và upload đều hoàn tất.

## Truy vết đề bài

| Yêu cầu | Spec | Công việc | Bằng chứng nghiệm thu |
| --- | --- | --- | --- |
| Đọc/làm sạch; xử lý chuỗi; tách kỹ năng; chuẩn lương/kinh nghiệm | F01–F02 | T01–T11 | Dataset mới, raw–clean, bảng review, quy tắc nhãn và file xuất |
| Top nhu cầu và kỹ năng lương cao | F03 | T12/T16 | Biểu đồ/bảng thật, n, đơn vị và nguồn |
| Kinh nghiệm–thu nhập; vai trò/khu vực–lương | F03 | T14–T15 | Scatter/correlation, bảng và biểu đồ so sánh |
| Ít nhất hai mô hình, hai metric | F04–F05 | T17–T20 | Artifact, prediction/nhãn, metric tính lại, reload parity |
| Kỹ năng có liên hệ gia tăng thu nhập | F03/F06 | T16/T21–T22 | Thống kê/gợi ý có số mẫu, phạm vi và giới hạn |
| Nhập hồ sơ → lương dự đoán và kỹ năng nên học | F05–F06 | T17/T20–T22 | Demo form thật từ model đã lưu |
| Python; Matplotlib/Seaborn; không pretrained/fine-tune | F01/F03/F04 | T01/T12–T18 | Môi trường, thư viện biểu đồ và quy trình train mới |
| Mã nguồn, dataset, ứng dụng demo | F08 | T26–T27 | Gói nộp có dataset và demo kiểm tra từ môi trường mới |
| Upload CSV/XLSX, lỗi theo dòng, không train qua UI | F07 | T23–T25 | Demo file đúng/sai, export đầy đủ, artifact không đổi |

## Quyết định trước triển khai

- [Chọn nguồn dataset Việt Nam mới có thể kiểm chứng](https://github.com/theihoz/ML/issues/3): nghiên cứu độc lập đang chạy.
- [Chốt cách đánh giá lương và xử lý hồ sơ ít bằng chứng](https://github.com/theihoz/ML/issues/4): chờ dữ liệu nguồn mới.
- [Chốt bằng chứng và cách xếp hạng kỹ năng nên học](https://github.com/theihoz/ML/issues/5): chờ dữ liệu nguồn mới.

Các quyết định này là decision ticket của wayfinder, khác với công việc triển khai; không gắn nhãn ready-for-agent cho chúng.

## Đăng theo bản đã duyệt

Đã đăng spec và công việc vào GitHub Issues của theihoz/ML, gắn ready-for-agent cho spec tổng thể và công việc triển khai, nối parent/sub-issue và blocking bằng quan hệ native; đã đọc lại kiểm chứng. Trạng thái blocked vẫn dựa trên quyết định và công việc chưa xong; không bắt đầu ticket chỉ vì nó có nhãn.


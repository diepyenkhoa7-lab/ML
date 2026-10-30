# Bản chia ticket ML — 30/10/2026

Trạng thái: **đã duyệt, đăng và đọc lại xác minh ngày 30/10/2026**. Nhánh dev/ml-development, nguồn spec ML/26 AC và ADR0006–0009. Đã tạo 23 issue con và 33 blocker native ở theihoz/ML; nội dung/trạng thái/nhãn parent và graph 27 ticket cũ giữ nguyên. Code ML chưa push.

Hiện có hai nhãn được duyệt từ một công ty, chưa nhập canonical. Không có training readiness. Policy nguyên tắc đã thống nhất; ngưỡng bằng số còn phải khóa theo dữ liệu trước fit. Cặp model duy nhất ở bản mới: **Ridge + Linear Regression**; MAE chính, RMSE phụ.

## Bản chia đã đăng

1. **[ML01 — Nhập chứng cứ nhãn đã duyệt vào snapshot và trang chất lượng](tickets/ML01.md) · [#43](https://github.com/theihoz/ML/issues/43)**
   - **Blocked by:** Không có blocker mới.
   - **Đầu ra:** Người dùng nhập ledger đã duyệt và xem nhãn bổ sung cùng lineage trên CLI/Streamlit, trong khi training vẫn bị chặn.
   - **Parent:** #6; truy vết T09/T11; AC01/AC02/AC03/AC04.

2. **[ML02 — Đối chiếu công ty và nhóm trùng trước chia tập](tickets/ML02.md) · [#44](https://github.com/theihoz/ML/issues/44)**
   - **Blocked by:** Không có blocker mới.
   - **Đầu ra:** Người kiểm toán xem bảng alias công ty, quan hệ tin trùng/đăng lại và nhóm giữ cùng tập, có export bằng chứng.
   - **Parent:** #31; truy vết T11/T17; AC03/AC05.

3. **[ML03 — Mở form dự đoán với trạng thái chưa có model](tickets/ML03.md) · [#45](https://github.com/theihoz/ML/issues/45)**
   - **Blocked by:** Không có blocker mới.
   - **Đầu ra:** Người dùng có form hồ sơ và CLI kiểm tra đầu vào; khi chưa có artifact, nhận trạng thái rõ và không có số lương.
   - **Parent:** #31; truy vết T17/T20; AC16/AC17/AC20.

4. **[ML04 — Mở rộng và kiểm duyệt nhãn từ nhiều công ty](tickets/ML04.md) · [#46](https://github.com/theihoz/ML/issues/46)**
   - **Blocked by:** Không có blocker mới.
   - **Đầu ra:** Tạo đợt hồ sơ nguồn/nhãn mới có kiểm duyệt, số mẫu thật và khoảng trống đủ rõ để quyết định gate dữ liệu.
   - **Parent:** #42; truy vết #42; AC02/AC03/AC04/AC24.

5. **[ML05 — Áp dụng policy đã khóa và hiển thị readiness](tickets/ML05.md) · [#47](https://github.com/theihoz/ML/issues/47)**
   - **Blocked by:** ML01, ML02, #4, #5.
   - **Đầu ra:** CLI và trang chất lượng cho biết cohort nào ready hoặc blocked theo cấu hình đã chấp nhận, không chỉ dựa vào n>0.
   - **Parent:** #31; truy vết T11/T17/T20; AC04/AC16/AC20/AC26.

6. **[ML06 — Khóa split theo công ty và xuất manifest](tickets/ML06.md) · [#48](https://github.com/theihoz/ML/issues/48)**
   - **Blocked by:** ML05.
   - **Đầu ra:** Người huấn luyện xem hoặc xuất phân hoạch 70/15/15 theo mục tiêu, hoặc nhận lý do không tạo được split hợp lệ.
   - **Parent:** #31; truy vết T17; AC05/AC06/AC07.

7. **[ML07 — Train Ridge ngoại tuyến và xem báo cáo ứng viên](tickets/ML07.md) · [#49](https://github.com/theihoz/ML/issues/49)**
   - **Blocked by:** ML06, #42.
   - **Đầu ra:** Chạy lệnh train Ridge trên dữ liệu thật đã chấp nhận, xem baseline và kết quả validation trên trang run.
   - **Parent:** #31; truy vết T17; AC08/AC10/AC11.

8. **[ML08 — Train Linear Regression trên cùng split](tickets/ML08.md) · [#50](https://github.com/theihoz/ML/issues/50)**
   - **Blocked by:** ML07, #42.
   - **Đầu ra:** Train Linear Regression độc lập và xem hai ứng viên trên cùng snapshot/features/split với Ridge.
   - **Parent:** #32; truy vết T18; AC08/AC10/AC11.

9. **[ML09 — Chọn bằng validation và đánh giá điều kiện phát hành](tickets/ML09.md) · [#51](https://github.com/theihoz/ML/issues/51)**
   - **Blocked by:** ML08.
   - **Đầu ra:** Trang so sánh cho biết model được chọn, kết quả test riêng và trạng thái đủ/chưa đủ điều kiện demo.
   - **Parent:** #32; truy vết T18; AC09/AC11/AC12.

10. **[ML10 — Nạp và kích hoạt artifact có kiểm tra toàn vẹn](tickets/ML10.md) · [#52](https://github.com/theihoz/ML/issues/52)**
   - **Blocked by:** ML09.
   - **Đầu ra:** Nạp lại pipeline trong tiến trình mới, chỉ kích hoạt run đạt policy; artifact thiếu/hỏng không làm mất model tốt trước.
   - **Parent:** #31; truy vết T17/T20; AC10/AC15/AC16.

11. **[ML11 — Dự đoán một hồ sơ và từ chối khi thiếu hỗ trợ](tickets/ML11.md) · [#53](https://github.com/theihoz/ML/issues/53)**
   - **Blocked by:** ML03, ML10.
   - **Đầu ra:** Form và CLI trả prediction có nguồn gốc khi được hỗ trợ, hoặc trạng thái/reason và prediction null.
   - **Parent:** #34; truy vết T17/T20; AC15/AC16/AC17.

12. **[ML12 — Xem sai số theo nhóm và tải báo cáo có provenance](tickets/ML12.md) · [#54](https://github.com/theihoz/ML/issues/54)**
   - **Blocked by:** ML09.
   - **Đầu ra:** Người dùng lọc sai số theo nghề, kinh nghiệm, địa điểm và tải bảng/ảnh đúng phạm vi đánh giá.
   - **Parent:** #33; truy vết T19; AC11/AC12/AC13.

13. **[ML13 — Xem kỹ năng đủ bằng chứng cho hồ sơ](tickets/ML13.md) · [#55](https://github.com/theihoz/ML/issues/55)**
   - **Blocked by:** ML11.
   - **Đầu ra:** Người dùng xem những kỹ năng chưa có mà train của model có đủ bằng chứng để xét tư vấn.
   - **Parent:** #35; truy vết T21; AC18/AC20.

14. **[ML14 — Gợi ý tối đa ba kỹ năng theo delta dự đoán](tickets/ML14.md) · [#56](https://github.com/theihoz/ML/issues/56)**
   - **Blocked by:** ML13.
   - **Đầu ra:** Form tư vấn trả top3 kỹ năng hợp lệ theo chênh lệch model của chính hồ sơ người dùng.
   - **Parent:** #36; truy vết T21/T22; AC18/AC19/AC20.

15. **[ML15 — Phân tích giá trị kỹ năng theo model và xuất kết quả](tickets/ML15.md) · [#57](https://github.com/theihoz/ML/issues/57)**
   - **Blocked by:** ML14.
   - **Đầu ra:** Dashboard có báo cáo kỹ năng giá trị cao theo model với tập/cách tính/n và export tái lập.
   - **Parent:** #36; truy vết T22; AC14/AC19.

16. **[ML16 — Vẽ kinh nghiệm và thu nhập có kiểm soát số mẫu](tickets/ML16.md) · [#58](https://github.com/theihoz/ML/issues/58)**
   - **Blocked by:** ML01, #4.
   - **Đầu ra:** Xem biểu đồ kinh nghiệm–thu nhập từ nhãn đã được chấp nhận hoặc thông báo thiếu bằng chứng.
   - **Parent:** #28; truy vết T14; AC02/AC13.

17. **[ML17 — So sánh thu nhập theo nghề và địa điểm](tickets/ML17.md) · [#59](https://github.com/theihoz/ML/issues/59)**
   - **Blocked by:** ML01, #4.
   - **Đầu ra:** Xem bảng/biểu đồ thu nhập quan sát theo nghề hoặc địa điểm và tải đúng dữ liệu đã lọc.
   - **Parent:** #29; truy vết T15; AC13.

18. **[ML18 — Xếp hạng kỹ năng theo thu nhập quan sát](tickets/ML18.md) · [#60](https://github.com/theihoz/ML/issues/60)**
   - **Blocked by:** ML01, #4.
   - **Đầu ra:** Xem kỹ năng gắn với mức thu nhập quan sát, có n và giới hạn cho từng nhóm.
   - **Parent:** #30; truy vết T16; AC13/AC14.

19. **[ML19 — Dự đoán CSV và xuất đủ mọi dòng](tickets/ML19.md) · [#61](https://github.com/theihoz/ML/issues/61)**
   - **Blocked by:** ML11.
   - **Đầu ra:** Mở rộng preview CSV hiện có thành batch prediction từ artifact đã lưu và tải kết quả đầy đủ.
   - **Parent:** #38; truy vết T24; AC21/AC23.

20. **[ML20 — Preview XLSX, chọn sheet và đối chiếu mapping](tickets/ML20.md) · [#63](https://github.com/theihoz/ML/issues/63)**
   - **Blocked by:** Không có blocker mới.
   - **Đầu ra:** Upload XLSX, chọn sheet và xem chuẩn hóa/lỗi trước khi dự đoán, dùng cùng hợp đồng hồ sơ như CSV.
   - **Parent:** #39; truy vết T25; AC22.

21. **[ML21 — Dự đoán XLSX và đối chiếu CSV/form](tickets/ML21.md) · [#64](https://github.com/theihoz/ML/issues/64)**
   - **Blocked by:** ML19, ML20.
   - **Đầu ra:** File XLSX đã mapping nhận batch prediction cùng kết quả và thứ tự như CSV/form, có download.
   - **Parent:** #39; truy vết T25; AC21/AC22/AC23.

22. **[ML22 — Đóng gói mã nguồn, dataset và model có manifest](tickets/ML22.md) · [#65](https://github.com/theihoz/ML/issues/65)**
   - **Blocked by:** ML12, ML15, ML16, ML17, ML18, ML21.
   - **Đầu ra:** Tạo gói nộp chỉ gồm dự án mới, dữ liệu được phép bàn giao và model/run thật có chứng cứ.
   - **Parent:** #40; truy vết T26; AC24/AC26.

23. **[ML23 — Cài mới và nghiệm thu demo offline](tickets/ML23.md) · [#66](https://github.com/theihoz/ML/issues/66)**
   - **Blocked by:** ML22.
   - **Đầu ra:** Cài gói ở môi trường mới và thực hiện trọn kịch bản báo cáo khi demo không dùng mạng.
   - **Parent:** #41; truy vết T27; AC15/AC24/AC25/AC26.

## Frontier và các thay đổi phụ thuộc đã duyệt

- Có thể bắt đầu: ML01, ML02, ML03, ML04, ML20. T23 preview CSV hiện có đã hoàn tất, không tạo lại ticket đó.
- ML01/ML02/ML03/ML20 là chức năng dữ liệu/trạng thái/preview, không fit; không cho gate #42 chặn chúng một cách giả tạo.
- ML04 cung cấp bằng chứng cho #42 và số liệu để chốt tham số #4/#5. Không coi ML04 hoàn tất là tự đóng gate. Người dùng cần duyệt các tham số thật trước khi issue quyết định tương ứng được giải quyết; ML05 chỉ áp dụng policy đã khóa, không tự đặt ngưỡng.
- ML05 phụ thuộc ML01/ML02 và #4/#5. #4/#5 không phụ thuộc code ML05; việc chốt tham số dùng bằng chứng ML04, tránh vòng lặp dependency.
- ML07/ML08 chỉ fit sau #42 và readiness/split hợp lệ. Artifact/inference/advice thành công ở phía sau; fixture không thay nghiệm thu train thật.
- ML16–ML18 là EDA lương quan sát, chỉ cần nhãn đã duyệt và policy thống kê; không chờ model như metric ML. Nếu thiếu mẫu, hiển thị trạng thái/n, không kết luận mạnh từ hai tin. Đây là điều chỉnh thứ tự đã duyệt so với phần còn chặn trong graph cũ.
- ML20 tách preview XLSX khỏi prediction: preview có thể làm trước T24/ML19; ML21 mới chờ batch CSV. Thay đổi dependency này đã được duyệt.
- Không tạo lại T01–T13/T23 đã hoàn tất hoặc mở lại toàn bộ audit đã sửa. AC01–AC03 ở đây là bảo vệ nhập nhãn/grouping, không phải ticket sửa lại parser.
- Các tên MLxx là ID của lát cắt, đã ánh xạ sang issue thật trong ticket-graph.json và ticket-publication.json. Parent cũ giữ nguyên, các ticket mới thu hẹp các phần việc còn lại; không chạy cả parent và child như hai bản triển khai trùng nhau.

## Kiểm thử và nghiệm thu

Giữ seam đã duyệt. 26 AC đều có ticket chịu trách nhiệm; AC08 chỉ đủ sau khi cả hai mô hình thực đã fit, không đánh dấu đạt từ ML07 riêng. Bản chia không tuyên bố AC đã đạt. Không viết test thay thế dữ liệu hoặc huấn luyện bằng fixture.

## Xác minh publication

23 issue đều mở, mang ready-for-agent, có đúng parent và tập blocker native theo bản duyệt; body hash khớp nội dung đã gửi. Đã đọc lại parent để xác nhận không đổi title/body/state/labels. Các thay đổi native chỉ thêm quan hệ child/blocker. Không đóng gate #4/#5/#42, không train, không push code; parent là đầu mục tổng hợp, không chạy trùng với các child. Bằng chứng đọc lại nằm trong ticket-publication.json.

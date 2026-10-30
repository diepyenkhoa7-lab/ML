# Review lại luồng đặc tả theo ask-matt

Ngày 28/10/2026. Phạm vi: tài liệu hiện có trong repo và trạng thái GitHub Issues được đọc trực tiếp bằng gh. Phiên này không có công cụ read_thread; chưa đọc được chat được dẫn, vì vậy không kết luận về toàn bộ diễn biến hoặc các câu trả lời chỉ nằm trong chat đó. Đề gốc đã được người dùng dán vào chat đánh giá trước.

## Kết luận hiện tại

Đã có SPEC.md, tám nhóm tính năng và 13 ticket nháp. Nhận định "chưa có spec" trong lần nghiên cứu trước không còn phản ánh trạng thái hiện tại. Spec mới bao phủ xử lý dữ liệu, các biểu đồ bắt buộc, hai model tự train và ít nhất hai metric, phân tích kỹ năng, dự đoán/tư vấn, Python và cấm pretrained, cùng sản phẩm bàn giao. Phần đã xác nhận và phần đề xuất được tách rõ; chưa coi draft là sản phẩm đã triển khai.

Luồng đang phù hợp với ask-matt: làm rõ domain, nghiên cứu các quyết định còn mở, tổng hợp spec, duyệt cách chia ticket rồi mới triển khai. Trong repo, grill-with-docs là lối vào có lưu glossary/ADR; wayfinder chỉ cần cho phần còn nhiều bất định. Không cần phỏng vấn lại toàn bộ dự án hoặc mở thêm bản đồ song song. [Nguồn chính thức: ask-matt](https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md).

## Phát hiện cần xử lý

### P2 — Đưa khử trùng thành đầu ra dùng chung trước biểu đồ

T06 yêu cầu thống kê theo tin duy nhất; T07 cũng phải dùng các quan sát đã làm sạch. Nhưng công việc nhóm tin trùng cụ thể hiện được giao cho T08, là nhánh huấn luyện mà T06/T07 không phụ thuộc. F02 nói chuẩn hóa trước nhóm trùng, chưa giao rõ bước tạo ID/nhóm tin chuẩn cho ticket nào. Nếu mỗi nhánh tự xử lý, biểu đồ và model có thể dùng số tin khác nhau; nếu chờ T08, các ticket biểu đồ không còn độc lập như đồ thị đang mô tả.

Đề xuất: chốt ID tin, quy tắc nhóm bản sao/tin đăng lại và artifact dùng chung ở bước dữ liệu trước T06/T07; dashboard báo số dòng thô, nhóm trùng và tin giữ lại. T08 dùng lại kết quả đó rồi bảo đảm nhóm không giao nhau giữa các tập. Quy tắc cụ thể phải dựa trên nguồn được chọn.

Vị trí: tickets/T06-nhu-cau-va-thoi-gian.md:11; tickets/T08-model-dau-tien-va-du-doan.md:11; features/F02-chuan-hoa-va-chat-luong.md:26.

### P2 — Chốt nhãn cho lương cố định, phân biệt với khoảng một cận

T05 có nhiệm vụ phân tích lương cố định nhưng acceptance criteria mới xác định khoảng hai cận và loại khoảng một cận. SPEC/ADR hiện mô tả target trung điểm của khoảng. Nghiên cứu nguồn trên GitHub lại chấp nhận cả lương cố định. Chưa rõ tin "25 triệu VND/tháng" được dùng làm target 25 triệu hay bị loại vì chỉ có một con số.

Đề xuất bổ sung quyết định và ví dụ: mức cố định có đơn vị rõ được giữ nguyên làm target, có thể biểu diễn min=max; "từ 25 triệu" hoặc "tối đa 25 triệu" vẫn là một cận và không thành target chính. Không tự suy mức cố định từ chuỗi thiếu chứng cứ. Đây là đề xuất cần chốt, không phải thay ADR đã được người dùng xác nhận.

Vị trí: tickets/T05-luong-kinh-nghiem-chat-luong.md:11; SPEC.md:65; quyết định nguồn trên GitHub.

## Những phần đã kiểm chứng là hợp lý

- SPEC tách lựa chọn Python/Streamlit, nguồn mới và Việt Nam là chính khỏi các thiết kế vẫn là đề xuất như Ridge/Random Forest, metric cụ thể và ngưỡng hỗ trợ.
- PLAN có bảng truy vết đề tới feature, ticket và bằng chứng nghiệm thu.
- Các ticket có đầu ra người dùng kiểm chứng được; tách dự đoán model đầu tiên, so sánh model thứ hai, tư vấn và upload thành những phần có thể demo.
- Đồ thị JSON có 13 ticket, không có chu trình; mọi depends_on khớp phần Blocked by trong Markdown. Đây là kiểm tra cấu trúc, không chứng minh các hợp đồng nghiệp vụ đã đầy đủ.
- GitHub có bản đồ với ba sub-issue; nghiên cứu nguồn đã có assignee. Hai quyết định đánh giá và tư vấn đều bị chặn bởi nghiên cứu nguồn bằng quan hệ native. Các quyết định vẫn mở và chưa có resolution comment tại thời điểm đọc. [Bản đồ](https://github.com/theihoz/ML/issues/2), [nguồn mới](https://github.com/theihoz/ML/issues/3), [đánh giá](https://github.com/theihoz/ML/issues/4), [tư vấn](https://github.com/theihoz/ML/issues/5).
- Chưa đăng ticket triển khai là phù hợp với trạng thái bản nháp chờ duyệt cách chia việc. Không dùng việc chưa publish làm lỗi quy trình khi tài liệu đã ghi rõ đang chờ bước này. [Nguồn chính thức: to-tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md).

## Bước tiếp theo theo ask-matt

1. Hoàn thành quyết định nguồn: file thật, schema, số tin duy nhất, số mẫu có lương hợp lệ, độ phủ và khả năng bàn giao. Trạng thái issue/assignee không tự chứng minh nghiên cứu đã hoàn tất.
2. Dùng bằng chứng nguồn để chốt cách đánh giá và tư vấn. Nếu thiết kế tư vấn dùng chênh lệch dự đoán, cập nhật quan hệ chặn khi cần kết quả từ quyết định đánh giá, thay vì mặc nhiên coi hai quyết định độc lập.
3. Bổ sung hai hợp đồng ở trên vào draft; tổng hợp quyết định đã chốt vào spec cuối và xác nhận điểm kiểm thử. to-spec đầy đủ bao gồm xuất bản lên tracker; draft local hiện tại chưa đồng nghĩa đã chạy xong bước này. [Nguồn chính thức: to-spec](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md).
4. Duyệt độ nhỏ của ticket và phụ thuộc, rồi xuất bản các ticket triển khai. Bắt đầu ticket có blocker đã giải quyết; giữ phần còn lại bị chặn. Chưa cần chạy implement-spec cho toàn dự án ở trạng thái này.

Review này không sửa SPEC, ADR, ticket hoặc GitHub Issues. Không chạy training hay công bố chất lượng mô hình.

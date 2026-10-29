# Spec phát triển các chức năng ML

Trạng thái: đặc tả phát triển ngày 29/10/2026, bổ sung cho spec tổng thể #6. Chưa huấn luyện hoặc gỡ gate #42/#4/#5. Seam MarketService, CLI và smoke Streamlit giữ theo phạm vi kiểm thử người dùng đã duyệt.

## Problem Statement

Ứng dụng hiện phân tích dữ liệu và preview CSV nhưng chưa có mô hình lương. Hai nguồn mới có 3.606 dòng thô; pipeline đang báo 322 tin EDA và 0 nhãn VND/tháng đủ điều kiện. Audit bổ sung phát hiện lỗi chuẩn hóa/định danh/phân nhóm cần sửa trước khi dùng dữ liệu cho ML; các số đếm EDA hiện tại phải được kiểm toán lại, không coi là chứng nhận dữ liệu sạch.

Người dùng cần tự huấn luyện ít nhất hai mô hình, đánh giá bằng ít nhất hai metric, dự đoán lương chào tuyển và tư vấn kỹ năng bằng bằng chứng thật, demo trực tiếp trên máy.

## Solution

Một quy trình Python từ kiểm toán nhãn → khóa snapshot → chia nhóm/chống rò nhãn → huấn luyện ngoại tuyến → đánh giá/chọn model → nạp artifact cho suy luận/tư vấn. Streamlit trình bày model và dữ liệu đã lưu, không huấn luyện khi mở trang hoặc upload.

Khi thiếu dữ liệu, chính sách đánh giá hoặc artifact tương thích, ứng dụng trả trạng thái có lý do và không tạo con số lương. Các phần kiểm tra hợp đồng, cấu hình và trạng thái bị chặn có thể phát triển trước; việc fit model và nghiệm thu chất lượng phải chờ dữ liệu thật được chấp nhận.

## User Stories

1. Là người huấn luyện, tôi muốn biết dataset đã đủ nhãn chưa, để tránh train trên mức lương tự suy đoán.
2. Là người kiểm toán, tôi muốn truy từng target về bản ghi và chứng cứ tiền tệ/kỳ, để xác minh nhãn.
3. Là người kiểm toán, tôi muốn thấy khoảng/cận, gross/net và lý do loại, để không đánh đồng các loại lương.
4. Là người phân tích, tôi muốn giữ tin không đủ nhãn trong EDA, để không làm lệch nhu cầu tuyển dụng.
5. Là người huấn luyện, tôi muốn khóa phiên bản dữ liệu và quy tắc, để tái lập một run.
6. Là người huấn luyện, tôi muốn tin trùng/đăng lại nằm cùng nhóm chia tập, để tránh đánh giá trên bản sao đã học.
7. Là người huấn luyện, tôi muốn feature chỉ từ thông tin hồ sơ được phép nhập, để tránh rò lương từ tiêu đề hoặc nội dung.
8. Là người huấn luyện, tôi muốn preprocessing chỉ học từ train, để validation/test thực sự độc lập.
9. Là người huấn luyện, tôi muốn chạy Ridge và Random Forest tự khởi tạo, để có hai mô hình thực đáp ứng đề bài.
10. Là người đánh giá, tôi muốn hai model dùng cùng split, để so sánh công bằng.
11. Là người đánh giá, tôi muốn xem MAE/RMSE cùng VND/tháng và số mẫu, để hiểu sai số.
12. Là người đánh giá, tôi muốn R² không xác định được ghi rõ, để không đọc một giá trị giả.
13. Là người đánh giá, tôi muốn chọn model bằng validation và giữ test riêng, để tránh chọn theo đáp án cuối.
14. Là người phân tích, tôi muốn xem lỗi theo nghề, kinh nghiệm và địa điểm, để biết vùng model chưa đủ hỗ trợ.
15. Là người demo, tôi muốn nạp lại model trong tiến trình mới, để xác nhận artifact chứa đủ preprocessing.
16. Là người dùng, tôi muốn nhập vai trò, kinh nghiệm, kỹ năng, địa điểm và hình thức, để nhận ước tính trong phạm vi model.
17. Là người dùng, tôi muốn biết model/dataset/đơn vị/gross-net của kết quả, để diễn giải đúng lương chào tuyển.
18. Là người dùng, tôi muốn được cảnh báo hoặc từ chối khi hồ sơ chưa đủ hỗ trợ, để không tin vào con số vô căn cứ.
19. Là người dùng, tôi muốn nhận kỹ năng chưa có phù hợp nghề, để cân nhắc học thêm.
20. Là người dùng, tôi muốn thấy số tin, liên hệ lương và chênh lệch model riêng biệt, để không hiểu chúng là quan hệ nhân quả.
21. Là người dùng, tôi muốn CSV/XLSX giữ đầy đủ dòng lỗi và thứ tự, để đối chiếu với file gốc.
22. Là người dùng, tôi muốn hồ sơ đơn và hồ sơ trong file cho cùng kết quả, để tránh hai bộ quy tắc khác nhau.
23. Là người demo, tôi muốn dự đoán/tư vấn khi tắt mạng sau khi chuẩn bị môi trường, để báo cáo ổn định.
24. Là người bàn giao, tôi muốn đủ mã nguồn mới, dataset được phép phân phối và model đã đánh giá, để người khác cài và chạy lại.

## Implementation Decisions

### Ràng buộc đã xác nhận

- Toàn bộ ứng dụng dùng Python/Streamlit; Việt Nam là phạm vi chính. Không pretrained, fine-tune, LLM, embedding có sẵn, model/code/dataset cũ hoặc dịch vụ dự đoán bên ngoài.
- MarketService giữ một ranh giới nghiệp vụ chung cho chuẩn hóa, kiểm tra readiness, train, đánh giá, nạp artifact, dự đoán và tư vấn. Adapter CLI/Streamlit chỉ nhận/hiển thị kết quả.
- Đơn vị mục tiêu chính là VND/tháng. Khoảng đủ chứng cứ dùng trung điểm, giữ hai đầu. Một cận/thỏa thuận/thiếu kỳ hoặc tiền tệ không thành target chính. Không tự đổi ngoại tệ hay gross/net.
- Quyết định ngày 29/10: nhóm chưa rõ gross/net được giữ riêng, không trộn với gross hoặc net đã xác nhận. Cohort/model/kết quả phải ghi basis; đủ tiền tệ và kỳ vẫn chưa thay các điều kiện readiness còn lại.
- Một tin là một quan sát dù có nhiều kỹ năng/địa điểm. Tách row nguồn, thực thể tin và nhóm chống leakage; không bỏ tham số định danh khi chỉ cần bỏ tracking.
- Trước khi khóa snapshot ML phải sửa/kiểm tra các lỗi audit có thể làm sai nhãn, nghề, Remote, bằng chứng và nhóm tin. Không dùng trạng thái parser “valid” làm chứng cứ duy nhất cho một target.
- Feature theo allowlist: vai trò, kinh nghiệm có biểu diễn khoảng/cận, kỹ năng chuẩn, địa điểm chuẩn và hình thức làm việc. Tiêu đề/JD nguyên văn, số tiền, cận lương, target, lý do suy từ target, ID/URL/công ty và trường nguồn chỉ phục vụ kiểm toán/nhóm/báo cáo; không tự đưa vào model.
- Alias/quy tắc được đóng phiên bản; vocabulary encoder, imputer và scaler chỉ fit train. Kỹ năng/nhóm chưa gặp không âm thầm biến thành hồ sơ được hỗ trợ.
- Snapshot, split, cấu hình, seed, feature schema, target policy, phiên bản thư viện và artifact có hash/ID. Run lỗi hoặc bị ngắt không thay model đang dùng.
- Dashboard chỉ dùng artifact nội bộ đã được kiểm tra. Không nhận model từ upload. Suy luận không ghi đè training snapshot hoặc tự fit lại.

### Đề xuất cần chốt qua các quyết định còn mở

- #4: Ridge và Random Forest là hai ứng viên khởi đầu; thêm baseline trung vị chỉ để tham chiếu, không thay một trong hai model yêu cầu. Chọn bằng validation MAE, báo MAE/RMSE/R² trên cùng split và đơn vị gốc.
- #4: chia theo nhóm tin với seed cố định; phương án grouped 70/15/15, seed 42 chỉ là đề xuất. Temporal holdout chỉ dùng khi ngày và sampling frame đủ phù hợp; không lấy hai snapshot khác nền tảng làm bằng chứng xu hướng thời gian.
- #4: basis đã chốt giữ riêng từng nhóm; còn phải chốt kinh nghiệm thiếu/khoảng/cận, số nhóm tối thiểu, outlier, ngưỡng hỗ trợ và tiêu chí chấp nhận model sau kiểm toán nhãn. Chưa có quyết định thì readiness tiếp tục bị chặn; không dùng ngưỡng mặc định tùy tiện để mở train.
- #5: tối đa ba kỹ năng chưa có; dùng nhu cầu từ train và thử thêm từng kỹ năng vào cùng hồ sơ nền. Cách phối hợp tín hiệu và ngưỡng phải được chốt; không dùng test để chọn danh sách hay tham số xếp hạng.

## Testing Decisions

- Mỗi chức năng có tiêu chí nghiệm thu trong ACCEPTANCE; bằng chứng triển khai phải phân biệt test logic với đánh giá model thật và demo môi trường sạch. Các tiêu chí hiện là yêu cầu, chưa được đánh dấu đạt.
- Test hành vi qua MarketService, CLI, Streamlit và nạp lại trong tiến trình mới, kế thừa seam đã duyệt. Không mock model hoặc kiểm tra private collaborator để thay bằng chứng chạy thật.
- Fixture tổng hợp nhỏ chỉ kiểm logic như cổng dữ liệu, chia nhóm, metric tính tay và trạng thái lỗi; không đi vào training/đánh giá chất lượng, dataset nộp hoặc metric thị trường. Test fit/save/reload phải dùng tập con mới có nhãn thật đã được xác minh sau gate dữ liệu.
- Chứng minh không giao nhóm giữa train/validation/test; preprocessing không học vocabulary/thống kê từ phần giữ lại; feature không chứa lương hoặc văn bản nguyên có lương.
- Hai model thực học từ cùng snapshot/split; recompute metric từ y_true/prediction đã lưu. Test không quyết định champion hoặc danh sách tư vấn.
- Kiểm tra artifact thiếu/hỏng/sai hash/schema/basis, hồ sơ âm/thiếu/OOV, kết quả không hữu hạn và trạng thái hỗ trợ. Không cắt/điền 0 prediction để che lỗi.
- Luồng đơn/batch dùng cùng artifact và chuẩn hóa; giữ thứ tự và mọi lỗi, CSV/XLSX tương đương, không đổi model/snapshot.
- Khi n=0 hoặc policy chưa chốt: train dừng trước fit, không xuất model/metric thành công, dashboard không hiển thị dự đoán giả.

## Out of Scope

Mở gate #42 chỉ bằng việc có code ML; dùng lại dữ liệu cũ; điền tiền tệ/kỳ theo thói quen; train bằng fixture; bảo đảm một mức accuracy trước đánh giá; cam kết học kỹ năng gây tăng lương; cloud/deploy, tài khoản, thanh toán hoặc báo cáo Word.

## Further Notes

Tám spec M01–M08 trong danh mục ML làm rõ các F04–F08 và ticket hiện có, không tự thay 27 ticket đã duyệt. F03/T14–T16 tiếp tục mô tả thống kê lương quan sát, tách khỏi feature importance hoặc chênh lệch dự đoán. Việc chia nhỏ lại ticket và đổi dependency là bước riêng sau khi duyệt phạm vi, không diễn ra trong lần viết spec này.

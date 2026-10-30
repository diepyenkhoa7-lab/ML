# Spec phát triển các chức năng ML

Trạng thái: đặc tả phát triển ngày 29/10/2026, bổ sung cho spec tổng thể #6. Chưa huấn luyện hoặc gỡ gate #42/#4/#5. Seam MarketService, CLI và smoke Streamlit giữ theo phạm vi kiểm thử người dùng đã duyệt.

## Problem Statement

Ứng dụng hiện phân tích dữ liệu và preview CSV nhưng chưa có mô hình lương. Hai nguồn mới có 3.606 dòng thô; sau sửa audit, pipeline eda-v5 có 320 tin EDA và 0 target từ cột salary. Kiểm duyệt ngày 29/10 chấp nhận hai nhãn thu nhập tháng chào tuyển có chứng cứ cùng tin vào file riêng; chưa ghép vào pipeline hoặc mở train. Hai nhãn cùng nghề/công ty/ngày không đủ chia ba tập độc lập. Các trường hợp khác vẫn giữ trạng thái review/loại và bằng chứng riêng, không coi số đếm EDA là chứng nhận mọi tin đã được review thủ công.

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
9. Là người huấn luyện, tôi muốn chạy Ridge và Linear Regression tự khởi tạo, để có hai mô hình thực đáp ứng đề bài.
10. Là người đánh giá, tôi muốn hai model dùng cùng split, để so sánh công bằng.
11. Là người đánh giá, tôi muốn xem MAE/RMSE cùng VND/tháng và số mẫu, để hiểu sai số.
12. Là người đánh giá, tôi muốn nhóm rỗng/ít mẫu được ghi rõ, để không đọc điểm số nhỏ như chứng nhận chất lượng.
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
- Quyết định kiểm duyệt ngày 29/10: thu nhập tháng chào tuyển được chấp nhận thành phạm vi riêng, không gộp với lương cơ bản hoặc khoản chưa rõ cấu phần. Không cộng thưởng năm/phụ cấp vào trung điểm tháng; ghi đồng thời phạm vi thu nhập và basis.
- Một tin là một quan sát dù có nhiều kỹ năng/địa điểm. Tách row nguồn, thực thể tin và nhóm chống leakage; không bỏ tham số định danh khi chỉ cần bỏ tracking.
- Vòng quyết định 29/10: chia theo công ty, mọi bản trùng/đăng lại cùng tập; mục tiêu đánh giá là công ty chưa có trong train. MAE là metric chính. Tư vấn ưu tiên chênh lệch dự đoán của model, không ưu tiên nhu cầu trước delta. Các chi tiết chưa chốt vẫn giữ trong phần đề xuất.
- Vòng tiếp theo: Ridge + Linear Regression; MAE chính, RMSE phụ; tỷ lệ mục tiêu 70/15/15, seed 42, chọn bằng validation MAE và test riêng. Không trả số lương/tư vấn khi thiếu hỗ trợ. Chỉ gợi ý candidate đủ hỗ trợ, delta > 0, tối đa ba; tie-break theo n train rồi tên chuẩn.
- Vòng cuối: validation MAE bằng nhau thì chọn Linear Regression, dùng giá trị chưa làm tròn. Model được chọn chỉ dùng demo/tư vấn khi MAE nhỏ hơn baseline trung vị train trên cả validation và test, cùng cohort/basis/phạm vi. Test không đạt thì lưu báo cáo/run nhưng không promote, không đổi model hoặc chỉnh tham số bằng test.
- Trước khi khóa snapshot ML phải sửa/kiểm tra các lỗi audit có thể làm sai nhãn, nghề, Remote, bằng chứng và nhóm tin. Không dùng trạng thái parser “valid” làm chứng cứ duy nhất cho một target.
- Feature theo allowlist: vai trò, kinh nghiệm có biểu diễn khoảng/cận, kỹ năng chuẩn, địa điểm chuẩn và hình thức làm việc. Tiêu đề/JD nguyên văn, số tiền, cận lương, target, lý do suy từ target, ID/URL/công ty và trường nguồn chỉ phục vụ kiểm toán/nhóm/báo cáo; không tự đưa vào model.
- Alias/quy tắc được đóng phiên bản; vocabulary encoder, imputer và scaler chỉ fit train. Kỹ năng/nhóm chưa gặp không âm thầm biến thành hồ sơ được hỗ trợ.
- Snapshot, split, cấu hình, seed, feature schema, target policy, phiên bản thư viện và artifact có hash/ID. Run lỗi hoặc bị ngắt không thay model đang dùng.
- Dashboard chỉ dùng artifact nội bộ đã được kiểm tra. Không nhận model từ upload. Suy luận không ghi đè training snapshot hoặc tự fit lại.

### Tham số còn chờ dữ liệu trước fit

- #4: temporal holdout chỉ xem xét khi ngày và sampling frame đủ phù hợp; không thay chia theo công ty đã chốt hoặc lấy hai snapshot khác nền tảng làm bằng chứng xu hướng thời gian.
- #4: basis và tiêu chí chấp nhận đã chốt; biểu diễn kinh nghiệm thiếu/khoảng/cận, số nhóm tối thiểu, outlier và ngưỡng hỗ trợ còn phải khóa theo dữ liệu trước fit. Readiness tiếp tục bị chặn khi thiếu các điều kiện này; không dùng ngưỡng mặc định tùy tiện để mở train.
- #5: ngưỡng hỗ trợ bằng số cho hồ sơ nền và hồ sơ thêm kỹ năng còn cần dữ liệu mở rộng để chốt trước fit; nhu cầu từ train giữ riêng như bằng chứng hỗ trợ. Không dùng test để chọn danh sách hay tham số xếp hạng.

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

Tám spec M01–M08 trong danh mục ML làm rõ các F04–F08 và ticket hiện có. Ngày 30/10, người dùng duyệt và đã đăng 23 issue ML chi tiết với dependency trong ticket-graph.json/TICKET_PLAN.md. Graph 27 ticket cũ giữ vai trò lịch sử/đầu mục tổng hợp, không tạo hai bản triển khai trùng nhau. F03/T14–T16 tiếp tục mô tả thống kê lương quan sát trong ML16–ML18, tách khỏi feature importance hoặc chênh lệch dự đoán. Publication này không mở gate hoặc tự huấn luyện.

# Spec tổng thể: Phân tích tuyển dụng CNTT Việt Nam và dự đoán lương

Trạng thái: đã được người dùng duyệt và đăng [spec trên GitHub](https://github.com/theihoz/ML/issues/6) ngày 28/10/2026. Branch: `dev/job-market-ml-from-scratch`. Các quyết định phụ thuộc dataset vẫn theo bản đồ wayfinder.

## Problem Statement

Người học cần một ứng dụng hoàn chỉnh để phân tích tuyển dụng CNTT và ước tính lương theo vai trò, kinh nghiệm, kỹ năng và địa điểm. Bài phải dùng Python, Matplotlib/Seaborn và ít nhất hai mô hình tự huấn luyện, có ít nhất hai metric, có dữ liệu bàn giao và demo trực tiếp trên máy.

Người dùng yêu cầu xây lại từ đầu bằng Python/Streamlit, tìm dataset mới và không dùng lại dữ liệu, model hay mã triển khai của ứng dụng cũ. Tên gọi tương đương trong dữ liệu mới cần được gom về nhãn thống nhất để thống kê và dự đoán nhất quán.

## Solution

Một ứng dụng Streamlit tiếng Việt có dữ liệu tuyển dụng đã kiểm tra, màn hình chất lượng dữ liệu, phân tích thị trường, so sánh mô hình, dự đoán và tư vấn nghề nghiệp. Người dùng có thể tải CSV/XLSX để chuẩn hóa, xem lỗi từng dòng và dự đoán hàng loạt.

Huấn luyện chạy bằng lệnh riêng. Dashboard đọc dataset và model đã lưu để demo trực tiếp trên máy. Nguồn chính phục vụ Việt Nam với VND/tháng; dữ liệu quốc tế nếu có được hiển thị và đánh giá độc lập. Xu hướng nhiều năm chỉ xuất hiện khi thời gian và phạm vi nguồn đủ so sánh.

## User Stories

1. Là người báo cáo, tôi muốn mở ứng dụng bằng lệnh rõ ràng để demo trên máy.
2. Là người phân tích, tôi muốn biết nguồn, revision, thời gian và đơn vị của mỗi dataset để giải thích xuất xứ.
3. Là người phân tích, tôi muốn chỉ dùng nguồn dữ liệu mới đã kiểm tra để thực hiện đúng phạm vi làm lại.
4. Là người phân tích, tôi muốn phân biệt số dòng thô, tin duy nhất và mẫu có nhãn lương để hiểu quy mô thực tế.
5. Là người phân tích, tôi muốn xem các dòng bị cách ly và lý do để rà soát chất lượng.
6. Là người phân tích, tôi muốn giữ giá trị gốc cạnh giá trị chuẩn để đối chiếu.
7. Là người phân tích, tôi muốn các tên HCM, Hồ Chí Minh và ho chi minh cùng thuộc HCM để thống kê thống nhất.
8. Là người phân tích, tôi muốn một tin có thể giữ cả HCM và HN để không mất địa điểm.
9. Là người phân tích, tôi muốn Remote được tách khỏi tỉnh/thành để phân tích hình thức làm việc.
10. Là người phân tích, tôi muốn tổng số tin đếm theo tin duy nhất để tránh tăng tổng do nhiều địa điểm.
11. Là người phân tích, tôi muốn phân biệt Backend, Frontend, Fullstack, Mobile, Data/ML, DevOps và QA Automation để so sánh đúng nghề.
12. Là người phân tích, tôi muốn gom các tên tương đương của một kỹ năng để không chia nhỏ kết quả.
13. Là người phân tích, tôi muốn phân biệt Java với JavaScript và C với C++ để kết quả bóc tách đúng nghĩa.
14. Là người phân tích, tôi muốn chuẩn hóa số năm kinh nghiệm và giữ dạng khoảng để hiểu yêu cầu tuyển dụng.
15. Là người phân tích, tôi muốn giữ hai đầu khoảng lương và dùng trung điểm hợp lệ để huấn luyện có căn cứ.
16. Là người phân tích, tôi muốn tin thiếu lương vẫn tham gia thống kê tuyển dụng để không làm lệch số lượng tin.
17. Là người phân tích, tôi muốn chỉ so sánh lương cùng thị trường, loại nhãn và đơn vị để kết quả có ý nghĩa.
18. Là người phân tích, tôi muốn xem top kỹ năng xuất hiện trong tin để nhận diện nhu cầu quan sát được.
19. Là người phân tích, tôi muốn xem lương theo kỹ năng kèm số mẫu để hiểu độ hỗ trợ.
20. Là người phân tích, tôi muốn xem quan hệ giữa kinh nghiệm và lương để phát hiện khác biệt giữa nhóm nghề.
21. Là người phân tích, tôi muốn so sánh lương theo vai trò và khu vực để hiểu mặt bằng trong dữ liệu.
22. Là người phân tích, tôi muốn xem biến động theo thời gian khi nguồn cho phép để phân tích xu hướng.
23. Là người phân tích, tôi muốn xem dữ liệu thiếu và ngoại lệ để giải thích các giới hạn.
24. Là người báo cáo, tôi muốn xuất biểu đồ và bảng đã lọc để trình bày kết quả.
25. Là người huấn luyện, tôi muốn tái lập bước làm sạch và chia tập để so sánh công bằng các mô hình.
26. Là người huấn luyện, tôi muốn dùng ít nhất hai mô hình tự học từ dữ liệu của dự án để đáp ứng đề bài.
27. Là người huấn luyện, tôi muốn xem ít nhất hai metric trên cùng tập đánh giá để hiểu sai số.
28. Là người huấn luyện, tôi muốn chọn mô hình bằng validation và báo cáo test riêng để đánh giá có căn cứ.
29. Là người demo, tôi muốn model được nạp từ artifact và cho kết quả nhất quán sau khi khởi động lại.
30. Là lập trình viên, tôi muốn nhập vai trò, kinh nghiệm, kỹ năng và địa điểm để nhận mức lương dự đoán.
31. Là lập trình viên, tôi muốn biết hồ sơ có đủ dữ liệu hỗ trợ không để hiểu giới hạn của dự đoán.
32. Là lập trình viên, tôi muốn nhận kỹ năng chưa có cùng bằng chứng để cân nhắc học tiếp.
33. Là người dùng, tôi muốn tải CSV/XLSX, ghép cột và xem lỗi theo dòng để dự đoán nhiều hồ sơ.
34. Là người dùng, tôi muốn tải kết quả có đơn vị và trạng thái từng dòng để sử dụng lại.
35. Là người báo cáo, tôi muốn gói bàn giao chứa mã nguồn mới, dataset được phép phân phối và hướng dẫn tái lập để nộp bài.
36. Là người báo cáo, tôi muốn chạy quy trình demo từ gói bàn giao để kiểm tra việc nộp bài hoàn chỉnh.

## Implementation Decisions

### Đã được người dùng xác nhận

- Xây mã nguồn mới, dataset mới; Việt Nam là thị trường chính.
- Python cho toàn bộ ứng dụng; Streamlit cho dashboard và demo trên máy.
- Các nhóm nghề gồm Backend, Frontend, Fullstack, Mobile, Data/ML, DevOps và QA Automation.
- Chuẩn hóa tên tương đương theo dữ liệu mới; HCM/Hồ Chí Minh/ho chi minh → HCM. Giá trị gốc được giữ để đối chiếu.
- Một tin có nhiều địa điểm; Remote độc lập; tổng số tin đếm theo tin duy nhất.
- Giữ hai đầu khoảng lương, dùng trung điểm cho khoảng đủ thông tin. Tin thỏa thuận, chỉ có một cận hoặc thiếu đơn vị không được coi là nhãn lương chính xác.
- Huấn luyện bằng lệnh riêng; dashboard dùng model đã lưu.
- Dashboard có dữ liệu chuẩn bị sẵn và nhận CSV/XLSX để chuẩn hóa, xem lỗi, dự đoán hàng loạt.
- Phân tích nhiều năm khi có nguồn phù hợp; dữ liệu khảo sát không được dùng thay số đo nhu cầu tuyển dụng.
- Ít nhất hai mô hình tự huấn luyện và hai metric; biểu đồ bằng Matplotlib/Seaborn; không dùng pretrained/fine-tune.

### Thiết kế đề xuất, chờ chốt qua bản đồ quyết định

- Một giao diện nghiệp vụ chung nhận yêu cầu chuẩn bị dữ liệu, báo cáo, huấn luyện, dự đoán và tư vấn. CLI và Streamlit cùng dùng giao diện này; tránh nhân đôi quy tắc.
- Các khối trách nhiệm: hồ sơ nguồn, chuẩn hóa dữ liệu, phân tích/biểu đồ, huấn luyện/đánh giá, suy luận/tư vấn và giao diện.
- Khởi đầu bằng Ridge và Random Forest; MAE, RMSE, R²; chọn model bằng validation MAE. Cấu hình chính xác và cách chia tập phụ thuộc kiểm toán dataset mới.
- Mỗi bản ghi lưu nguồn/ID/URL, thời gian và loại thời gian, chuỗi gốc, địa điểm chuẩn dạng tập, hình thức làm việc, vai trò, kỹ năng, kinh nghiệm, khoảng lương, tiền tệ/kỳ, trạng thái chất lượng và lý do.
- Tách tập tin đủ điều kiện EDA khỏi tập có nhãn lương đủ điều kiện huấn luyện. Mỗi nhãn phải truy ngược được chứng cứ nguồn.
- Tin đăng lại và bản sao được nhóm trước chia tập. Imputation, từ vựng mã hóa và biến đổi học từ dữ liệu chỉ fit trên train.
- Nội dung chứa lương, hai đầu lương và các trường suy trực tiếp từ nhãn không làm feature dự đoán.
- Giữ thông tin gross/net khi nguồn có; nếu chưa rõ thì hiển thị chưa rõ. Ngoại tệ không được tự quy thành VND.
- Ngày đăng, hạn nộp, ngày cập nhật và ngày tải có kiểu ngữ nghĩa riêng. So sánh năm dùng thời gian nguồn đã xác minh và mẫu nguồn có thể đối chiếu.
- Tư vấn dự kiến trả tối đa ba kỹ năng chưa có, gắn số mẫu và lý do; xếp hạng từ dữ liệu train. Ngưỡng bằng chứng và việc dùng chênh lệch dự đoán cần được chốt sau kiểm toán nguồn.
- Kết quả suy luận ghi phiên bản model, phiên bản dữ liệu, đơn vị, trạng thái và cảnh báo. Một con số lương là ước tính lương chào tuyển trong phạm vi dữ liệu.
- Bản cài phục vụ demo tải artifact đã lưu, không truy cập nguồn ngoài trong luồng dự đoán.
- Giới hạn dung lượng file, số dòng và thời gian xử lý được cấu hình, thông báo trước khi tải file; không tự cắt bỏ dòng.

## Testing Decisions

- Điểm kiểm thử chính đã được duyệt: hành vi qua giao diện nghiệp vụ chung, dùng dataset kiểm thử nhỏ có nguồn/nhãn đã rà soát; CLI và Streamlit được smoke test từ đầu đến cuối.
- Kiểm tra đầu vào/đầu ra và quy tắc domain; không khẳng định chất lượng qua việc mock model hoặc so sánh hàm với chính nó.
- Bao phủ đổi tên HCM/HN, nhiều địa điểm, Remote, vai trò, từ khóa dễ nhầm, khoảng kinh nghiệm, lương thỏa thuận/một cận/thiếu đơn vị và giữ nguyên raw.
- Kiểm tra một tin nhiều địa điểm không làm tăng tổng, bảng/biểu đồ dùng đúng tập mẫu và nêu đơn vị, thiếu thời gian không tạo xu hướng giả.
- Kiểm tra các nhóm tin không giao nhau giữa các tập; fit preprocessing chỉ trên train; cả hai model dùng cùng tập đánh giá; không dùng test để chọn cấu hình.
- Đo metric lại từ nhãn và prediction đã lưu; số trên dashboard khớp artifact. Metric không được điền sẵn.
- Kiểm tra save/reload ở tiến trình mới và đối chiếu CLI với dashboard trên cùng hồ sơ.
- Kiểm tra upload có cả dòng hợp lệ và lỗi, giữ thứ tự, xuất được kết quả và không làm đổi dataset/model gốc.
- Kiểm tra gói bàn giao bằng cài đặt mới, mở app, nạp model, dự đoán, tư vấn, upload và xuất kết quả khi nguồn mạng bị tắt.
- Hệ thống cũ chỉ cung cấp bối cảnh lịch sử; không tái sử dụng mã, fixture dữ liệu hoặc metric của nó cho bản mới. Fixture tổng hợp nhỏ chỉ kiểm tra logic, phải gắn rõ và không tham gia huấn luyện/đánh giá chất lượng.
- Nhóm kiểm tra bắt buộc của bản mới gồm lint, kiểm tra các hợp đồng dữ liệu/mô hình và smoke giao diện; đưa vào một lệnh kiểm tra và CI khi tạo ứng dụng mới.

## Out of Scope

- Dùng lại dataset/model/code của ứng dụng cũ hoặc tải lại cùng nguồn cũ để coi là nguồn mới.
- Pretrained, fine-tune, dịch vụ LLM, embedding pretrained hoặc dữ liệu giả làm bằng chứng thị trường.
- Cam kết một kỹ năng gây tăng lương, cam kết mức sai số khi chưa đánh giá.
- Mua dataset, deploy cloud, đăng nhập, thanh toán hoặc tự thu thập sau cổng xác thực.
- Huấn luyện khi người dùng upload hoặc khi mở dashboard.
- Báo cáo Word, sơ đồ bắt buộc hoặc bản triển khai quốc tế nếu chưa có yêu cầu riêng.

## Further Notes

Bản đồ wayfinder canonical: [Bản đồ quyết định](https://github.com/theihoz/ML/issues/2). Ba quyết định còn mở: [Nguồn dataset mới](https://github.com/theihoz/ML/issues/3), [Đánh giá và mức hỗ trợ](https://github.com/theihoz/ML/issues/4), [Bằng chứng tư vấn](https://github.com/theihoz/ML/issues/5).

Đợt khảo sát bốn ứng viên mới chưa chọn được nguồn đủ điều kiện; bằng chứng ở [báo cáo nguồn mới](https://github.com/theihoz/ML/blob/411f1dbf43fea51b47677356b10f7cb3f5955190/docs/research/new-vietnam-datasets-20261028.md). Chưa chọn dataset cuối, chưa chốt ngưỡng low-support, chưa có kết quả model và chưa có lịch báo cáo. Các phần phụ thuộc phải giữ trạng thái chờ quyết định; việc duyệt spec không phải bằng chứng ứng dụng đã hoàn thành.


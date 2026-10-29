# Retro phiên lập kế hoạch ngày 28/10/2026

## Cập nhật sau triển khai EDA ngày 29/10/2026

Đã có runtime/Makefile/CI riêng trong job_market; lint bao phủ cả pages. Các ca alias, thiếu đơn vị, nhiều địa điểm và snapshot đã thành kiểm thử cụ thể. Chưa thay AGENTS của người dùng.

Agent phụ hết quota giữa frontier: T03/T07 còn worktree chưa commit, merger/T06 dừng trước khi thay đổi. Main đã kiểm kê và tiếp tục trực tiếp; bằng chứng TDD phân biệt vòng đỏ thực quan sát với phần code tiếp nhận. Lần tiếp theo nên checkpoint code/lát cắt sớm và giữ môi trường trong job_market/.venv thay vì chỉ ở /tmp để giảm phần phải khởi tạo lại.

Review trên dữ liệu thật phát hiện Flutter/Unity bị bỏ sót dù unit test cũ xanh. Nên giữ kiểm tra đối chiếu các tên công nghệ phổ biến thực quan sát, đồng thời tăng rules_version khi đổi danh mục và khởi động lại demo trước nghiệm thu. Không dùng số test làm thay thế cho việc xem bảng/biểu đồ thật.

Gói wheel chỉ đưa raw/provenance được chỉ định vào, tránh gom cả cache/processed. Phần đóng gói bàn giao đầy đủ và kiểm tra offline cả model vẫn thuộc T26/T27, chưa được đánh dấu hoàn tất.

Phần dưới giữ lại đề xuất của phiên lập kế hoạch, không phải trạng thái triển khai hiện tại.

Phạm vi: phiên hiện tại, từ yêu cầu tạo branch và phỏng vấn đến lập spec/bản đồ quyết định. Đây là đề xuất cải thiện môi trường cho lần triển khai; chưa sửa các cấu hình hoặc code cũ.

## 1. Ưu tiên cao: tách điểm vào của dự án mới khỏi môi trường cũ

Bằng chứng: người dùng yêu cầu làm lại hoàn toàn và dùng dataset mới; nhánh mới hiện vẫn kế thừa cây dự án cũ. Makefile hiện dùng môi trường TensorFlow, có lệnh train-llm, web-build gọi npm và web gọi ứng dụng cũ. Quy tắc ignore hiện loại phần lớn dữ liệu ngoài các ngoại lệ cũ.

Ảnh hưởng: agent kế tiếp dễ chạy nhầm lệnh hoặc đóng gói nhầm dữ liệu/artifact; dataset mới có thể không vào gói nộp nếu chỉ nhìn trạng thái Git.

Đề xuất: T01–T02 tạo điểm vào và môi trường riêng của ứng dụng Python mới, một hồ sơ nguồn được cho phép và kiểm tra tự động từ chối nguồn/artifact ngoài hồ sơ. T26–T27 đối chiếu manifest với file thật trong gói bàn giao. Chỉ thêm một navigation pointer ngắn trong tài liệu điều hướng của agent tới spec mới sau khi bộ kế hoạch được duyệt; không viết lại AGENTS hiện có của người dùng.

## 2. Ưu tiên cao: có cấu hình kiểm tra nhưng thiếu nơi bắt buộc chạy

Bằng chứng: pyproject có cấu hình Ruff; Makefile check hiện chỉ chạy pip check và test chạy unittest. Không thấy workflow CI hoặc cấu hình pre-commit được theo dõi; thư mục hooks chỉ có các file mẫu, không có core.hooksPath được cấu hình. Đây là kiểm tra cấu hình, không phải kết quả chạy kiểm thử.

Ảnh hưởng: lỗi cơ học và vi phạm hợp đồng dữ liệu có thể đi vào lần bàn giao nếu không ai gọi đúng lệnh.

Đề xuất: trong T01 của bản mới, gom lint và kiểm thử thiết yếu vào một lệnh, chạy cùng lệnh trong CI. Khi có code chuẩn hóa/huấn luyện, thêm kiểm tra cụ thể cho target thiếu đơn vị, một tin nhiều địa điểm, phân biệt Java/JavaScript và leakage; không thay các lỗi cơ học này bằng một trang quy định prose dài.

## 3. Ưu tiên vừa: ghi ngay quyết định mới vào đúng nơi

Bằng chứng: sau vòng hỏi đầu, người dùng chốt nhóm nghề, trung điểm lương, nhiều địa điểm và upload, rồi chuyển nhanh sang các skill lập kế hoạch. Glossary/ADR ban đầu chưa ghi đủ các câu trả lời đó; phiên này đã bổ sung trước khi viết spec.

Đề xuất: sau mỗi vòng có câu trả lời, cập nhật glossary cho thuật ngữ và ADR cho quyết định khó đảo ngược. Spec đánh dấu riêng phần được người dùng xác nhận và phần đề xuất. Điểm này cần xét ngữ nghĩa khi review; không tạo một quy tắc tự động giả vờ hiểu mọi quyết định.

## 4. Ưu tiên vừa: tìm tool/file đúng phạm vi để giảm lượt đọc vô ích

Bằng chứng: một lần tìm metadata tool bằng từ rộng khớp hàng loạt công cụ Vercel và tạo hơn 23 nghìn token output trước khi bị cắt; tìm exact prefix multi_agent sau đó trả đúng nhóm cần dùng. Một số lệnh rg gọi thư mục optional chưa tồn tại làm trả exit 2 và dừng phần đọc nối bằng &&.

Đề xuất: discovery dùng exact name/prefix, in tên và mô tả rút gọn trước rồi mới đọc schema tool đã chọn; kiểm tra thư mục optional tồn tại trước khi tìm. Với các lượt đọc độc lập, gom song song; với publication, đợi kết quả tạo ID rồi mới nối quan hệ.

## Kết quả của retro

Các thay đổi môi trường đề xuất đã được gắn vào T01–T02/T26–T27 của bản chia việc v2 và phần kiểm thử của spec. Chưa thay hook, CI, Makefile hoặc AGENTS; retro này không chứng nhận ứng dụng mới đã được triển khai hay kiểm thử.


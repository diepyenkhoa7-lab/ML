# Đánh giá cách đặc tả dự án ML

Ngày kiểm tra: 28/10/2026. Đây là ghi chú nghiên cứu và đề xuất cải thiện, không phải spec đã được người dùng phê duyệt.

Cập nhật sau lần kiểm tra này: repo đã có spec và ticket nháp, GitHub đã có bản đồ quyết định cùng ba sub-issue. Xem [review mới nhất](ask-matt-review-2026-10-28.md); các nhận định trạng thái bên dưới giữ nguyên bối cảnh thời điểm kiểm tra cũ.

## Phạm vi và giới hạn

Đề gốc được người dùng cung cấp trực tiếp trong phiên đánh giá: đọc/làm sạch dữ liệu tuyển dụng hoặc khảo sát; bóc kỹ năng từ chuỗi và chuẩn hóa lương/kinh nghiệm; vẽ các nhóm biểu đồ bằng Matplotlib/Seaborn; tự huấn luyện ít nhất hai mô hình, đánh giá bằng ít nhất hai metric; phân tích kỹ năng liên quan giá trị gia tăng; nhập hồ sơ để dự đoán lương và gợi ý kỹ năng; bàn giao source, dataset và demo báo cáo. Python và cấm pretrained/fine-tune là ràng buộc đề. Nội dung chat được dẫn chưa được truy cập bằng `read_thread`, vì công cụ này không có trong phiên; báo cáo không dựa vào suy đoán nội dung chat đó.

Nguồn hiện tại đã đọc trong repo: `AGENTS.md`, các cấu hình trong `docs/agents/`, `GLOSSARY.md`, ADR 0001–0004, `docs/rebuild/wayfinder/` và README. Các tài liệu đang được bổ sung đồng thời; kết luận này là ảnh chụp tại thời điểm nghiên cứu.

Đã kiểm tra tracker bằng `gh issue list --repo theihoz/ML --state all --limit 100 --json number,title,body,labels,state,url,comments`; kết quả là `[]`. Tại thời điểm kiểm tra chưa thấy spec được đăng thành GitHub Issue; map local cũng tự ghi là bản soạn trước khi đăng. Nhánh hiện tại là `dev/job-market-ml-from-scratch`.

## Kết luận

Cách đi hiện tại đúng hướng: đã cấu hình tracker, thống nhất ngôn ngữ, ghi lại lựa chọn lớn và tách các câu hỏi còn mở. Các artifact hiện tại là tài liệu lập kế hoạch; chưa có bản spec cuối trong những tài liệu đã đọc. `grill-me` không tự phát sinh spec: luồng chính thức tách bước phỏng vấn với `to-spec`. Bước cần bổ sung là liên kết từng yêu cầu đề với hành vi nghiệm thu và bằng chứng bàn giao. Có thể soạn spec nháp ngay, đánh dấu rõ phần phụ thuộc nguồn dữ liệu; chưa gắn toàn bộ dự án là sẵn sàng triển khai độc lập khi các blocker chưa giải quyết. [Nguồn: ask-matt](https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md).

## Đối chiếu với phương pháp Matt Pocock

1. **Đang có repo thì dùng luồng có tài liệu.** Nguồn chính thức hướng công việc trong repo qua `grill-with-docs`, rồi `to-spec` và `to-tickets` nếu cần nhiều phiên triển khai. `research` cung cấp bằng chứng cho quá trình này, không thay quyết định của người dùng. Nếu công việc quá mơ hồ cho một phiên, `wayfinder` giúp chốt quyết định trước khi chuyển sang spec. [Nguồn: ask-matt](https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md).

2. **Glossary và ADR đang làm đúng vai trò.** Glossary chỉ chứa thuật ngữ; không biến nó thành danh sách tính năng. ADR chỉ cần đoạn ngắn nêu bối cảnh, quyết định và lý do; các ADR hiện có không cần kéo dài chỉ để giống mẫu kiến trúc nhiều mục. Chỉ thêm ADR cho lựa chọn có chi phí đổi ý, cần bối cảnh và có đánh đổi thật. [Nguồn: domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md), [định dạng ADR](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/ADR-FORMAT.md).

3. **Tách sự thật cần kiểm tra với lựa chọn cần chốt.** Chất lượng nguồn dữ liệu là việc phải kiểm tra, không thể giải quyết bằng câu trả lời “cứ dùng dataset đó”. Phạm vi thị trường, hành vi khi thiếu mẫu và cách ưu tiên gợi ý là quyết định thiết kế. Map hiện tại đã ghi Ridge/Random Forest, các metric và tối đa ba kỹ năng dưới dạng đề xuất, đúng cách tránh biến giả định thành yêu cầu đã duyệt. [Nguồn: grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md).

4. **Spec cần thêm hợp đồng hành vi.** `to-spec` tổng hợp những điều đã bàn, gồm vấn đề, giải pháp, user stories, quyết định triển khai, kiểm thử và ngoài phạm vi. Dùng thuật ngữ glossary và tôn trọng ADR; tránh khóa spec vào đường dẫn file hoặc đoạn code dễ lỗi thời. Không dùng riêng glossary/map làm spec. [Nguồn: to-spec](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md).

5. **Ticket cần lát cắt chạy được.** Mỗi ticket nên tạo một hành vi có thể demo hoặc kiểm chứng và chỉ khai báo những phụ thuộc thật. Khi dùng GitHub, giữ quan hệ parent/blocker; mỗi ticket có acceptance criteria. Tránh chia đơn thuần thành “làm toàn bộ dữ liệu”, “làm toàn bộ model”, “làm toàn bộ UI” mà không có đầu ra dùng thử. [Nguồn: to-tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md).

Tên skill hiện hành là `to-spec` và `to-tickets`; hướng dẫn cũ dùng `write-a-prd`, `to-prd` hoặc `prd-to-issues` có thể chưa phản ánh bản hiện tại. [Nguồn: ghi chú phát hành chính thức](https://github.com/mattpocock/skills/releases).

## Cải thiện để bám đề

Các mục sau là đề xuất đánh giá cho dự án này, không phải yêu cầu mới do Matt Pocock đặt ra.

| Nhóm yêu cầu đề | Điều spec cần ghi rõ | Bằng chứng nghiệm thu đề xuất |
| --- | --- | --- |
| Đọc và làm sạch | Định dạng đầu vào; cột cần có; thiếu dữ liệu; trùng tin; kỹ năng từ chuỗi; kinh nghiệm khoảng; lương cố định/khoảng/thiếu đơn vị | Dữ liệu mẫu đầu vào và kết quả chuẩn hóa, số dòng giữ/loại cùng lý do; giữ trường gốc để đối chiếu |
| Biểu đồ | Xác định cách đếm kỹ năng và đo lương; đủ năm góc nhìn: công nghệ có nhu cầu cao; công nghệ lương cao; kinh nghiệm–thu nhập; lương theo vai trò; lương theo khu vực | Các biểu đồ Matplotlib/Seaborn có nhãn, đơn vị, nguồn và số mẫu; trường hợp ít mẫu có thông báo |
| Ít nhất hai mô hình | Cùng mục tiêu và tập dữ liệu so sánh; tự train; xử lý trùng trước chia tập; fit tiền xử lý trên train; chọn model bằng validation | Hai artifact mô hình, lệnh train, báo cáo ít nhất hai metric và test giữ riêng |
| Kỹ năng và giá trị gia tăng | Phân biệt liên hệ quan sát, ảnh hưởng trên dự đoán và tăng lương nhân quả; chốt cách xếp hạng | Bảng/biểu đồ giải thích phương pháp và giới hạn; không hứa học kỹ năng sẽ tăng lương một mức chắc chắn |
| Nhập hồ sơ | Vai trò, kinh nghiệm, kỹ năng; đơn vị lương; hồ sơ ngoài phạm vi; dữ liệu hỗ trợ ít | Một hồ sơ hợp lệ cho ra lương và gợi ý kỹ năng chưa có; hồ sơ thiếu/sai hoặc ít bằng chứng được xử lý rõ |
| Bàn giao | Source, dataset thuộc định dạng đề chấp nhận, hướng dẫn tái lập và demo | Chạy lại từ môi trường mới, nạp được model đã lưu, mở được dữ liệu và biểu đồ dùng trong báo cáo |

Ví dụ acceptance criteria để đưa vào bản nháp:

- Chuỗi `Node.js; nodejs` quy về một kỹ năng, không đếm hai lần trong một tin; các cách viết HCM quy về nhãn chuẩn, vẫn giữ giá trị gốc.
- Khoảng 20–30 triệu VND/tháng cho nhãn trung điểm 25 triệu VND/tháng; tin “thỏa thuận” vẫn tham gia phân tích tuyển dụng, không được tự điền nhãn để train hồi quy. Đây đã là quyết định ADR 0003.
- Hai model được so sánh trên cùng tập giữ lại; tiền xử lý chỉ fit trên train. Lưu rồi nạp lại pipeline cho ra cùng dự đoán trong sai số số học chấp nhận được. [Cơ sở: scikit-learn về leakage](https://scikit-learn.org/stable/common_pitfalls.html), [tập validation/test](https://scikit-learn.org/stable/modules/cross_validation.html).
- Gợi ý không chứa kỹ năng người dùng đã có; mỗi gợi ý có bằng chứng và số mẫu hỗ trợ, hoặc thông báo thiếu dữ liệu. Không diễn giải chênh lệch quan sát/dự đoán thành cam kết tăng lương nhân quả.
- Dashboard nạp model đã lưu; upload CSV/XLSX không tự train. Đây đã là quyết định ADR 0004.

**Phân biệt ba loại ràng buộc.** Đề bắt buộc Python, tự huấn luyện ít nhất hai mô hình và cấm pretrained/fine-tune. Streamlit, Việt Nam là chính, dataset hoàn toàn mới và không kế thừa code là lựa chọn người dùng ghi trong ADR; giữ chúng nếu vẫn là ý định hiện tại, nhưng không mô tả chúng thành nguyên văn đề. Ridge/Random Forest, MAE/RMSE/R² và tối đa ba kỹ năng trong map vẫn là phương án đề xuất.

**Chọn nguồn theo khả năng chứng minh yêu cầu.** Đề cho phép khảo sát hoặc tin tuyển dụng. Nếu chọn khảo sát, số người dùng công nghệ không tự động chứng minh nhu cầu tuyển dụng; cần cách diễn giải phù hợp hoặc nguồn tuyển dụng bổ sung. Dữ liệu quốc tế phải tách mục tiêu và đơn vị với Việt Nam. Từ “xu hướng” trong tên đề chưa tự đủ để bắt buộc phân tích nhiều năm; chỉ cam kết xu hướng thời gian nếu đề/giảng viên xác nhận và nguồn có mốc thời gian so sánh được.

**Không ấn định ngưỡng chất lượng mô hình khi chưa kiểm tra dữ liệu.** Có thể chốt ngay quy tắc chống leakage và cách chọn model. Ngưỡng mẫu tối thiểu theo vai trò/khu vực và mức sai số chấp nhận nên dựa vào kiểm toán nguồn, sau đó ghi quyết định rõ trong spec. “Model tốt” hoặc “gợi ý hợp lý” chưa phải tiêu chí nghiệm thu kiểm chứng được. [Cơ sở về acceptance criteria: Agent Brief](https://github.com/mattpocock/skills/blob/main/skills/engineering/triage/AGENT-BRIEF.md).

**Xử lý xung đột tài liệu cũ.** README vẫn mô tả Vue/FastAPI/Qwen trong khi ADR đã chốt Python/Streamlit và cấm pretrained. Khi chốt spec mới cần cập nhật điểm vào tài liệu, đánh dấu tài liệu legacy và chỉ dẫn đâu là nguồn thẩm quyền; nếu để nguyên, agent triển khai sau có thể theo nhầm hợp đồng cũ. Đây là phát hiện tài liệu, chưa phải kết luận bản mới đã được triển khai.

## Đường đi đề xuất

1. Soạn spec nháp ngay với ma trận trên, tách yêu cầu đề/lựa chọn đã chốt/điểm còn mở.
2. Giải quyết bằng chứng nguồn mới trong map; kiểm tra đủ trường cho các đầu ra đề.
3. Chốt đánh giá, phạm vi hỗ trợ và cách gợi ý theo nguồn thực sự chọn được, rồi cập nhật spec.
4. Chia ticket: nguồn mới → dữ liệu chuẩn dùng được; hồ sơ → dự đoán từ model tự train; hai model → so sánh có biểu đồ; hồ sơ → gợi ý có bằng chứng; gói bàn giao → demo tái lập. Đây chỉ là cách chia sơ bộ, cần kiểm tra lại phụ thuộc sau khi có spec.

Theo cấu hình repo, spec và ticket chính thức nằm trong GitHub Issues của `theihoz/ML`, không phải trong ghi chú nghiên cứu này. Chỉ dùng `ready-for-agent` khi hợp đồng đã đầy đủ để agent làm việc độc lập; các điểm còn cần thông tin phải được ghi cụ thể. Không tạo issue hoặc thay nhãn trong đợt nghiên cứu này. [Cơ sở về trạng thái: triage](https://github.com/mattpocock/skills/blob/main/skills/engineering/triage/SKILL.md).

Chỉ dẫn có thể gửi sang chat đang lập kế hoạch:

> Tổng hợp đề và ADR thành spec nháp ngay theo cấu trúc `to-spec`; đánh dấu dataset, split và ngưỡng hỗ trợ chưa chốt. Thêm bảng III.1–III.4/IV/V → user story → acceptance criteria → bằng chứng bàn giao. Không hỏi lại các quyết định đã ghi trong ADR; không coi blocker là đã giải quyết hoặc đánh dấu toàn bộ dự án `ready-for-agent`. Ghi rõ đây là draft, chưa phải spec canonical đã đăng tracker.

Chỉ dẫn trên đề xuất cách soạn **bản nháp có điều chỉnh**. Nó không đồng nghĩa đã chạy trọn skill `to-spec`, vốn bao gồm đăng spec lên tracker. Trong phiên nghiên cứu này không gọi `to-spec` hoặc `to-tickets` để xuất bản.

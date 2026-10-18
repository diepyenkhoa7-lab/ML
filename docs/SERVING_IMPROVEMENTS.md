# Cải tiến luồng nhập file và phục vụ Gemma

Lượt fine-tune corrected đã hoàn tất nhưng không vượt điều kiện nghiệm thu. Web giữ adapter `20261017T105728Z` và Ridge v2. Những thay đổi dưới đây cải thiện pipeline ứng dụng, không được tính là tăng F1 raw của adapter hoặc giảm MAE thu nhập.

Worker đọc nguyên đầu vào trong context 2.048 token gồm phần dành cho output; không cắt ngầm. Cấu hình model local cho phép context lớn hơn, nhưng không suy rằng đã kiểm chứng toàn bộ giới hạn đó. Nếu JSON/schema sai, worker được sinh lại tối đa một lần khi còn đủ context, giữ cả raw attempts và kết quả cuối; vẫn lỗi thì báo theo dòng. Mô tả trùng hoàn toàn chỉ suy luận một lần trong cùng request, không cache dữ liệu giữa các lần nhập.

JSON đúng schema vẫn có thể chứa kỹ năng suy đoán hoặc tên tính năng chung. Khi thiếu cột kỹ năng riêng, ứng dụng dùng danh mục tên công nghệ/alias có bằng chứng trực tiếp trong mô tả làm feature dự đoán; giữ raw Gemma extraction và `skill_evidence` riêng để kiểm tra. Không suy SQL từ MySQL hoặc Java từ JavaScript. Từ điển vẫn có thể thiếu công nghệ mới; người dùng có thể cung cấp cột kỹ năng riêng, được ưu tiên và không bị lọc bởi danh mục mô tả.

Web kiểm tra lại metadata trước khi gửi job Gemma. Trạng thái bận dựa vào lock thật nên nhận diện cả train, đánh giá và suy luận; có nút kiểm tra lại GPU sau khi tác vụ kết thúc. Bảng đã có cột chuẩn vẫn dự đoán bằng Ridge/RF khi không bật Gemma. Nhãn nguồn của bảng demo 48 dòng lấy theo model train thực tế, không đóng cứng v1.

Đã kiểm chứng bằng trình duyệt thật: nhập `application_gemma_long_demo.json`, ghép cột mô tả, bật Gemma, chạy GPU rồi Ridge/RF và tải ZIP. Kết quả 3/3 dòng có dự đoán, 1 dòng trùng, 2 tin riêng; không có nhãn lương độc lập nên không tính MAE cho bảng này. ZIP đã tải qua giao diện và xác minh checksum 10 file. Kỹ năng “Express … implied” và SQL suy từ MySQL không đi vào feature; raw model vẫn được giữ nguyên.

Bằng chứng ở `outputs/metrics/gemma_corrected_v22/serving_qa/browser_upload_export.json`, `grounded_overview.png`, `grounded_rows.png`, `demo_analysis.zip`. Benchmark context trước/sau retry chỉ có một tin dài từ train; không chứng minh chất lượng trên mọi file. Các metric holdout lương và raw extraction vẫn được báo cáo riêng theo đúng model/corpus đã khóa.

97 tests, Ruff check/format 70 file và source copy tách biệt đều đạt; cài frontend offline, Prettier và production build đạt. Bằng chứng ở `outputs/metrics/gemma_corrected_v22/source_export_final.json`. Các bổ sung báo cáo sau kiểm thử không thay code/model/nhãn. Báo cáo cá nhân vẫn cần mẫu giảng viên và STT/họ tên/MSSV; nội dung kỹ thuật có trong `reports/BAO_CAO_NOI_DUNG.md`.

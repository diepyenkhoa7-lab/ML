# Nhật ký làm lại dự án TensorFlow

## 2026-10-23 — Đã thực hiện

Người dùng tự dọn source cũ và yêu cầu tiếp tục triển khai kiến trúc đã chốt. Giữ thư mục dữ liệu gốc và môi trường; không phục hồi giao diện hoặc Gemma. Bản thay đổi trước khi dọn đã lưu ở `/private/tmp/ml-before-tf-20261023/`; lịch sử Git cũ vẫn tồn tại.

Đã viết pipeline Python `career_ai`: chuẩn hóa, chia nhóm, đầu hồi quy trong Qwen3, baseline tuyến tính TensorFlow, loss có trọng số thị trường, trích xuất JSON, thống kê tư vấn và xuất biểu đồ. Một backbone Qwen dùng chung cho hai loại target; trường thị trường xác định đơn vị và thang log. Baseline là mô hình đối chứng, không thay thế LLM trong kiến trúc.

Rà soát nhãn từ raw thay vì kế thừa nhãn kỳ tháng suy đoán. Gom cùng công ty và nội dung tin đăng trùng thành nhóm trước khi tạo biến thể JSONL. Đóng băng bảng và nhãn bằng checksum. Tập chốt: train10.417 (155 VN), validation2.405 (37 VN), test3.206 (49 VN). Nhãn Việt Nam ít; nhãn trích xuất vẫn là silver. Chưa có cơ sở nói sai số được cải thiện.

Đã có 7 kiểm thử hợp đồng dữ liệu đạt: không trùng nhóm, không rò salary vào prompt, đúng đơn vị, JSONL theo split và metric hỗ trợ nhóm nhỏ. Kiểm tra tĩnh source đạt. Bằng chứng: `tests/test_contracts.py`, `data/tensorflow_v1/manifest.json`, `outputs/prepare.log`. Năm notebook được chuẩn bị; trạng thái thực thi từng notebook thể hiện ngay trong file.

## Đang thực hiện

Cài TensorFlow2.20/TensorFlow Text2.20.1/KerasHub0.32 trong `.venv-tf`; tải preset Qwen phiên bản cố định. Trọng số chính thức nặng6.883.417.048 byte. Mạng chậm là trở ngại thực tế; có công cụ tải chia phần và kiểm SHA256, không coi metadata đã tải là đủ trọng số.

Chưa xác nhận nạp pretrained, cập nhật LoRA trên pretrained hoặc độ chính xác mới. Công cụ kiểm tra Qwen nhỏ khởi tạo ngẫu nhiên chỉ xác minh API, không là kết quả đề tài. Metric phải lấy từ experiment thật; không dùng thành công của sửa kiến trúc làm bằng chứng tăng độ chính xác.

## Các bước sẽ chạy sau khi đủ điều kiện

Kiểm tra import/thiết bị và LoRA nhỏ → train/evaluate baseline → kiểm tra pretrained Qwen, smoke LoRA trên cả hai thị trường, save/reload → train đầy đủ tối đa2epoch → đánh giá test riêng đơn vị và phần trích xuất → demo tệp và biểu đồ. Mỗi bước có log riêng và dừng khi thất bại; không bỏ qua lỗi để công bố hoàn tất.

## 2026-10-23 — Mốc lưu source và khởi chạy điều phối

Đã push source gọn lên `origin/dev/tensorflow-rebuild`, commit triển khai `d5db9e9`. Lịch sử local trước rebuild giữ ở `dev/tensorflow-rebuild-history-20261023`; bản khôi phục thay đổi chưa commit cũng được chép sang `data/archive/pre_tensorflow_20261023/` để không phụ thuộc riêng thư mục tạm.

Đã khởi chạy bộ cài môi trường, tải trọng số theo phiên bản và bộ điều phối training thật. Trạng thái tại thời điểm ghi là **waiting_for_environment**, chưa bắt đầu cập nhật trọng số. `outputs/latest_pipeline.json` là bằng chứng hiện hành, `.cache/tf_environment_status.json` là trạng thái bộ cài. Không coi khởi chạy bộ điều phối là đã train thành công. Output notebook cũ từ lần chuẩn bị dữ liệu trước được xóa để tránh nhầm với kết quả snapshot chốt; sẽ chạy lại bằng kernel TensorFlow sạch.

## 2026-10-23 — Kiểm thử thực tế và bắt đầu fine-tune đầy đủ

Phát hiện tiến trình trước không còn sống dù status còn ghi running. Không xác định được nguyên nhân kết thúc từ log, vì vậy đánh dấu interrupted; không tiếp tục gọi đó là đang training. Thử launchd bị kẹt khi mở môi trường Python, đã dỡ tác vụ này. Sau đó chuyển sang worker tách phiên, kiểm tra PID/tiến trình thực tế và lưu trạng thái worker riêng. Không tạo tác vụ tự khởi động khi đăng nhập.

Tái sử dụng14 wheel đã tải hoàn chỉnh sau kiểm CRC, tải tiếp các phần trọng số. Đã tải đủ6.883.417.048 byte, SHA256 khớp manifest. TensorFlow2.20/Keras3.15.1/KerasHub0.32 đã import và cập nhật LoRA trên Qwen nhỏ thành công. Metal1.2.0 lỗi nạp thư viện `_pywrap_tensorflow_internal.so`; đã gỡ plugin, kiểm tra lại CPU và khóa môi trường. Không gọi CPU là GPU/Metal.

Baseline đầu train được nhưng dự đoán ngoài miền số cho phép. Chẩn đoán trên validation cho thấy chuẩn hóa one-hot hiếm khuếch đại các đặc trưng phân loại. Sửa chỉ chuẩn hóa kinh nghiệm, giữ one-hot0/1; thêm kiểm thử hồi quy lỗi và train experiment mới. Test evaluation trước đã được gọi nhưng dừng do miền dự đoán, chưa sinh metric; không chọn hyperparameter theo test.

Baseline mới `outputs/baseline_20261023T082631`: quốc tế MAE30.577,77USD/năm, RMSE58.495,02USD/năm, R²0,4219 (3.157 mẫu); Việt Nam MAE5.497.220,55VND/tháng, RMSE7.287.465,53VND/tháng, R²0,4258 (49 mẫu). Đây là mức đối chứng thực tế, chưa phải kết quả LLM. Lưu/nạp ở tiến trình mới cho hai thị trường khớp. CLI thực tế đọc CSV/XLSX/JSON:4 dòng hợp lệ,1 dòng lỗi riêng; xuất dự đoán và biểu đồ thành công.

Phát hiện lỗi hậu xử lý sinh văn bản: cắt số ký tự của prompt làm mất phần đầu JSON do cách tokenizer xử lý token đặc biệt. Đổi sang `strip_prompt=True` của Keras và thêm test. Kiểm tra lại pretrained bằng câu tiếng Việt trả đúng JSON với Backend Developer,3 năm,Python/SQL. Một mẫu này chỉ là kiểm tương thích, không là điểm chất lượng chung.

Smoke Qwen LoRA20 mẫu hoàn tất, có2 language update và32 mẫu validation language; lưu adapter/head và so sánh dự đoán trong tiến trình mới đạt. Không dùng smoke để chấm test full. Vòng đầy đủ trên10.417 dòng train, tối đa2epoch đã bắt đầu trên CPU lúc15:31. Các log loss hiện hữu; chưa có metric LLM full, chưa thể kết luận vượt baseline.

Đã chạy5 notebook bằng kernel TensorFlow sạch; cờ train trong notebook giữ tường minh. Có12 kiểm thử hợp đồng đạt trong môi trường mới. Bằng chứng tổng hợp có thể commit: `docs/RUNTIME_EVIDENCE.json`; trạng thái sống hiện hành: `outputs/background_status.json`, `outputs/latest_pipeline.json`, `scripts/status.py`.

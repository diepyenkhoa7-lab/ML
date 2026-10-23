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

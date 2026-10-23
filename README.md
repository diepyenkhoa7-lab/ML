# Career AI — TensorFlow / Keras

Bản làm lại trên nhánh `dev/tensorflow-rebuild`: một Qwen3-1.7B có đầu hồi quy chung cho Việt Nam và quốc tế; hồi quy tuyến tính TensorFlow làm đối chứng. Không có frontend/FastAPI/Gemma trong source hoạt động.

## Môi trường và chạy

Python 3.11. Cài `requirements.txt` vào `.venv-tf`. Cần tải trọng số Keras chính thức bằng `scripts/download_qwen.py`; base weights không nằm trong Git.

```
.venv-tf/bin/python -m pip install -r requirements.txt
.venv-tf/bin/python scripts/download_qwen.py
.venv-tf/bin/python -m career_ai prepare
.venv-tf/bin/python -m career_ai train-baseline --run outputs/baseline
.venv-tf/bin/python -m career_ai train-llm --run outputs/qwen --epochs 2
.venv-tf/bin/python -m career_ai evaluate --run outputs/baseline --model baseline
.venv-tf/bin/python -m career_ai evaluate --run outputs/qwen --model llm
.venv-tf/bin/python -m career_ai analyze --run outputs/qwen --input data/profiles_demo.json
.venv-tf/bin/python -m career_ai advise --run outputs/qwen --input data/profiles_demo.json
```

`prepare` từ chối ghi đè snapshot. Training tạo thư mục run mới; `--limit` chỉ dành cho smoke trial, không dùng claim kết quả full. Năm notebook trong `notebooks/`; training trong notebook được bật tường minh bằng `RUN_TRAINING=True`. Dữ liệu demo từ train, không dùng chấm generalization.

## Hợp đồng dữ liệu

Hồ sơ cần `market` (`international` hoặc `vietnam`), `role`, `location` (quốc gia cho khảo sát), `experience_years`, `skills` (chuỗi phân cách `;`). Nhãn là `salary` và luôn gắn thị trường: tổng thu nhập khảo sát USD/năm, hoặc trung điểm khoảng lương chào tuyển VND/tháng. Không chuyển ngoại tệ tự động. Lương nguồn không vào prompt hồi quy.

Nguồn quốc tế Stack Overflow 2024 (ODbL/DbCL; ghi nguồn Stack Overflow). Việt Nam TiniX, snapshot đã có trong `data/raw/tinixai_2026/data.parquet`, giấy phép nguồn CC-BY-NC-4.0. Bộ parser quy tắc được di chuyển từ lịch sử Git để kiểm tra lại kỳ lương bằng số tiền khớp trong mô tả, không nâng nhãn thiếu kỳ lên strict. Dữ liệu gốc và manifest cũ giữ trong `data/`; các file này không đồng nghĩa tất cả được train bản mới.

Tập mới là nguồn đã từng được nghiên cứu, chia lại không tạo một benchmark mới thu thập độc lập. Nhãn trích từ nguồn/rà soát quy tắc là silver, chưa phải human gold. Nhãn Việt Nam ít hơn đáng kể. Không hứa LLM tốt hơn hồi quy hoặc cam kết sai số thấp.

## Huấn luyện và đánh giá

Qwen backbone LoRA rank8 + LayerNorm/Dense64/Dense1-softplus; loss Huber trên log-lương chuẩn hóa theo thị trường. Batch1, gradient accumulation8, AdamW5e-5, tối đa2epoch. Language replay dùng đáp án trích xuất JSON và mask prompt. Chọn checkpoint trên validation. MAE/RMSE/R² báo cáo riêng từng thị trường. Thống kê kỹ năng từ train cần10 mẫu hỗ trợ; liên hệ quan sát không chứng minh tăng lương do học kỹ năng.

Tài liệu trạng thái thực thi trong `outputs/`; chưa có checkpoint/metric thì không được xem training đã hoàn thành. `predict`, `analyze`, `advise` không cập nhật trọng số. `make test` kiểm tra nhóm, leakage và đơn vị.

## Tái lập và theo dõi

Tải raw đúng phiên bản: `.venv-tf/bin/python scripts/download_data.py`. Kiểm checksum trước khi dùng; lệnh này không ghi đè raw khác checksum. `data/tensorflow_v1/README.md` mô tả bộ lọc và loại nhãn. Dữ liệu đã chia có trong source gọn; raw/trọng số lớn tải riêng.

Trên máy này, bộ điều phối đang được dùng là `scripts/run_training_pipeline.py`: chờ môi trường sẵn sàng, kiểm tra API, train baseline thật, chờ đủ Qwen, smoke LoRA20 mẫu, rồi train đầy đủ2epoch và đánh giá. Trạng thái mới nhất ở `outputs/latest_pipeline.json`; log từng bước trong thư mục pipeline ghi trong đó. Một lỗi sẽ dừng chuỗi, không chuyển trạng thái sang hoàn tất. Không khởi chạy thêm một bộ điều phối khi bộ hiện tại còn chạy.

`python scripts/check_tensorflow.py --device cpu` kiểm tra Qwen kích thước nhỏ khởi tạo ngẫu nhiên: có cập nhật LoRA và save/reload, chỉ là kiểm tương thích. `--device gpu` yêu cầu GPU thực sự trả tensor đầu ra; không suy ra pretrained đã chạy chỉ từ kiểm tra nhỏ. Chỉ khóa môi trường vào `requirements-lock-tf-macos-arm64.txt` sau khi bộ cài và kiểm tra thành công. Dùng lock này trên cùng nền tảng, không coi là lock cho CUDA/Linux.

Đọc CSV/XLSX/JSON theo các cột hồ sơ đã nêu; JSON là mảng các object. Có thể đưa thêm `description` để LLM trích phần thiếu; `market` và `location` phải được cung cấp. Lỗi được ghi theo dòng, không tự đoán đơn vị. `analyze` xuất `predictions.csv/json`, `figures/*.png`, bảng thống kê kỹ năng; biểu đồ từ prediction được hiểu là dự đoán. Không vẽ xu hướng thời gian khi không có cột thời gian phù hợp.

Chọn checkpoint LLM bằng trung bình MAE log theo thị trường +0,1×answer-only cross-entropy trên tối đa32 mẫu validation trích xuất. Tỷ trọng này cố định trước khi đánh giá test. Báo cáo test có MAE/RMSE/R² theo thị trường, vai trò, nhóm kinh nghiệm; dưới10 mẫu gắn `low_support`. Baseline chặn log dự đoán dưới0 để đảm bảo mức lương không âm. Tư vấn kỹ năng dựa vào chênh lệch trung vị quan sát, chịu ảnh hưởng các yếu tố gây nhiễu.

Bản khôi phục source trước khi dọn ở `data/archive/pre_tensorflow_20261023/` (local, không đẩy lên Git). Notebook dùng kernel `career-ai-tf` được đăng ký trong `.venv-tf`; có thể chọn interpreter này trong VS Code. `scripts/execute_notebooks.py` chạy kernel sạch và lưu output, không bật cờ training trong notebook.

## Kết quả đã kiểm chứng ngày 23/10/2026

Môi trường đã khóa trong `requirements-lock-tf-macos-arm64.txt`; CPU vượt kiểm tra. Metal không nạp được với TensorFlow2.20, nên đã gỡ và chọn CPU. Trọng số Qwen đã tải đủ, SHA256 khớp. Smoke LoRA20 mẫu và kiểm tra save/reload ở tiến trình mới đạt; vòng full2epoch đang chạy, chưa có metric LLM full. Chi tiết và giới hạn: `docs/RUNTIME_EVIDENCE.json`.

Baseline test: MAE30.578USD/năm (quốc tế),5,50triệuVND/tháng (Việt Nam); R² lần lượt0,4219/0,4258. Không xem đây là kết quả Qwen. Mười hai kiểm thử đạt; CLI và model thật đã chạy qua CSV/XLSX/JSON, lỗi từng dòng, xuất bảng/biểu đồ. Năm notebook đã thực thi; cell so sánh chờ metric full của LLM.

Chạy `python scripts/status.py` để đối chiếu PID sống với trạng thái lưu. `make pipeline-background` chỉ khởi chạy một worker tách phiên; từ chối nếu worker trước còn sống. Khi máy ngủ, tiến trình cũng có thể tạm dừng; khi worker chết, không coi file running cũ là bằng chứng tiếp tục train. Checkpoint partial là adapter/head trung gian, không bao gồm đầy đủ optimizer để tự khôi phục chính xác giữa epoch.

`python scripts/compare_runs.py --baseline outputs/BASELINE --llm outputs/QWEN --output outputs/COMPARISON` tạo bảng và biểu đồ đối chiếu, yêu cầu hai run dùng cùng snapshot và LLM đã có test full. Smoke bị từ chối. Notebook đánh giá cũng gọi lệnh này khi đủ metric. Với baseline và mô tả cần trích xuất, thêm `--extractor-run outputs/QWEN` trỏ tới LLM đã train; không dùng thư mục baseline làm extractor.

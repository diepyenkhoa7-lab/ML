# Career AI — TensorFlow / Keras

Bản trên nhánh `dev/tensorflow-rebuild`: Qwen3-1.7B fine-tune với đầu dự đoán lương cho Việt Nam và quốc tế; hồi quy tuyến tính TensorFlow làm đối chứng. Có ứng dụng web **Vue3 + JavaScript / Python + FastAPI**, dùng trọng số đã học, không train qua web.

## Chạy ứng dụng web

```sh
make web
```

Mở **http://127.0.0.1:8000**. Dashboard có dữ liệu sẵn có, tìm/lọc/xuất dữ liệu, upload CSV/JSON/XLSX và ghép cột, dự đoán lương, tư vấn kỹ năng, biểu đồ Matplotlib/Seaborn, so sánh MAE/RMSE/R². Tác vụ có tiến độ, lỗi từng dòng và lịch sử. Dữ liệu upload được lưu riêng; không cập nhật trọng số.

Đã cài môi trường trên máy hiện tại. Máy mới cần Python3.11, Node24, `requirements.txt` + `requirements-web.txt`, `npm --prefix frontend ci` và trọng số đã học. Hướng dẫn đầy đủ trong `docs/WEB_DEMO.md`; kiểm thử trong `docs/WEB_QA.md`. Gói model có thể nạp bằng `scripts/restore_web_models.py`; base pretrained tải riêng theo manifest.

## Model đã chốt ngày 25/10/2026

Dùng `outputs/qwen_20261023T082631`: đã train2epoch, giữ trọng số epoch1 theo validation. Đã nạp lại backbone + LoRA + đầu hồi quy trong tiến trình mới và khớp2 hồ sơ probe. Người dùng đã dừng mọi training bổ sung; không tiếp tục trial `auto_lr_low`. Test cuối, demo thật và5 notebook kernel sạch đã hoàn tất. Kết quả ở `docs/AUTONOMOUS_RESULTS.md`; checklist ở `docs/DELIVERY_CHECKLIST.md`.

Validation quốc tế n=2368: MAE31508,37USD/năm, RMSE64012,33, R²0,36624. Việt Nam n=37: MAE7696924,67VND/tháng, RMSE9080539,59, R²0,13729. Quốc tế gần baseline; Việt Nam kém baseline (MAE6337482,63VND/tháng). Trên32 mẫu silver: JSON schema100%, role accuracy81,25%, experience accuracy100%, Skill F1=0,6466. Đây là kết quả validation, chưa phải kết quả test.

Test cuối: MAE30282,04USD/năm ở quốc tế (baseline30577,77), MAE6019790,60VND/tháng ở Việt Nam (baseline5497220,55). LLM tốt hơn nhẹ ở quốc tế, kém hơn ở Việt Nam. Trên85 mẫu silver, JSON schema100%, Skill F1=0,6599. Không dùng test để điều chỉnh trọng số hoặc chọn lại model.

Suy luận bằng trọng số đã học, không cập nhật model:

```sh
.venv-tf/bin/python -m career_ai analyze --run outputs/qwen_20261023T082631 --input data/profiles_demo.json
.venv-tf/bin/python -m career_ai advise --run outputs/qwen_20261023T082631 --input data/profiles_demo.json
```

## Môi trường và chạy

Python 3.11. Cài `requirements.txt` vào `.venv-tf`. Cần tải trọng số Keras chính thức bằng `scripts/download_qwen.py`; base weights không nằm trong Git.

```
.venv-tf/bin/python -m pip install -r requirements.txt
.venv-tf/bin/python scripts/download_qwen.py
.venv-tf/bin/python -m career_ai prepare
.venv-tf/bin/python -m career_ai train-baseline --run outputs/baseline
.venv-tf/bin/python -m career_ai train-llm --run outputs/qwen --epochs 1
.venv-tf/bin/python -m career_auto.evaluation --run outputs/baseline --model baseline
.venv-tf/bin/python -m career_auto.evaluation --run outputs/qwen --model llm
.venv-tf/bin/python -m career_ai analyze --run outputs/qwen --input data/profiles_demo.json
.venv-tf/bin/python -m career_ai advise --run outputs/qwen --input data/profiles_demo.json
```

`prepare` từ chối ghi đè snapshot. Training tạo thư mục run mới; `--limit` chỉ dành cho smoke trial, không dùng claim kết quả full. Năm notebook trong `notebooks/`; training trong notebook được bật tường minh bằng `RUN_TRAINING=True`. Dữ liệu demo từ train, không dùng chấm generalization.

Các lệnh `prepare`/`train-*` ở trên phục vụ tái lập riêng. Goal hiện tại đã chốt model; không chạy chúng trong quá trình bàn giao.

## Hợp đồng dữ liệu

Hồ sơ cần `market` (`international` hoặc `vietnam`), `role`, `location` (quốc gia cho khảo sát), `experience_years`, `skills` (chuỗi phân cách `;`). Nhãn là `salary` và luôn gắn thị trường: tổng thu nhập khảo sát USD/năm, hoặc trung điểm khoảng lương chào tuyển VND/tháng. Không chuyển ngoại tệ tự động. Lương nguồn không vào prompt hồi quy.

Nguồn quốc tế Stack Overflow 2024 (ODbL/DbCL; ghi nguồn Stack Overflow). Việt Nam TiniX, snapshot đã có trong `data/raw/tinixai_2026/data.parquet`, giấy phép nguồn CC-BY-NC-4.0. Bộ parser quy tắc được di chuyển từ lịch sử Git để kiểm tra lại kỳ lương bằng số tiền khớp trong mô tả, không nâng nhãn thiếu kỳ lên strict. Dữ liệu gốc và manifest cũ giữ trong `data/`; các file này không đồng nghĩa tất cả được train bản mới.

Tập mới là nguồn đã từng được nghiên cứu, chia lại không tạo một benchmark mới thu thập độc lập. Nhãn trích từ nguồn/rà soát quy tắc là silver, chưa phải human gold. Nhãn Việt Nam ít hơn đáng kể. Không hứa LLM tốt hơn hồi quy hoặc cam kết sai số thấp.

## Huấn luyện và đánh giá

Qwen backbone LoRA rank8 + LayerNorm/Dense64/Dense1-softplus; loss Huber trên log-lương chuẩn hóa theo thị trường. Batch1, gradient accumulation8, AdamW5e-5, tối đa2epoch. Language replay dùng đáp án trích xuất JSON và mask prompt. Chọn checkpoint trên validation. MAE/RMSE/R² báo cáo riêng từng thị trường. Thống kê kỹ năng từ train cần10 mẫu hỗ trợ; liên hệ quan sát không chứng minh tăng lương do học kỹ năng.

Tài liệu trạng thái thực thi trong `outputs/`; chưa có checkpoint/metric thì không được xem training đã hoàn thành. `predict`, `analyze`, `advise` không cập nhật trọng số. `make test` kiểm tra nhóm, leakage và đơn vị.

## Tái lập và theo dõi

Tải raw đúng phiên bản: `.venv-tf/bin/python scripts/download_data.py`. Kiểm checksum trước khi dùng; lệnh này không ghi đè raw khác checksum. `data/tensorflow_v1/README.md` mô tả bộ lọc và loại nhãn. Dữ liệu đã chia có trong source gọn; raw/trọng số lớn tải riêng.

Trên máy này, goal do `career_auto.coordinator` quản lý, registry ở `outputs/auto_dev/state.json`; xem hợp đồng trong `docs/AUTONOMOUS_GOAL.md`. Vòng Qwen gốc đã hoàn tất; controller legacy đã được kết thúc có chủ đích sau train và registry legacy được đánh dấu superseded. Không khởi chạy `pipeline-background` hoặc `run_training_pipeline.py` trong quá trình bàn giao.

`python scripts/check_tensorflow.py --device cpu` kiểm tra Qwen kích thước nhỏ khởi tạo ngẫu nhiên: có cập nhật LoRA và save/reload, chỉ là kiểm tương thích. `--device gpu` yêu cầu GPU thực sự trả tensor đầu ra; không suy ra pretrained đã chạy chỉ từ kiểm tra nhỏ. Chỉ khóa môi trường vào `requirements-lock-tf-macos-arm64.txt` sau khi bộ cài và kiểm tra thành công. Dùng lock này trên cùng nền tảng, không coi là lock cho CUDA/Linux.

Đọc CSV/XLSX/JSON theo các cột hồ sơ đã nêu; JSON là mảng các object. Có thể đưa thêm `description` để LLM trích phần thiếu; `market` và `location` phải được cung cấp. Lỗi được ghi theo dòng, không tự đoán đơn vị. `analyze` xuất `predictions.csv/json`, `figures/*.png`, bảng thống kê kỹ năng; biểu đồ từ prediction được hiểu là dự đoán. Không vẽ xu hướng thời gian khi không có cột thời gian phù hợp.

Bản biểu đồ mới trong `career_auto.charts` giữ từng quan sát hợp lệ, không loại người/tin khác nhau chỉ vì trùng đặc trưng. Biểu đồ suy luận ghi rõ predicted income và kỹ năng trong file đầu vào, không coi đó là số liệu nhu cầu tuyển dụng thực đo. Biểu đồ kỹ năng–thu nhập cần10 mẫu mỗi kỹ năng; thiếu mẫu xuất thông báo thay vì xếp hạng. CLI đã chuyển sang bản này sau khi vòng train gốc kết thúc.

Chọn checkpoint LLM bằng trung bình MAE log theo thị trường +0,1×answer-only cross-entropy trên tối đa32 mẫu validation trích xuất. Tỷ trọng này cố định trước khi đánh giá test. Báo cáo test có MAE/RMSE/R² theo thị trường, vai trò, nhóm kinh nghiệm; dưới10 mẫu gắn `low_support`. Baseline chặn log dự đoán dưới0 để đảm bảo mức lương không âm. Tư vấn kỹ năng dựa vào chênh lệch trung vị quan sát, chịu ảnh hưởng các yếu tố gây nhiễu.

Bản khôi phục source trước khi dọn ở `data/archive/pre_tensorflow_20261023/` (local, không đẩy lên Git). Notebook dùng kernel `career-ai-tf` được đăng ký trong `.venv-tf`; có thể chọn interpreter này trong VS Code. `scripts/execute_notebooks.py` chạy kernel sạch và lưu output, không bật cờ training trong notebook.

## Môi trường và bằng chứng

Môi trường đã khóa trong `requirements-lock-tf-macos-arm64.txt`; CPU vượt kiểm tra. Metal không nạp được với TensorFlow2.20, nên đã gỡ và chọn CPU. Trọng số Qwen đã tải đủ, SHA256 khớp. Vòng full hoàn tất và lưu/nạp ở tiến trình mới đạt. Chi tiết và giới hạn: `docs/RUNTIME_EVIDENCE.json`.

Baseline test: MAE30.578USD/năm (quốc tế),5,50triệuVND/tháng (Việt Nam); R² lần lượt0,4219/0,4258. Không xem đây là kết quả Qwen. 32 kiểm thử phần mềm đạt. Qwen đã chạy demo thật CSV/XLSX/JSON:4 hồ sơ hợp lệ,2 lỗi theo dòng;2 mô tả văn bản được trích xuất rồi dự đoán; tư vấn có bằng chứng hoặc báo thiếu dữ liệu. Cả5 notebook đã thực thi. Demo từ train không phải đánh giá generalization.

Chạy `python scripts/status.py` để đối chiếu PID sống với trạng thái lưu. `make pipeline-background` chỉ khởi chạy một worker tách phiên; từ chối nếu worker trước còn sống. Khi máy ngủ, tiến trình cũng có thể tạm dừng; khi worker chết, không coi file running cũ là bằng chứng tiếp tục train. Checkpoint partial là adapter/head trung gian, không bao gồm đầy đủ optimizer để tự khôi phục chính xác giữa epoch.

`python scripts/compare_runs.py --baseline outputs/BASELINE --llm outputs/QWEN --output outputs/COMPARISON` tạo bảng và biểu đồ đối chiếu, yêu cầu hai run dùng cùng snapshot và LLM đã có test full. Smoke bị từ chối. Notebook đánh giá cũng gọi lệnh này khi đủ metric. Với baseline và mô tả cần trích xuất, thêm `--extractor-run outputs/QWEN` trỏ tới LLM đã train; không dùng thư mục baseline làm extractor.

## Goal phát triển tự động

Goal và heartbeat mỗi30 phút theo `docs/AUTONOMOUS_GOAL.md`. Người dùng đã chốt model, `search_closed=true`; không mở thêm cấu hình train. `make auto-tick` điều phối bước đánh giá/demo/notebook/bàn giao kế tiếp; đây là lệnh thực thi, không chỉ xem trạng thái.

`python -m career_auto.evaluation --run outputs/RUN` và CLI `evaluate` mặc định validation. `--split test` yêu cầu selected_run được goal chốt; smoke không được chấm full. Không tự gọi train/resume của trial đã hủy. Checkpoint optimizer đã được kiểm resume thật trên smoke; điều này không thay thế đánh giá chất lượng model đã chọn.

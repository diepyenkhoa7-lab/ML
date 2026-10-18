# Chạy ứng dụng IT Career Insight

## Mở trên máy hiện tại

```bash
cd /Users/scara2906/Downloads/ML
make app
```

Mở http://127.0.0.1:8000. Lệnh build Vue và chạy FastAPI một worker, không train.
Nếu app đã chạy tại địa chỉ này, dùng ngay; Ctrl+C ở terminal chạy server để dừng.
Đổi cổng khi cần: `APP_PORT=8010 make app`.

Máy clone mới cần Python 3.11 + Node 20.19+ hoặc 22.12+:

```bash
make setup
make frontend-setup
make app
```

Model lương nhỏ có trong nhánh source. Để tái hiện trên Mac ARM64, dùng phiên bản
trong `requirements-lock-macos-arm64.txt` (scikit-learn 1.9.1 khi train model). Gemma là tùy chọn khi nhập bảng đã có cột;
muốn đọc mô tả cần bản MLX + adapter theo README/GEMMA_TUNING.md. Base weights tải
riêng, không có trong Git. App chỉ nạp artifact tin cậy khớp checksum.

## Từ bảng đến kết quả

1. Chọn CSV (UTF-8, hỗ trợ phân cách phẩy/chấm phẩy/tab/pipe), XLSX (sheet đầu),
   hoặc JSON (array object). Có bảng mẫu 48 tin thật ở giao diện và data/examples/.
2. Xem trước rồi ghép cột. Cần vai trò/chức danh, hoặc mô tả + bật Gemma.
   Cột kỹ năng có thể là array JSON hoặc chuỗi phân cách `;`/`,`/`|`.
3. Nếu có cột `salary_monthly_vnd`, hiểu là số VND/tháng. Với cột lương chung,
   numeric cần chọn tiền tệ/kỳ; hệ số triệu chỉ áp dụng giá trị số thuần.
   Chuỗi có đơn vị như `20–30 triệu VND/tháng`, `240 triệu VND/năm` tự phân tích.
   Giữ trung điểm hai cận theo quy ước nhãn model. Năm chia 12. Không tự đổi USD.
   Thiếu/không rõ đơn vị vẫn dự đoán nhưng không dùng lương đó tính metric.
4. Ngày đăng nhận ISO `YYYY-MM-DD` (kể cả timestamp) hoặc `DD/MM/YYYY`.
   Ngày lỗi có cảnh báo; thiếu ngày không tạo biểu đồ thời gian.
5. Bật Gemma khi cần đọc mô tả: tối đa 20 mô tả/lượt, kiểm tra context 2.048 token
   gồm phần dành cho output. Mô tả dài cần rút gọn, không cắt ngầm. Gemma chỉ điền
   trường thiếu; không ghi đè cột đã cung cấp. Lương Gemma đọc được lưu riêng,
   không dùng làm nhãn tính MAE. Schema lỗi được model thử lại tối đa một lần nếu đủ context; giữ cả raw attempts trong ZIP. Vẫn lỗi thì báo theo dòng, không sửa JSON để che lỗi.
   Khi không có cột kỹ năng riêng, pipeline chỉ dùng tên công nghệ có bằng chứng trực tiếp
   trong mô tả và thuộc danh mục nhận diện; giữ extraction Gemma riêng, có source_skill_evidence.
   Danh mục có thể thiếu công nghệ mới; nhập cột kỹ năng riêng để chủ động cung cấp.
   GPU bận train/đánh giá/suy luận được kiểm tra trước khi chạy; dùng “Kiểm tra lại GPU”
   sau khi tác vụ hoàn tất.
6. Bấm Phân tích. Xem tiến độ → Tổng quan / Dự đoán từng dòng / Chất lượng & sai số.
   Top công nghệ dùng danh mục v1 (alias chuẩn và công nghệ thông dụng); kỹ năng ngoài
   danh mục vẫn được giữ trong bảng. Chọn nguồn lương cung cấp/dự đoán; chọn trạng thái của từng dòng để đọc cảnh báo.
7. Tải CSV, Excel, từng PNG, hoặc ZIP gồm bảng CSV/XLSX/JSON, report.md, manifest
   (checksum đầu vào/model/code/output), biểu đồ và raw output Gemma nếu đã dùng.

Mỗi dòng giữ source_row và các cột gốc dưới tiền tố input_. Dòng lỗi vẫn được xuất,
không đi vào model. Trùng hoàn toàn giữ dự đoán nhưng loại khỏi metric/biểu đồ.
CSV/XLSX escape chuỗi giống công thức; JSON giữ giá trị gốc.

## Tư vấn nghề nghiệp

Chọn vai trò, cấp bậc, kinh nghiệm, khu vực, kỹ năng → Dự đoán & xem gợi ý.
Model hiện tại là Ridge v2; RF dùng đối chiếu (theo configs/application.json). Gợi ý lấy từ kỹ năng có ít nhất 5 mẫu
train và hệ số Ridge dương, xếp theo mức tăng dự đoán model chính khi thêm một kỹ năng, cần ít nhất 5 mẫu cùng vai trò.
Chỉ đề xuất nếu chênh lệch model dương; nếu không có thì báo chưa đủ bằng chứng.
Đây là quan hệ từ model/dữ liệu, không chứng minh học kỹ năng sẽ tăng thu nhập.
Giải thích được điền bằng Python từ số liệu kiểm tra được; Gemma phụ trách trích xuất.

## Giới hạn và dữ liệu

- Local một người dùng, chỉ bind 127.0.0.1; một worker, không phải bản deploy public.
- 10 MiB/file, 2.000 dòng, 100 cột; XLSX giải nén tối đa 50 MiB.
- Vai trò hỗ trợ: tám vai trò trong model; các nghề khác báo chưa hỗ trợ thay vì đoán.
- Dữ liệu upload và kết quả ở outputs/app_runtime/, được ignore và không publish.
  Job hoàn tất đọc lại được sau restart; job dang dở được đánh dấu cần chạy lại.
  Xóa một thư mục UUID ở đây sau khi dừng app nếu muốn xóa dữ liệu tương ứng.
- Không có MAE/RMSE/R² khi thiếu nhãn. Metric bảng nhập không phải kiểm định độc lập,
  nhất là dữ liệu mẫu lấy từ train. V2 test mới30 tin, Ridge MAE khoảng4,43 triệu; v1 lịch sử test28 tin MAE6,66 triệu, khác tập.
- Nhãn silver; gross/net chưa rõ; không suy số năm từ seniority. Không có khoảng tin
  cậy được hiệu chỉnh nên app không bịa khoảng chắc chắn quanh dự đoán.
- Các lệnh train/suy luận/evaluate của dự án dùng khóa GPU chung `.cache/gemma-gpu.lock`;
  nếu đang có lượt khác, lệnh mới báo bận trước khi nạp model. Lệnh gọi trực tiếp
  `python -m mlx_lm ...` bên ngoài wrapper không tham gia khóa này; không chạy đồng thời.
- Chỉ nhận tối đa 2 lượt phân tích (1 đang chạy, 1 chờ); API trả 429 và Retry-After khi đầy.
- Dữ liệu nhập mới có checksum snapshot và phiên bản. Bảng đã lưu từ bản cũ cần nhập
  lại trước khi tạo job mới; kết quả lịch sử hoàn tất vẫn đọc được. Trạng thái JSON
  hỏng được giữ thành `state.corrupt.<id>.json` và đánh dấu lỗi, không chặn app khởi động.
- Phản hồi Gemma có request_id, index và hash nội dung từng mô tả; thiếu/thừa/đảo
  dòng đều bị từ chối. Web có tối đa một lượt model thử lại khi lỗi schema và đủ
  context, giữ cả raw attempts; benchmark đánh giá vẫn dùng một lượt. Khi lỗi worker, xem
  `outputs/app_runtime/<job_id>/gemma_worker.json`; payload sai hợp đồng được giữ
  trong `gemma_invalid_transport.txt`. Các log này ở local, không đưa vào Git.
- Tab Chất lượng & sai số hiển thị adapter thực sự đã dùng, số dòng trích thành công/lỗi
  và link raw JSON. Bảng từng dòng có trạng thái Gemma; chọn Gemma nhưng không có
  mô tả thì ghi rõ chưa gọi, không gán provenance adapter giả.
- Khi sửa hồ sơ tư vấn, kết quả cũ được xóa và phản hồi đến muộn bị bỏ qua. Gợi ý
  kỹ năng tính trực tiếp từ Ridge đã fit và train đã kiểm chứng, không tin CSV báo cáo sửa tay.

## Kiểm thử và phát triển

```bash
make app-test
make lint
npm --prefix frontend run format:check
# phát triển: một terminal make api; terminal khác:
npm --prefix frontend run dev
```

API/OpenAPI: http://127.0.0.1:8000/docs. Endpoint chính:
`POST /api/datasets`, `POST /api/datasets/demo`, `POST /api/analyses`,
`GET /api/analyses/{id}`, `GET /api/analyses/{id}/rows`,
`GET /api/analyses/{id}/artifacts/{name}`, `POST /api/salary/predict`,
`POST /api/career/advice`. Endpoint Gemma được tích hợp trong job phân tích
qua `use_gemma: true`, không có endpoint train.

Bản v2: xem [SALARY_V2_RUNBOOK](SALARY_V2_RUNBOOK.md). Badge, bảng và biểu đồ lấy model
của chính job, nên kết quả lịch sử không bị gán nhãn model mới. Mục tư vấn hiển thị riêng
trung vị khảo sát ITviec, không dùng nó thay lương chào tuyển dự đoán. Train có1078 nhãn
thiếu kỳ lương với giả định tháng/trọng số0,3; không coi toàn bộ dữ liệu là gold.

Kịch bản trình bày đã có bằng chứng chạy: [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

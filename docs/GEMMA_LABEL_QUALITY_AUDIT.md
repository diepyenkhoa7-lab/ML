# Rà soát chất lượng nhãn Gemma sau reviewed v2

## Phát hiện đã xác minh

Giả thuyết ban đầu chỉ có lỗi model là chưa đủ. Đối chiếu văn bản hiển thị xác nhận các nhãn silver thiếu kỹ năng có thật và bỏ sót số năm viết bằng chữ/dấu cộng:

- `tinixai:198658`: câu “Có ít nhất một năm kinh nghiệm phát triển các dự án liên quan” cần 1 năm, không phải null.
- `tinixai:335784`: văn bản nêu TensorRT / ONNX / OpenVINO nhưng nhãn skills bỏ sót cả ba.
- `tinixai:449770` và `466600`: BERT, T5, Mistral, LLaMa, GPT, Deep Learning, Langchain, llamaindex, RESTAPI hiện diện; bộ từ khóa cũ bỏ sót.
- Train `35981`, `38690`, `8639`: các dạng 2+ years, 1+ years và 4–6+ năm không được parser cũ nhận đủ.

`data/annotation/gemma_v2.1.1/` đã quét 137 tin train mới và 31 validation, không đọc ví dụ test. Có 18 đề xuất thay đổi; sau đối chiếu nguồn, chấp nhận 17 (7 train, 10 validation), bác bỏ 1. `tinixai:4622` giữ 2 năm tổng thể production vì các yêu cầu 1 năm là chuyên môn thành phần. `277770` giữ tên cụ thể Ant Design Mobile, không rút về framework cha. Đây là **AI source review, không phải human gold**.

Bản draft `gemma_v2.1.0` được giữ với builder snapshot/checksum; vòng `2.1.1` bổ sung dạng dấu cộng và công nghệ có bằng chứng trong train. Các file proposal và quyết định là artifact riêng, không ghi đè corpus/split/protocol cũ. Builder cũng không lấy công nghệ từ địa chỉ/công ty hoặc số năm từ salary.

## Chẩn đoán độ nhạy với nhãn

Dùng đúng raw predictions đã lưu, giữ trọng số và đầu vào; chỉ áp dụng 10 quyết định validation trong bộ nhớ để đo tác động nhãn tham chiếu:

| Adapter | F1 với reference cũ | F1 với reference đã sửa một phần |
|---|---:|---:|
| Parent đang phục vụ | 0,727273 | 0,805825 |
| Candidate 501 bước | 0,784946 | 0,857143 |

**Các số tăng trong từng hàng là thay đổi cách chấm, không phải model được cải thiện.** Không thay selection cũ, không tuyên bố candidate đạt promotion: ba legacy guards vẫn thất bại. Nhãn sửa mới chỉ là một lượt có phạm vi, từ điển vẫn có thể thiếu công nghệ. Cần hoàn thiện nhãn, khóa corpus/protocol mới và chấm baseline cùng reference trước khi fine-tune lại.

## Trạng thái

- Đã có code chạy thật: `scripts/refine_gemma_references.py`, `scripts/adjudicate_gemma_corrections.py`, cùng artifact chứa dẫn chứng/hash.
- Đã có regression tests cho chữ số, tháng/năm, dấu cộng, kinh nghiệm mâu thuẫn, không suy kỹ năng nền, không lấy địa chỉ làm nhãn và giữ kinh nghiệm tổng thể.
- 84 tests và Ruff check/format 62 file đạt.
- Chưa tạo corpus train mới từ các quyết định; chưa train vòng tiếp theo. Adapter web, model lương và các test không thay đổi.
- Luồng nhập file còn giới hạn Gemma 20 dòng và context 1024 token; worker hiện từ chối mô tả quá dài. Đây là hạng mục ứng dụng cần cải thiện tiếp, chưa được coi là đã giải quyết trong lượt audit nhãn.
- Báo cáo theo mẫu và tên STT/họ tên/MSSV còn cần thông tin người dùng; công việc model/app vẫn tiếp tục độc lập.

Chi tiết quyết định và diagnostic ở `data/annotation/gemma_v2.1.1/adjudicated_changes.jsonl` và `cached_validation_diagnostic.json`. Không chạy lại hai script vào output cũ vì artifact được giữ bất biến.

Bản source copy độc lập đã chạy lại 84 tests, Ruff, strict SFT/frozen split checks, npm ci offline, Prettier và production build, tất cả exit 0. Bằng chứng ở `data/annotation/gemma_v2.1.1/source_export.json`; report này được thêm sau lần kiểm thử, không đổi code hoặc nhãn.

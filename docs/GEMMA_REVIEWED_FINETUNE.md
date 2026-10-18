# Gemma: rà soát 214 nhãn và fine-tune từ dữ liệu đã duyệt

Người dùng xác nhận ngày 18/10/2026: “bắt đầu duyệt và fine tune”. Đây là lượt fine-tune Gemma trích xuất JSON; không phải train lại mô hình hồi quy dự đoán lương và không chứng minh MAE thu nhập giảm.

## Rà soát nhãn

Giữ nguyên queue cũ `data/annotation/v3.1.0/`. Bản rà soát mới ở `data/annotation/gemma_v2.0.0/review.jsonl` có đủ 214 quyết định, dẫn chứng, các trường thay đổi, checksum nguồn và lý do loại. **201 dòng được chấp nhận, 13 dòng bị loại**. Nhãn là **AI-reviewed silver**, không phải human gold; `gold=null` được giữ rõ ràng.

Đã kiểm tra toàn bộ danh sách chức danh, kiểm tra tự động trên từng bản ghi và đọc sâu văn bản gốc cho các ca nghi ngờ. Các ca bị loại gồm lập trình máy phay/CNC, máy đột/cắt laser, khuôn/cơ khí, lắp đặt điện/AV, phát triển sản phẩm thời trang và tuyển nhiều vai trò quản lý/kiến trúc không rõ một vai trò trong schema. Không đổi nhãn salary/split đã đóng băng của v3/v3.1.

Nhãn trích xuất mới chỉ dựa vào văn bản thực sự đưa cho Gemma:

- Kinh nghiệm lấy từ câu có số năm/tháng rõ trong chức danh/yêu cầu; không suy từ Senior/Junior và không sao chép trường metadata khi thiếu bằng chứng. 105/201 đầu vào không đủ một giá trị rõ nên giữ `null`; “không yêu cầu kinh nghiệm” rõ ràng là 0. Ca có số năm khác nhau không tự chọn số thấp nhất.
- Vai trò dựa vào chức danh; sửa 8 nhãn chức danh như Mobile, Embedded, AI Engineer hoặc các tiêu đề ghi cả Frontend/Backend. Không biến kinh nghiệm với sản phẩm AI thành vai trò ML Engineer.
- Kỹ năng lấy từ các tên công nghệ hiện diện, chuẩn alias; không suy Java từ JavaScript, React từ React Native hoặc ngôn ngữ nền tảng từ framework. Danh sách kỹ năng đề xuất cũ không được chèn làm đáp án có sẵn trong prompt.
- Địa điểm lấy từ trường gốc và chuẩn tên thành phố khi rõ. Đây là trường được bổ sung cho schema Gemma, không được gọi là hàng trăm lỗi địa điểm đã sửa vì queue đề xuất cũ chưa có trường này.
- Giữ hai cận tiền, VND và kỳ tháng có dẫn chứng; không lấy midpoint làm nhãn trích xuất. Có thể đọc câu lương tháng rõ trong nội dung thay vì khung phân loại header thiếu kỳ.

Với yêu cầu dài, builder chọn các câu nguồn nguyên vẹn nằm trong ngân sách context. Nhãn kỹ năng/kinh nghiệm được tính lại trên phần hiển thị đó. Đây là trích đoạn rõ ràng, không phải gắn nhãn của cả bài vào một prompt đã bị cắt mất bằng chứng. Mỗi input cộng 256 token đáp án nằm trong context 1.024 của worker web.

## Corpus và protocol

`data/finetune_reviewed/v2.0.0/`:

| Tập | Số mẫu | Ý nghĩa |
|---|---:|---|
| Train | 501 | 137 tin mới + 364 mẫu silver replay cũ để giữ định dạng và hành vi thiếu trường |
| Validation mới | 31 | 31 tin nguồn độc lập, 24 nhóm công ty |
| Test mới | 33 | 33 tin nguồn, 24 nhóm công ty; chỉ mở sau khi đạt validation |

Tất cả 201 tin mới kế thừa split theo công ty, seed 20261018. Validation/test mới loại công ty của train adapter cha. Valid/test v1 đã bị loại khỏi đầu vào queue ban đầu. Test Gemma cũ không mở lại để tuning; validation cũ 72 mẫu chỉ làm regression guard. Không gọi 501 mẫu train là 501 tin mới do con người duyệt: 364 là replay cũ và có biến thể từ cùng tin.

Protocol `configs/gemma_reviewed_protocol.json` được khóa trước khi chấm baseline và train: **một candidate**, một epoch, LR `1e-5`, batch 1, rank 8, 4 layers, prompt masking, gradient checkpoint, context 1024. Tiếp tục từ adapter `20261017T105728Z`, optimizer khởi tạo lại; chuyển corpus phải có checksum adapter cha, manifest corpus cũ/mới và hyperparameter khớp protocol. Lệnh từ chối lượt train thứ hai dùng cùng protocol.

Chọn bằng score validation mới: `0.5 × mean field exact + 0.3 × Skill F1 + 0.2 × schema validity`, tăng ít nhất 0,005, schema mới ít nhất 90%, JSON validity không giảm. Validation cũ không được giảm score quá 0,01, Skill F1 quá 0,015 hoặc schema validity quá 0,01. Nếu không đạt, giữ adapter web cũ và không mở test mới. Nếu đạt, chấm baseline/candidate một lần trên test mới trước khi quyết định tích hợp. Không tối ưu tham số theo test.

Baseline cùng 31 validation mới: Skill F1 **0,72727**, mean field exact **0,85081**, JSON/schema validity **1,0**. Không so trực tiếp với Skill F1 0,93756 trên 72 job-card cũ như thể cùng tập. Lỗi baseline tập trung ở kỹ năng và kinh nghiệm khi đọc trích đoạn nguồn.

## Train và suy luận là các lệnh khác nhau

```bash
# Kiểm tra corpus/lineage, KHÔNG train
make gemma-reviewed-plan

# TRAIN THẬT 501 bước; một candidate theo protocol đã khóa
make gemma-reviewed-train

# Chỉ suy luận trên web, KHÔNG cập nhật trọng số
make app
```

`make gemma-adapter` vẫn là luồng corpus cũ; dùng `gemma-reviewed-train` cho lượt dữ liệu mới này. Script preserve artifact và không tự thay adapter web. Theo dõi run thực:

```bash
tail -f outputs/training_logs/gemma_20261018T002705Z/console.log
```

Run `20261018T002705Z` đã hoàn tất **501/501 bước**, exit code 0. Train loss cuối 0,006; validation loss toàn bộ 31 mẫu giảm từ 0,392 xuống 0,110. Đây là loss được log làm tròn, không phải độ chính xác trích xuất. Config, xác nhận người dùng và lineage nằm trong thư mục log; adapter mới lưu riêng tại `adapters/gemma-jobs/20261018T002705Z/`. Đọc `run.json`, `summary.json` và kết quả raw extraction tại `outputs/metrics/gemma_reviewed_v2/` để đánh giá; adapter web chỉ đổi sau khi đạt protocol.

## Kết quả nghiệm thu

Đã train xong và chấm raw extraction. Trên 31 validation mới: Skill F1 **72,73% → 78,49%**, schema **100% → 93,55%**, score **0,843585 → 0,852016**. Trên 72 validation cũ: Skill F1 **93,76% → 90,22%**, schema **95,83% → 93,06%**, score **0,941685 → 0,922048**. Cả ba regression guard cũ không đạt.

Vì vậy **không promote**, giữ adapter web `20261017T105728Z`, test mới 33 tin chưa được chấm và test cũ không mở lại. Không train trùng cùng protocol. Báo cáo đầy đủ, raw predictions và từng gate ở `outputs/metrics/gemma_reviewed_v2/REPORT.md` và `selection.json`. 79 unit tests, Ruff và strict corpus đều đạt; kiểm thử phần mềm không thay thế chất lượng extraction.

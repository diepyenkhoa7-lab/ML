# Hợp đồng dữ liệu

## Dataset dự đoán lương

Mỗi hàng là một tin tuyển dụng; nếu dùng khảo sát thì ghi rõ loại nguồn và không
diễn giải số người trả lời khảo sát thành nhu cầu tuyển dụng.

| Trường | Quy ước |
|---|---|
| record_id | ID ổn định; các bản sao/biến thể cùng tin phải được nhóm cùng nhau khi chia tập |
| source | Nguồn và URL/ID có thể truy vết |
| posted_date | ISO date; thiếu ngày thì không kết luận xu hướng theo thời gian |
| role, level, location | Chuẩn hóa danh mục trước EDA; ghi lại bảng ánh xạ |
| experience_years | Số năm kinh nghiệm; thiếu để null, không mặc định 0 |
| skills | Chuỗi phân cách bằng dấu `;`, ví dụ `Python;FastAPI;PostgreSQL` |
| salary_min, salary_max | Số tiền theo đơn vị currency/period; thỏa thuận để null |
| currency | VND, USD,... |
| salary_period | month hoặc year; các kỳ khác cần quy tắc riêng |
| salary_basis | gross, net hoặc unknown; không gộp tùy tiện các nhóm này |
| description | Tin gốc để trích xuất; không dùng làm feature lương nếu chứa nhãn |

Pipeline hiện có thêm `salary_monthly_vnd` chỉ cho tiền tệ VND,
`salary_monthly_native`, `target_definition`, `salary_basis` và thông tin nguồn/ngày.
Nếu thực hiện quy đổi ngoại tệ sau này phải thêm `fx_rate_to_vnd`, `fx_date`, `fx_source`.
Với khoảng đủ hai đầu, dùng trung điểm rồi chia 12 nếu là lương năm, sau đó nhân
tỷ giá VND khi có bảng tỷ giá và chính sách rõ ràng; bản hiện tại không đổi ngoại tệ.
Với chỉ một đầu lương, giữ nhãn thiếu trong phiên bản đầu, trừ khi nhóm
công bố một quy tắc riêng. Lương thỏa thuận không được đổi thành 0.

Không đưa `salary_min`, `salary_max`, tỷ lệ quy đổi có thể làm lộ nhãn, hoặc mô tả
chứa lương vào features. Fit tiền xử lý trên train; validation chọn cấu hình,
test chỉ đánh giá cuối. Khử trùng/nhóm cùng tin trước khi chia. Nếu đủ ngày đăng,
ưu tiên test trên giai đoạn sau. `configs/salary.yaml` mới là cấu hình dự kiến,
chưa có pipeline huấn luyện nghiệp vụ.

## Dataset fine-tune

Ba file thật: `data/finetune/{train,valid,test}.jsonl`. Mỗi dòng có
`source_record_id` và `messages` gồm user/assistant, có thể thêm system.
Nhãn trích xuất là chuỗi JSON trong `assistant.content`. Không có thông tin trả null.
Nhãn tư vấn phải bám số liệu được truyền vào prompt.

Chia nhóm nguồn trước khi sinh thêm biến thể. Công cụ `scripts/validate_sft.py`
kiểm tra cấu trúc, ID nguồn và prompt trùng giữa các tập; nhóm vẫn phải rà soát
ngữ nghĩa và những tin gần trùng mà kiểm tra tự động chưa phát hiện.

## Nguồn gốc và bàn giao

Lưu nguồn, ngày lấy, quyền chia sẻ, số dòng trước/sau làm sạch, đơn vị lương và
các giới hạn trong `data/DATA_CARD.md`. Giữ file gốc ở `data/raw/`, bản sạch ở
`data/processed/`, danh sách ID chia tập ở `data/splits/`. Dataset được phép chia sẻ
và kết quả đánh giá không bị ignore. Nếu không thể đưa lên Git, bàn giao link tải
cùng checksum và hướng dẫn. Các nguồn đã nhập, độ mới và giới hạn được ghi trong
`docs/DATA_SOURCES.md`; số đếm thực tế nằm ở `outputs/data_quality/source_inventory.json`.
Các CSV ứng viên chưa thay thế bước làm sạch hoặc bộ train/valid/test cuối cùng.
CSV chuẩn hóa và nhãn hiện có ở `data/processed/cleaned/`; quy tắc, ý nghĩa từng
file và giới hạn ở [DATA_CLEANING.md](DATA_CLEANING.md). Bộ chia sau rà soát nhãn
hiện hành nằm ở `data/splits/v1.0.1/`, xem
[LABEL_REVIEW_AND_SPLITS.md](LABEL_REVIEW_AND_SPLITS.md).

# Kết quả goal TensorFlow

Model được chọn: `outputs/qwen_20261023T082631`.
Chọn bằng validation; không dùng kết quả test để thay cấu hình.

| Thị trường | Đơn vị | n | MAE baseline | MAE LLM | RMSE LLM | R² LLM |
|---|---|---:|---:|---:|---:|---:|
| international | USD/year | 3157 | 30577.77 | 30282.04 | 57703.57 | 0.4374380101390939 |
| vietnam | VND/month | 49 | 5497220.55 | 6019790.60 | 8321248.87 | 0.2513921873244741 |

JSON schema rate: 1.0; Skill F1: 0.6599326599326599.
Nhãn ngôn ngữ là silver, chưa phải human gold; xem độ khớp từng trường trong handoff.json.

## Phân tích lỗi và giới hạn

Các nhóm sai số theo vai trò/kinh nghiệm nằm trong metric JSON; 10 dòng có sai số tuyệt đối lớn nhất mỗi thị trường ở largest_errors.csv.
- Nhóm vai trò MAE cao nhất với ít nhất10 mẫu: international | Senior Executive (C-Suite, VP, etc.), MAE 97186.36, n=35.
- Nhóm vai trò MAE cao nhất với ít nhất10 mẫu: vietnam | Software Developer, MAE 6753682.61, n=29.

Đây là mô tả lỗi, không chứng minh nguyên nhân. Khác biệt khu vực, thành phần thu nhập và độ nhiễu nhãn là giả thuyết cần nghiên cứu riêng.
Dữ liệu Việt Nam ít và là lương chào tuyển; khảo sát quốc tế là tổng thu nhập USD/năm. Không gộp hai đơn vị, không bảo đảm tăng lương khi học kỹ năng.
Nguồn từng được nghiên cứu và baseline test đã mở trước; không gọi là benchmark độc lập mới.
Không công bố LLM tốt hơn baseline nếu metric thực tế không cho thấy điều đó.

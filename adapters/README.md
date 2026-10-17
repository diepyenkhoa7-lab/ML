# Adapter artifacts

`gemma-smoke/` dành riêng cho kiểm tra 20 iterations trên mẫu giả lập.
`gemma-jobs/` dành cho huấn luyện dữ liệu thật. Không dùng smoke adapter để báo cáo
kết quả fine-tune hoặc thay thế adapter nghiệp vụ.

Các file trọng số adapter được ignore mặc định. Khi bàn giao, cung cấp file/URL tải,
checksum, model revision và cấu hình huấn luyện tương ứng.

Bản dùng mặc định sau đợt tuning: `gemma-jobs/20261017T105728Z/`, chọn bằng
validation, không phải run mới nhất. Lượt cuối `20261017T111205Z` giảm điểm nên
không được chọn. `outputs/metrics/gemma_tuning/recommendation.json` ghi checksum,
điểm validation/test và giới hạn sau đánh giá cuối. Final adapters nhỏ được đưa
lên nhánh source; trọng số base và checkpoint trung gian giữ local.

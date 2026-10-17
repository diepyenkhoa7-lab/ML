# Adapter artifacts

`gemma-smoke/` dành riêng cho kiểm tra 20 iterations trên mẫu giả lập.
`gemma-jobs/` dành cho huấn luyện dữ liệu thật. Không dùng smoke adapter để báo cáo
kết quả fine-tune hoặc thay thế adapter nghiệp vụ.

Các file trọng số adapter được ignore mặc định. Khi bàn giao, cung cấp file/URL tải,
checksum, model revision và cấu hình huấn luyện tương ứng.

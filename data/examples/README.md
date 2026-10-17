# Dữ liệu mẫu kiểm tra môi trường

`jobs_template.csv` chỉ có header để nhóm điền dữ liệu thật. Các mẫu trong
`finetune/` do dự án tự viết, là tin **giả lập** để kiểm tra định dạng và train ngắn.
Không đưa các mẫu này vào dataset thị trường, thống kê EDA hoặc benchmark chất lượng.
Không trộn adapter `gemma-smoke` với adapter huấn luyện thật `gemma-jobs`.

`source_record_id` liên kết mỗi mẫu với một tin nguồn. Mọi biến thể của cùng tin phải
ở cùng tập. MLX-LM dùng trường `messages` và bỏ qua metadata này.

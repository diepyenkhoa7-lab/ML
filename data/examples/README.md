# Dữ liệu mẫu kiểm tra môi trường

`international_demo.csv/.xlsx/.json` là cùng 12 hồ sơ thật từ **train** của
`global_survey_v1_7f2c2dbf6989`, nguồn Stack Overflow Developer Survey 2024.
Nhãn `salary_annual_usd` là tổng thu nhập USD/năm. Dùng để thử nhập/xuất và
ghép cột, không phải test độc lập hoặc dữ liệu mới. Xem docs/INTERNATIONAL_DATA.md
và data/raw/stackoverflow_2024/README.md về ODbL/DbCL và ghi nguồn Stack Overflow.

`jobs_template.csv` chỉ có header để nhóm điền dữ liệu thật. Các mẫu trong
`finetune/` do dự án tự viết, là tin **giả lập** để kiểm tra định dạng và train ngắn.
Không đưa các mẫu này vào dataset thị trường, thống kê EDA hoặc benchmark chất lượng.
Không trộn adapter `gemma-smoke` với adapter huấn luyện thật `gemma-jobs`.

`source_record_id` liên kết mỗi mẫu với một tin nguồn. Mọi biến thể của cùng tin phải
ở cùng tập. MLX-LM dùng trường `messages` và bỏ qua metadata này.

# Dữ liệu fine-tune thật

Ba file JSONL ban đầu đang trống. Mỗi dòng sau này cần `source_record_id` và
`messages` user/assistant. Giữ mọi biến thể của một tin nguồn trong cùng một split.

Kiểm tra trước khi train: `make validate-sft`.
Mẫu kỹ thuật nằm riêng ở `data/examples/finetune/`, không được trộn vào dataset thật.

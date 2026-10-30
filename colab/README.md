# Colab A100: Qwen3 TensorFlow

Notebook live: https://colab.research.google.com/drive/1T6W4K1It62Px0TpI-Fxs0PETvHGoyKGe

Không upload file hay checkpoint local. Tải source công khai tại commit 550065adb0f693dee0d2fbb19419e00d74500cae; tải raw và pretrained chính thức đúng revision/checksum. Tái tạo dataset, giữ split/nhãn/đơn vị như local. Train từ pretrained, không từ checkpoint Mac.

14 cell: cấu hình; môi trường; raw/clean/split/EDA; TensorFlow baseline; pretrained; A100/CLI/charts; smoke/resume/reload; full training; validation; so sánh; demo CSV/XLSX/JSON và tư vấn; final test; tests/năm notebook/manifest; theo dõi và xuất kết quả.

Đã xác minh A100-SXM4 40 GB VRAM. Giữ FP32, context1024, batch1, accumulation8, tối đa2epoch. Backbone và language loss trên GPU; không offload loss sang CPU. Full chỉ được chạy sau smoke thật đạt cập nhật LoRA, optimizer resume và fresh-process reload.

Bản ipynb ở đây là backup source mới, chưa có execution output. Xem kết quả thật ở notebook Colab. /content là tạm thời: tải checkpoint trước khi phiên bị xóa. Không sửa source/môi trường khi đang train. Nguồn đã nghiên cứu trước, nhãn VN silver, test không dùng chọn cấu hình; chỉ công bố chất lượng sau đo thật.

Mốc kiểm chứng 25/10/2026 (giờ Việt Nam): Colab đã tải raw, tái tạo đúng checksum, chạy EDA, train baseline và kiểm tra nạp lại. Smoke A100 đạt actual_lora_update, mid_epoch_optimizer_resume, completed_after_resume và fresh_process_prediction_parity. Train full A100 đã tới ít nhất 11 hồ sơ/epoch1 và một optimizer step thật; chưa có metric LLM full. Các cell đánh giá/demo/test/năm notebook đã được xếp sau full; chưa được coi là hoàn thành. Local PID19191 vẫn chạy độc lập tại thời điểm kiểm tra.

# Nghiệm thu dashboard và nhánh quốc tế

## Đã thực hiện

- Tải thật ba nguồn pinned, `make open-data-verify` xác nhận tất cả bytes/SHA raw. Audit: `outputs/data_quality/open_sources_20261018.json`.
- Train thật SO2024 và AIJobs; nguồn/split/protocol/validation selection/test/models có manifest riêng. Không train Level vì thiếu period/experience; không fine-tune Gemma với dữ liệu quốc tế. Metric và giới hạn: `docs/INTERNATIONAL_DATA.md`.
- Dashboard phân tích 5 biểu đồ train SO2024 hoặc 5 biểu đồ strict train Việt Nam; bảng so Ridge/RF/baseline riêng theo dataset/unit; profile → hai dự đoán và gợi ý có số mẫu hỗ trợ.
- Browser thật tại `http://127.0.0.1:8000/`: tải CSV quốc tế 12 mẫu qua file chooser → ghép đúng 5 cột → phân tích thành công 12/12 → biểu đồ → metric → tải ZIP. Các mẫu này lấy từ train, chỉ kiểm tra chức năng, không phải kết quả generalization.
- ZIP tải qua browser có CRC đúng, toàn bộ SHA của file trong manifest khớp, đúng `USD/year`, không có trường dự đoán VND giả. ID và ZIP hash ở `download_verification.json`.
- Browser xác nhận tư vấn Backend/USA/3 năm/Python+SQL trả RF khoảng 86,9 nghìn USD/năm, Ridge khoảng 102,4; không có panel ITviec. Đây là ví dụ suy luận, không phải lương thị trường thực hoặc metric mới.
- Browser chuyển bảng so sánh từ SO2024 sang Việt Nam: test 3.158 → 30, USD/năm → VND/tháng, model được chọn và các metric đổi đúng ngữ cảnh.
- Kiểm tra desktop 1440×1000 và mobile 390×844. Dashboard, model comparison và advice không tràn ngang document (390/390); menu mobile chia 3 cột. Ảnh thật trong thư mục này.
- 105 unit/acceptance tests đạt; Ruff check/format và Prettier/Vite build đạt. Source-only copy không có raw/caches/runtime vẫn đạt 105 tests, build frontend và tái tạo gói quốc tế cùng hash. Full test transcript được lưu cùng bằng chứng.

## Ranh giới xác nhận

Sai số khảo sát quốc tế vẫn đáng kể; self-report không phải gold, grouped profile split không chứng minh độc lập người/công ty và không phải temporal test. SO2024 không phản ánh mức lương mới nhất 2026. Khảo sát, AIJobs benchmark và tin Việt Nam không so trực tiếp metric khác mục tiêu/đơn vị.

Gemma còn tích hợp cho nhánh tin Việt Nam theo adapter cũ; chưa chạy lại GPU inference trong vòng nghiệm thu quốc tế này. Không có bằng chứng deployment public hay buổi demo trước giảng viên. Báo cáo cá nhân nằm ngoài phạm vi. Browser file chooser phản hồi chậm bất thường; file cuối cùng đã nhập thành công, không kết luận đó là lỗi hoặc benchmark hiệu năng của API.

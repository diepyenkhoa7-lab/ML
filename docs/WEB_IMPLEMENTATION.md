# Web CareerLens — Vue 3 JS + FastAPI

Triển khai theo yêu cầu ngày 26/10/2026. Dùng Qwen `outputs/qwen_20261023T082631` (adapter và đầu lương đã học, epoch1 đã chọn) và baseline hiện có. Không train, không đổi raw/nhãn/split/trọng số.

Frontend Vue3/Vite, JavaScript và CSS; backend Python/FastAPI phục vụ luôn bản build. Thiết kế theo hướng dữ liệu: nền sáng, thanh điều hướng xanh than, điểm nhấn xanh chanh, bố cục rõ số liệu và đơn vị. Vận dụng backend-patterns cho service/repository/queue; frontend-slides cho phân cấp nội dung và responsive, taste cho tính nhất quán, không biến ứng dụng thành video/slide.

Luồng: xem dữ liệu train → lọc/tìm → biểu đồ nguồn; hoặc tải CSV/JSON/XLSX → xem trước/ghép cột → tác vụ suy luận có tiến độ → lỗi từng dòng, dự đoán, baseline, gợi ý tùy chọn → xuất CSV/XLSX/JSON/PNG. Form cá nhân dùng cùng dịch vụ.

API: `/api/overview`, `/api/records`, `/api/metrics`, `/api/uploads`, `/api/analyses`, `/api/profiles`, `/api/jobs`, `/api/jobs/{id}/results` và download. Một worker suy luận, model nạp lười và dùng lại, không có endpoint train. Trạng thái và đầu ra riêng dưới outputs/web; lần khởi động sau đánh dấu tác vụ dở dang, không tự chạy lại.

Giới hạn demo local: file10MB, tối đa500 dòng; tư vấn tối đa20 dòng/lần. Không cắt dữ liệu âm thầm. Hai thị trường giữ đơn vị riêng. Thu nhập nhập vào chỉ dùng đối chiếu nếu có unit đúng; không đi vào đặc trưng. Kỹ năng khảo sát không gọi là nhu cầu tuyển dụng; liên hệ thu nhập không phải nhân quả. Demo chạy127.0.0.1, một process, chưa là dịch vụ đa người dùng công khai.

Kiểm chứng: API/validation/file path/queue bằng tests; browser thật ở desktop/tablet/mobile; upload3 định dạng và hồ sơ/văn bản bằng model thật; kiểm tải kết quả và biểu đồ, console, tiến độ và lỗi. Fixture không tính là chất lượng AI.

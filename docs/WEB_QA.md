# Kiểm chứng web — 26/10/2026

Đã kiểm bằng ECC chrome-devtools với server FastAPI tại127.0.0.1:8000, frontend Vue3/JavaScript bản production build. Dùng `backend-patterns`, `fastapi-patterns`, `mle-workflow`; vận dụng phân cấp/responsive của `frontend-slides` và hướng hình ảnh nhất quán của `taste`. Không tạo slide/video thay cho web.

## Luồng thực tế

- Form trình duyệt: Frontend Developer, Hà Nội,2năm, git/javascript → Qwen19793393,28VND/tháng, khớp CLI đã kiểm. Baseline22756252,29; không dùng số này làm benchmark mới.
- Browser upload JSON:3 dòng,2 dự đoán hợp lệ ở hai thị trường,1 lỗi; ghép cột, tiến độ, lịch sử, biểu đồ và download hoạt động. Tư vấn quốc tế trả3 kỹ năng có support87/19/24, giải thích tiếng Việt; Việt Nam báo insufficient_data.
- HTTP với model thật: CSV/JSON/XLSX đều2 hợp lệ/1 lỗi, cùng dự đoán trong rtol1e-5, đúng hai đơn vị; mỗi tác vụ xuất3 định dạng và10PNG đọc được. Tin tuyển dụng văn bản được Qwen trích rồi dự đoán. `outputs/web/real_http_acceptance.json`, log `real_http_final.log`.
- Tìm python + Backend Developer tại Việt Nam hiển thị4 hồ sơ, link xuất giữ bộ lọc. Đổi quốc tế giữ tìm kiếm, đổi đúng đơn vị USD/năm.
- Menu mobile mở/đóng được, Escape đóng menu. Đã xem screenshot desktop/mobile; không tràn ngang ở375/768/1440. Bốn số liệu dashboard375px không bị cắt.

Plugin chặn đọc đường dẫn file/screenshot của workspace qua API filesystem riêng. Vì vậy file browser QA được tạo bằng File/DataTransfer từ dữ liệu API rồi đưa qua input Vue; CSV/XLSX file vật lý được gửi bằng HTTP smoke. Không gọi kiểm native OS file chooser là đã tự động xác minh. Screenshot đã xem trực tiếp qua plugin, không có baseline ảnh cũ để khẳng định visual regression; phần regression là INCONCLUSIVE.

## Kiểm tra kỹ thuật

39 unittest đạt, gồm7 bài API/queue/upload/restart/giới hạn; fixture chỉ chứng minh phần mềm. Model thật được kiểm riêng như trên. `outputs/web/all_tests.log`.

Vite build đạt; Ruff đạt; pip check không có xung đột. Trọng số adapter/đầu lương giữ nguyên checksum qua toàn bộ smoke; không mở training.

Axe-core4.14.0 chạy5 trang ở375×812,768×1024,1440×1000:0 violation trong nhóm WCAG2A/AA và2.1AA đã chọn;0 tràn ngang. Đã sửa chữ tương phản thấp, nhãn input file và vùng bảng cuộn có thể focus. Đây là kiểm tự động và keyboard cơ bản, không là chứng nhận toàn bộ WCAG/screen reader. Chi tiết `outputs/web/browser_audit.json`.

Console ở phiên kiểm cuối không có error/warn. Các lỗi422/429 được chủ động kiểm trong API tests là hành vi mong đợi, không giả làm thành công.

## Giới hạn

Chỉ kiểm local trên macOS ARM64, CPU và một process server. Chưa kiểm cloud/auth/multi-tenant; không làm tăng metric AI hay gọi dữ liệu train-derived là benchmark độc lập. Kết quả model trên test giữ nguyên trong AUTONOMOUS_RESULTS.md.

Verdict: luồng demo local đạt; visual regression không có baseline để đối chiếu.

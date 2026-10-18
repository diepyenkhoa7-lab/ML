# Kế hoạch ứng dụng tích hợp — 17/10/2026

Trạng thái: đã triển khai và kiểm chứng local. Người dùng yêu cầu lập kế hoạch và thực hiện bằng ECC.

## Mục tiêu và giới hạn

Ứng dụng local Vue 3 + FastAPI: nhập CSV/XLSX/JSON, xem/ghép cột, chuẩn hóa,
Gemma đọc mô tả khi được bật, dự đoán lương từng dòng bằng pipeline đã lưu,
phân tích Matplotlib/Seaborn, tư vấn dựa trên số liệu, tải kết quả và biểu đồ.
Thiết kế workspace gọn: sidebar xanh đậm, nền sáng ấm, màu xanh lá cho thao tác,
bảng và biểu đồ là nội dung chính; sử dụng được trên desktop/mobile và bàn phím.

- Nạp Ridge/RF theo `configs/application.json`, xác minh checksum; chỉ predict,
  không fit lại. Hiện phục vụ v2_042e3aa1a886, giữ bd9af2fa002caae8 để rollback.
- Gemma mặc định 105728Z đã chọn bằng validation; không thay theo run mới nhất.
- Dữ liệu nhập giữ trong outputs/app_runtime (local, không đưa lên Git).
- Giới hạn demo local: 10 MiB/file, 2.000 dòng, 100 cột; Gemma tối đa 20 mô tả/lượt.
  Đây là giới hạn vận hành của bản demo, không phải yêu cầu từ giảng viên.
- Không mặc định đổi ngoại tệ/đoán kỳ lương; cột salary_monthly_vnd có nghĩa rõ ràng.
  Lương numeric ở cột chung cần người dùng chọn đơn vị/kỳ/hệ số.
- Feature cố định: experience_years, role, level, location, skills. Lương/mô tả không
  đi vào bộ hồi quy. Level chuẩn hóa bằng cùng quy tắc đã có, không suy năm từ seniority.
- Giữ nguyên train/validation/test và mọi model đã đánh giá. Không train trong ứng dụng.
- Biểu đồ ghi rõ thực tế/dự đoán; không có ngày đăng thì không gọi thống kê là xu hướng thời gian.
- Tư vấn dùng support thực từ train và chênh lệch dự đoán khi thêm kỹ năng; không suy nhân quả.
- Gemma đảm nhiệm trích xuất; giải thích/tư vấn được điền từ số liệu Python để kiểm tra được.
- Chạy trên 127.0.0.1; chưa phải triển khai đa người dùng/public hoặc nền tảng đăng nhập.

## Các bước

1. Dịch vụ dữ liệu/model: reader, mapping, chuẩn hóa, nạp pipeline, cảnh báo dữ liệu lạ.
2. Engine phân tích: dự đoán, lỗi từng dòng, metric trên bảng có nhãn, thống kê,
   biểu đồ, export CSV/XLSX/JSON/Markdown/ZIP cùng provenance và checksum.
3. API: upload/preview, job phân tích có tiến độ, đọc kết quả, download, hồ sơ/tư vấn.
4. Gemma worker suy luận riêng, dùng system prompt đã train, kiểm tra schema/context,
   báo lỗi thực và phát hiện GPU đang train. Không sửa output để làm đẹp metric.
5. Vue: nhập/ghép cột, tiến độ, dashboard/bảng, tư vấn, download, trạng thái lỗi/empty.
6. Kiểm chứng: integration test bằng model thật; reader 3 định dạng, unit/kỳ lương,
   input thiếu/sai/OOD, export an toàn công thức bảng tính, browser desktop/mobile,
   Gemma inference thực khi GPU rảnh; cập nhật runbook, commit/push nhánh source gọn.

## Tiêu chí nghiệm thu

| ID | Điều kiện và kết quả | Kiểm chứng |
|---|---|---|
| AC01 | Nhập 3 định dạng, xem trước, đổi ghép cột; file sai/oversize báo lỗi và không tạo job | API integration |
| AC02 | Mỗi dòng giữ source_row, kết quả hoặc lỗi; predict giống pipeline gốc, model/hash không đổi | Model parity + batch tests |
| AC03 | Lương thiếu vẫn predict; numeric thiếu đơn vị không thành nhãn; năm chia 12, USD không tự đổi VND | Fixtures biên |
| AC04 | 4 nhóm biểu đồ đề bài có PNG thật, có nguồn lương/số mẫu; thiếu nhãn/ngày không bịa metric/trend | API + kiểm tra ảnh |
| AC05 | CSV/XLSX/JSON/ZIP mở được, giữ dòng lỗi; các chuỗi công thức được escape khi xuất bảng tính | Export tests |
| AC06 | Gemma chạy suy luận khi bật, schema sai/context dài báo lỗi; không có lệnh train trong API | Worker tests + GPU smoke |
| AC07 | Browser upload → map → phân tích → đọc bảng/biểu đồ → xuất; hồ sơ → lương/tư vấn; mobile không tràn | ECC Chrome DevTools |

## Tài liệu kỹ thuật

- https://fastapi.tiangolo.com/tutorial/request-files/
- https://vuejs.org/guide/quick-start.html
- https://scikit-learn.org/stable/model_persistence.html

Model joblib chỉ nạp artifact tin cậy có checksum từ repo, không nhận model do người dùng upload.

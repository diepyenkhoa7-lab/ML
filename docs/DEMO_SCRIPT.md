# Kịch bản demo đề tài 4

Kịch bản khoảng 7–10 phút cho bản local hiện tại. Đây là hướng dẫn trình bày đã có
bằng chứng chạy ứng dụng, không xác nhận buổi báo cáo trước giảng viên đã diễn ra.

## Chuẩn bị trước buổi báo cáo

1. Mở app tại `http://127.0.0.1:8000/`. Nếu chưa chạy: `make app` từ thư mục dự án.
   Không chạy thêm server cùng cổng hoặc chạy train Gemma trong lúc demo.
2. Chuẩn bị `data/examples/application_gemma_long_demo.json` và
   `outputs/submission/datasets.zip` (tạo bằng `make submission-data`).
3. Mở nhánh GitHub `publish/salary-gemma-prep`, báo cáo kỹ thuật và bảng test metrics.
   Mac cần có base MLX và adapter `20261017T105728Z` để demo đọc mô tả.
   Bảng có cột cấu trúc vẫn dùng được khi GPU bận hoặc không có Gemma.

## 1. Giới thiệu bài toán — khoảng 1 phút

“Ứng dụng phân tích tin tuyển dụng CNTT và ước tính lương chào tuyển theo tháng.
Python làm sạch, tính thống kê và vẽ Matplotlib/Seaborn. Ridge và Random Forest
dự đoán lương; Gemma trích xuất trường từ mô tả để đưa vào pipeline.”

Nêu ba loại dữ liệu khác nhau: tin tuyển dụng dùng train; corpus Gemma có nhãn
silver; ITviec/TopDev là tham chiếu tổng hợp, không phải nhãn cá nhân để train.
Không gọi dữ liệu snapshot là thống kê đại diện cho toàn thị trường Việt Nam.

## 2. Phân tích bảng — khoảng 2 phút

1. Chọn **Nhập dữ liệu → Thử với 48 tin có sẵn** (48 dòng từ snapshot train).
2. Kiểm tra ghép cột vai trò, kinh nghiệm, kỹ năng và lương. Với bảng cấu trúc,
   không cần bật Gemma. Bấm **Phân tích**.
3. Tại Tổng quan, chọn nguồn **Lương cung cấp** để trình bày top nhu cầu công nghệ,
   lương theo công nghệ, tương quan kinh nghiệm–lương và so sánh vai trò/khu vực.
   Chỉ các kỹ năng đủ số mẫu mới có thống kê lương; đây là liên hệ quan sát.
4. Đổi sang nguồn **Lương dự đoán Ridge** để giải thích khác biệt giữa quan sát
   và kết quả model. Đọc một dòng ở bảng dự đoán và cảnh báo của dòng đó.
5. Mở **Chất lượng & sai số**. Nói rõ metric của bảng mẫu lấy từ train không phải
   bằng chứng kiểm định độc lập. Dùng bảng frozen test dưới đây để trình bày độ chính xác.
6. Bấm **Tải toàn bộ kết quả**: ZIP có bảng CSV/XLSX/JSON, báo cáo, PNG và manifest.

| Model, cùng 30 tin test | MAE (triệu VND/tháng) | RMSE (triệu VND/tháng) | R² |
|---|---:|---:|---:|
| Ridge v2 đang phục vụ | 4,433 | 5,664 | 0,540 |
| Random Forest v2 đối chiếu | 5,737 | 6,990 | 0,300 |

Nguồn: `outputs/metrics/salary_v2_042e3aa1a886/test_metrics.json`.
Target là trung điểm khoảng lương chào tuyển; chưa xác định gross/net. Sai số này
không phải sai số tối đa hay độ chắc chắn cho mỗi cá nhân.

## 3. Gemma đọc mô tả — khoảng 2 phút

1. Nhập `data/examples/application_gemma_long_demo.json` qua nút chọn file.
   Kiểm tra cột mô tả, bật **Gemma**, rồi bấm **Phân tích**.
2. Giải thích Gemma chỉ điền trường thiếu. Cột kỹ năng riêng được ưu tiên; nếu đọc
   từ mô tả, features kỹ năng có bằng chứng chữ trong nguồn. Raw Gemma được giữ riêng.
3. File gồm 3 dòng với 1 bản trùng: lần QA đã ra 3 dự đoán, 2 tin không trùng,
   không có nhãn lương độc lập, nên không có MAE mới. Các tin này là nguồn train
   phục vụ kiểm tra chức năng, không phải thử nghiệm chất lượng trên tin chưa thấy.
4. Tải ZIP và chỉ vị trí `gemma_outputs.json` cùng provenance model/adapter.
   Context web 2.048 token gồm phần dành cho output; không nhận mọi mô tả dài vô hạn.

Bằng chứng browser/GPU/export trước đó:
`outputs/metrics/gemma_corrected_v22/serving_qa/browser_upload_export.json`.
Nếu GPU bận, dùng **Kiểm tra lại GPU** sau khi lượt đang chạy kết thúc; có thể
demo bảng cấu trúc ở bước 2 trong lúc chờ, không gán kết quả cũ thành lượt Gemma mới.

## 4. Tư vấn nghề nghiệp — khoảng 2 phút

1. Chọn **Tư vấn nghề nghiệp**. Nhập Backend Developer, Junior, 3 năm, Hà Nội,
   `Python, SQL`. Bấm **Dự đoán & xem gợi ý**.
2. Trên model hiện tại: Ridge khoảng **26,5 triệu**, RF khoảng **23,9 triệu**.
   ITviec nhóm 3–4 năm hiển thị riêng **30,1 triệu**, là trung vị khảo sát, không
   phải lương thật của hồ sơ giả định này và không dùng để sửa dự đoán.
3. Chỉ vào gợi ý Rust/Docker/AWS/Golang và số mẫu cùng vai trò. Đây là thay đổi
   dự đoán khi thêm kỹ năng; không được diễn giải thành cam kết học xong tăng lương.
4. Thêm `Rust` vào ô kỹ năng: kết quả cũ phải biến mất. Bấm dự đoán lại: Ridge
   khoảng **33,6 triệu**, RF khoảng **26,1 triệu**, Rust không còn là gợi ý mới.
   Chênh lệch Ridge khớp khoảng +7,05 triệu của thẻ gợi ý trong sai số làm tròn.

Đã xác minh trên browser và API thật: tám vai trò phản hồi với hai dự đoán dương
cho bộ hồ sơ thử này; API từ chối Accountant bằng 422; khu vực/kỹ năng chưa có
trong train có cảnh báo. Bằng chứng và ảnh thật:
`outputs/app_verification/career_demo/`. Đây là kiểm chứng chức năng, không phải
đo MAE hay benchmark độ trễ trên người dùng thật.

## 5. Kết luận và bàn giao — khoảng 1 phút

- Mở GitHub, ZIP dữ liệu và báo cáo theo mẫu cá nhân khi đã hoàn thiện.
- Nêu giới hạn: nhãn silver, 1.078 weak train giả định kỳ tháng với trọng số 0,3;
  test salary chỉ 30 tin; độ lệch tham chiếu ITviec chưa tốt hơn mọi bản cũ.
- Hai lượt fine-tune Gemma từ 214 dòng đã hoàn tất nhưng không đạt guard nên
  giữ adapter cũ trên web. Cần kiểm chứng nhãn độc lập và validation nguồn mới
  trước vòng tiếp theo; giảm loss chưa chứng minh giảm sai số lương.

Báo cáo nội dung hiện có tại `reports/BAO_CAO_NOI_DUNG.md`; chưa phải bản cá nhân
đúng mẫu và chưa tự điền STT/họ tên/MSSV khi chưa được cung cấp.

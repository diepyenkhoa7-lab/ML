# Nghiệm thu ứng dụng local

Đã thực hiện kế hoạch tại docs/APP_IMPLEMENTATION_PLAN.md, AC01–AC07.

- 40 unit/integration tests: reader 3 định dạng, validation, model parity/hash,
  đơn vị lương, dòng lỗi/trùng, metric, PNG/CSV/XLSX/ZIP, hỗ trợ tư vấn và GPU guard.
- API smoke qua server thật: CSV/XLSX/JSON thiếu nhãn vẫn predict và không bịa metric;
  một phiếu tổng hợp được Gemma trích xuất thật rồi chuyển RF dự đoán. Không train.
- Browser ECC: upload bằng File API từ template app, ghép cột, tiến độ, 48 dự đoán,
  phân trang, chuyển nguồn lương biểu đồ, download và tư vấn. Chi tiết ở browser.json.
  Tool không có quyền chọn đường dẫn file OS của workspace; phần upload browser
  dùng File API, còn byte/file reader được kiểm tra trực tiếp qua API cả ba định dạng.
- Screenshot thật: dashboard-desktop.png, dashboard-mobile.png, advice-desktop.png.
  Mobile 390px không tràn ngang, cả ba mục điều hướng hiển thị đầy đủ.
- Tập mẫu là 48 tin từ train hoặc synthetic cho kiểm tra chức năng, không dùng làm
  đánh giá độc lập. Điểm test lịch sử vẫn giữ nguyên; chưa chứng minh mọi bảng nhập.
- Bản source tách riêng cũng đạt 40 tests, Ruff, strict JSONL/frozen CSV,
  npm ci offline sạch, Prettier và build Vue; xem source_export.json.
- App local một người dùng; chưa triển khai public, authentication hoặc load test.

Dữ liệu người dùng chỉ ở outputs/app_runtime, không có trong publication.
Lượt train Gemma người dùng tự chạy 115335Z và output inference thủ công giữ riêng.

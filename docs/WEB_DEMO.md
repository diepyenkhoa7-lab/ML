# CareerLens — demo web

Stack: Vue3 + JavaScript + Vite; Python3.11 + FastAPI. Dùng Qwen3-1.7B đã fine-tune trong `outputs/qwen_20261023T082631` và baseline TensorFlow hiện có. Không có endpoint train, không sửa trọng số hoặc tập dữ liệu đã chia.

## Chạy trên máy hiện tại

```sh
cd /Users/scara2906/Downloads/ML
make web
```

Mở http://127.0.0.1:8000. `make web` build Vue rồi chạy FastAPI một worker. Nếu web đã mở, dùng luôn phiên đó. Khi chạy foreground từ terminal, Ctrl+C dừng server.

## Chuẩn bị trên máy khác

```sh
python3.11 -m venv .venv-tf
.venv-tf/bin/python -m pip install -r requirements.txt -r requirements-web.txt
npm --prefix frontend ci
make web
```

Trên macOS ARM64, có thể cài đúng môi trường đã kiểm bằng `requirements-lock-web-macos-arm64.txt`. Frontend dùng Node24 đã kiểm và package-lock.json. Không coi lock macOS là lock CUDA/Linux.

Cần có backbone đúng `configs/qwen_source.json`, adapter/đầu hồi quy và baseline. Source gọn không chứa trọng số lớn. Gói bàn giao đã tạo trước đó nằm ở `outputs/delivery/qwen_salary_demo_20261025.zip`. Khôi phục model/metric về đúng chỗ:

```sh
.venv-tf/bin/python scripts/restore_web_models.py --archive PATH_TO_DELIVERY.zip
.venv-tf/bin/python scripts/download_qwen.py
```

Script khôi phục xác minh checksum gói và từng file; không ghi đè file khác nội dung. `--check-only` chỉ kiểm, không thay file. `scripts/download_qwen.py` chỉ tải backbone; adapter là phần đã train, không được thay bằng backbone chưa fine-tune. Trên máy hiện tại các trọng số đã đầy đủ.

## Luồng sử dụng

1. **Tổng quan:** chọn Việt Nam/quốc tế; xem thu nhập trung vị, kỹ năng và5 loại biểu đồ từ train. Không trộn USD/năm với VND/tháng. Địa điểm Việt Nam là chuỗi nguồn, chưa đồng nghĩa129 thành phố chuẩn hóa.
2. **Dữ liệu thị trường:** tìm kỹ năng, lọc vai trò/khu vực, chuyển trang, xuất toàn bộ kết quả đã lọc.
3. **Phân tích file:** tải CSV/JSON/XLSX, xem trước, ghép cột, xác nhận thị trường/khu vực mặc định, gửi phân tích. Vai trò/kinh nghiệm/kỹ năng thiếu có thể được Qwen trích từ cột mô tả. Không cắt file âm thầm.
4. **Tư vấn nghề nghiệp:** nhập hồ sơ hoặc dán tin tuyển dụng; xem dự đoán Qwen và baseline, kỹ năng có bằng chứng hoặc thông báo thiếu mẫu. Tối đa3 kỹ năng, support>=10; không hứa tăng lương.
5. **Đánh giá mô hình:** MAE/RMSE/R² test, JSON/schema/Skill F1, nhóm sai số cao và giới hạn dữ liệu. Model Việt Nam kém baseline được công bố nguyên kết quả.

Kết quả theo từng dòng có mức lương, đơn vị, model_version hoặc lỗi. Tải CSV/XLSX/JSON và mở/lưu PNG. Tác vụ chạy lần lượt, có tiến độ và lịch sử; đổi trang không dừng tác vụ. File và kết quả nằm ở `outputs/web/`, tách khỏi raw/splits.

File mẫu tải ngay trên giao diện. Schema chuẩn: market, role, location, experience_years, skills; description tùy chọn. market chỉ `vietnam`/`international`, kinh nghiệm0–80 năm, kỹ năng chuỗi phân cách dấu chấm phẩy hoặc mảng. Header phổ biến như DevType/WorkExp/Country được gợi ý ánh xạ, người dùng có thể sửa.

Lương nguồn chỉ đối chiếu khi có `salary` và `unit` đúng hoặc bạn xác nhận đơn vị; không đưa vào đặc trưng dự đoán. Đây là đối chiếu dữ liệu bạn cung cấp, không tự trở thành benchmark độc lập.

## Giới hạn phiên demo local

- File tối đa10MB/500 dòng; tư vấn tối đa20 hồ sơ/lần. Ba tác vụ chờ/đang chạy tối đa; đầy hàng đợi trả thông báo.
- Lần đầu cần nạp TensorFlow/backbone. Model được giữ trong bộ nhớ để các lần sau nhanh hơn. Chạy1 process server để tránh nhân bản model và tranh tài nguyên.
- Sau restart, tác vụ dở dang được đánh dấu gián đoạn, không tự chạy lại. Kết quả hoàn tất vẫn đọc được.
- Server bind127.0.0.1 và kiểm Origin/Host local; chưa có tài khoản/tenant/triển khai công khai. Không mở ra Internet như một dịch vụ production.
- Dự đoán là ước tính, nhãn trích xuất silver; khảo sát kỹ năng đã sử dụng khác nhu cầu tuyển dụng.

## Phát triển và kiểm tra

Backend: `.venv-tf/bin/python -m uvicorn career_web.app:app --host 127.0.0.1 --port 8000 --workers 1`.
Frontend ở terminal khác: `npm --prefix frontend run dev`, mở127.0.0.1:5173. Vite proxy `/api` về FastAPI; không cần CORS công khai.

```sh
.venv-tf/bin/python -m unittest discover -s tests -v
npm --prefix frontend run build
.venv-tf/bin/python scripts/check_web.py
```

Lệnh cuối cần server đang mở và model thật, tự tạo mẫu từ train, kiểm3 định dạng, trích xuất, export/PNG và checksum trọng số. Không train; không tính thành metric chất lượng AI. Bằng chứng dưới outputs/web; đánh giá model thật vẫn là kết quả valid/test đã chốt.

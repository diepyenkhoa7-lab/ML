# Phân tích thị trường việc làm CNTT Việt Nam

Ứng dụng mới viết bằng Python và Streamlit, chạy trực tiếp trên máy. Đợt hiện tại đã có nhập liệu, chuẩn hóa, kiểm tra chất lượng, EDA và preview hồ sơ CSV.

## Chạy ứng dụng

Từ thư mục repository:

```sh
cd job_market
python3.11 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
make check PYTHON=.venv/bin/python
make run PYTHON=.venv/bin/python
```

Mở http://127.0.0.1:8502. Có thể đổi cổng bằng `PORT=8503` khi gọi make run. Môi trường .venv riêng nằm trong job_market.

## Các màn hình

- Trang chính: top kỹ năng theo nguồn, nghề, địa điểm và Remote; bảng/biểu đồ cùng số mẫu, tải CSV/PNG.
- Nguồn dữ liệu và Tải nguồn: raw, xuất xứ, revision, giấy phép và checksum; tải lại đúng phiên bản.
- Vai trò, Địa điểm, Kỹ năng, Lương, Kinh nghiệm: đối chiếu raw–chuẩn, bằng chứng, trạng thái cần rà soát và CSV.
- Chất lượng: đối chiếu các partition, nhóm trùng/cùng trường quan sát và tải snapshot kèm manifest.
- Độ phủ thời gian: giữ riêng nguồn/tháng đăng, giải thích khi chưa đủ cơ sở kết luận xu hướng.
- Preview CSV: ghép cột hồ sơ, giữ thứ tự và lỗi từng dòng; UTF-8, tối đa 5 MiB/10.000 dòng.

## Dữ liệu mới

Hai nguồn được tải mới đúng revision, raw giữ nguyên tại datasets/raw. Metadata/attribution nằm trong datasets/provenance, datasets/README.md và src/career_market/sources.json.

| Nguồn | Phiên bản | Dòng thô | Khai báo giấy phép |
| --- | --- | ---: | --- |
| lucaznguyenofficial/vietnamese-job-posting-vietnamese-version | 2 | 2.056 | CC0 |
| baocgb/vietnam-it-jobs-raw-data-from-topcv-2026 | 1 | 1.550 | CC BY 4.0 |

Sau quy tắc nghề hiện tại: 322 tin EDA, 454 tin cần rà soát vai trò và 2.830 tin ngoài bảy nhóm nghề. Đây là phạm vi quan sát của dataset; các quy tắc bảo thủ có thể bỏ sót tin. TopCV thiếu JD nên kỹ năng chỉ có chứng cứ từ tiêu đề. Hai nguồn khác nền tảng và thời gian, chưa đủ cơ sở so sánh xu hướng nhiều năm.

HCM/HN giữ chung alias, Remote là hình thức làm việc riêng. Lương giữ khoảng/cận/tiền tệ/kỳ; chỉ có target khi đủ chứng cứ VND/tháng. Tin thiếu lương vẫn có thể dùng cho EDA. Hiện có **0 nhãn lương đủ điều kiện**; ML đang chờ gate #42. Chưa có model, metric, dự đoán hoặc tư vấn dựa trên model mới.

## Lệnh dữ liệu

Chạy từ job_market:

```sh
PYTHONPATH=src .venv/bin/python -m career_market sources
PYTHONPATH=src .venv/bin/python -m career_market preview jobs-2026 --limit 5
PYTHONPATH=src .venv/bin/python -m career_market download jobs-2026
PYTHONPATH=src .venv/bin/python -m career_market prepare --output datasets/processed
```

Snapshot gồm rows, eda, review, duplicates, salary_targets, nhóm cùng trường quan sát và manifest SHA-256. Tập target rỗng vẫn có schema. Thư mục processed và cache archives được sinh lại bằng lệnh, không thay raw.

CLI và Streamlit cùng gọi MarketService. Kiểm tra lint, nghiệp vụ và smoke UI/CLI bằng make check; bằng chứng từng lát cắt nằm trong docs/tdd. Workflow chỉ kiểm tra ứng dụng mới này.

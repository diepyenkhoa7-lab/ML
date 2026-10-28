# Nguồn tin tuyển dụng

Ứng dụng Python/Streamlit độc lập cho T01 (#15). Xem raw của hai nguồn Kaggle mới đã duyệt, kèm schema, số dòng và xuất xứ. Chạy trong thư mục `job_market`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
make check PYTHON=.venv/bin/python
make run PYTHON=.venv/bin/python
```

Với môi trường mới do main chuẩn bị, không cài editable:

```sh
make check PYTHON=/private/tmp/ml-market-env-20261029/bin/python
make run PYTHON=/private/tmp/ml-market-env-20261029/bin/python
PYTHONPATH=src /private/tmp/ml-market-env-20261029/bin/python -m career_market sources
PYTHONPATH=src /private/tmp/ml-market-env-20261029/bin/python -m career_market preview jobs-2026 --limit 5
```

`MarketService.sources()` trả danh mục nguồn. `MarketService.preview(source_id, limit=5)` kiểm toàn bộ file rồi trả `RawPreview`: `source`, `row_count`, `columns`, `raw_sha256`, `records`. Mỗi `RawRecord` giữ `source_id`, `job_id` (None nếu nguồn chỉ có URL), `job_url` và `raw` nguyên giá trị. `limit=None` hoặc giới hạn cao đọc mọi bản ghi; không chuẩn hóa URL/ID hay nội dung. Lỗi đầu vào dùng `MarketError`; CLI in stderr và exit 2, dashboard hiện thông báo.

`MarketService(raw_dir=Path(...))` cho phép chọn thư mục chứa file raw đã duyệt. Dashboard nhận đường dẫn tương tự qua `CAREER_MARKET_RAW_DIR`; file vẫn phải khớp schema, số dòng và SHA-256 trong catalog.

Raw nằm ở `datasets/raw`, metadata gốc ở `datasets/provenance`, catalog ở `src/career_market/sources.json`. File CSV được trích nguyên byte sau khi kiểm ZIP tải mới khớp SHA-256 trong `EDA_FIRST.md`. Không có downloader, bước chuẩn hóa, khử trùng hoặc ML trong T01. Hai nguồn chưa tạo thành chuỗi thời gian so sánh; kỳ lương chưa xác nhận, ML tiếp tục bị chặn.

GitHub Actions chỉ chạy lint/test của `job_market`; không chạy ứng dụng hoặc test cũ. Bằng chứng red–green: `docs/tdd/T01.md`.

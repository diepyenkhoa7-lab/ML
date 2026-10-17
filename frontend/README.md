# Giao diện Vue 3

Ứng dụng nhập bảng, ghép cột, theo dõi job, xem biểu đồ/dự đoán và tư vấn nghề nghiệp.
Build được phục vụ cùng FastAPI, không cần hai server khi demo.

```bash
make frontend-setup
make app
```

Phát triển riêng: `make api` và `npm --prefix frontend run dev` (proxy API sang 8000).
Kiểm tra: `npm --prefix frontend run build` và `npm --prefix frontend run format:check`.
Xem docs/APP_RUNBOOK.md; dữ liệu người dùng không lưu trong frontend hoặc Git.

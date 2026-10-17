"""API khởi tạo; các chức năng nghiệp vụ được triển khai sau khi có dữ liệu và model."""

from fastapi import FastAPI

app = FastAPI(title="IT Career Insight", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "stage": "environment", "models_loaded": False}

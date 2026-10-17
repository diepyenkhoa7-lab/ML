"""Local Vue + FastAPI application. Upload and inference never launch training."""

import fcntl
import json
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.schemas import (
    FIELDS,
    AnalysisRequest,
    JobState,
    Meta,
    Preview,
    Profile,
    ProfileResult,
)
from backend.app.services.data import MAX_BYTES, MAX_ROWS, ROOT, normalize_row
from backend.app.services.gemma import availability
from backend.app.services.salary import salary_service
from backend.app.services.store import AppStore


def create_app(runtime=None):
    store = AppStore(runtime)

    @asynccontextmanager
    async def lifespan(app):
        with (store.root / "app.lock").open("w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError(
                    "Thư mục dữ liệu đã có app đang chạy; chỉ dùng một worker"
                ) from exc
            store.recover()
            try:
                yield
            finally:
                store.pool.shutdown(wait=True)
                fcntl.flock(lock, fcntl.LOCK_UN)

    app = FastAPI(title="IT Career Insight", version="0.2.0", lifespan=lifespan)
    app.state.store = store
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).hostname not in {"127.0.0.1", "localhost"}:
            return JSONResponse({"detail": "Ứng dụng chỉ phục vụ thao tác local"}, status_code=403)
        if (
            request.headers.get("content-length", "").isdigit()
            and int(request.headers["content-length"]) > MAX_BYTES + 1024 * 1024
        ):
            return JSONResponse({"detail": "File vượt giới hạn 10 MiB"}, status_code=413)
        return await call_next(request)

    @app.exception_handler(FileNotFoundError)
    async def not_found(request, exc):
        return JSONResponse({"detail": "Không tìm thấy dữ liệu hoặc kết quả"}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.get("/health", response_model=dict)
    def health():
        return {
            "status": "ok",
            "stage": "application",
            "models_loaded": bool(salary_service().models),
        }

    @app.get("/api/meta", response_model=Meta)
    def meta():
        service = salary_service()
        return dict(
            salary_model=dict(
                experiment_id=service.manifest["experiment_id"],
                selected_model="random_forest",
                roles=service.roles,
                levels=sorted(service.levels),
                locations=sorted(service.locations),
                train_jobs=123,
                unit="VND/month",
                label_quality="silver",
                test_jobs=28,
                test_mae_vnd=6656370,
            ),
            gemma=availability(),
            fields=list(FIELDS),
            limits=dict(max_bytes=MAX_BYTES, max_rows=MAX_ROWS, gemma_rows=20),
        )

    @app.post("/api/datasets", response_model=Preview, status_code=201)
    async def upload(file: UploadFile):
        try:
            content = await file.read(MAX_BYTES + 1)
            if len(content) > MAX_BYTES:
                raise HTTPException(413, "File vượt giới hạn 10 MiB")
            return store.ingest(content, file.filename or "upload")
        finally:
            await file.close()

    @app.post("/api/datasets/demo", response_model=Preview, status_code=201)
    def demo():
        return store.demo()

    @app.get("/api/templates/{name}")
    def template(name: str):
        if name not in {"application_demo.csv", "application_demo.xlsx", "application_demo.json"}:
            raise HTTPException(404, "Không tìm thấy bảng mẫu")
        return FileResponse(ROOT / "data/examples" / name, filename=name)

    @app.post("/api/analyses", response_model=JobState, status_code=202)
    def submit(payload: AnalysisRequest):
        return store.submit(payload)

    @app.get("/api/analyses/{identifier}", response_model=JobState)
    def state(identifier: str):
        return store.state(identifier)

    @app.get("/api/analyses/{identifier}/rows", response_model=dict)
    def rows(
        identifier: str,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=25, ge=1, le=100),
    ):
        state = store.state(identifier)
        if state["status"] != "completed":
            raise HTTPException(409, "Phân tích chưa hoàn tất")
        values = json.loads((store.folder(identifier) / "results.json").read_text())
        return dict(total=len(values), offset=offset, rows=values[offset : offset + limit])

    @app.get("/api/analyses/{identifier}/artifacts/{name}")
    def artifact(identifier: str, name: str):
        state = store.state(identifier)
        if state["status"] != "completed" or name not in state["result"]["files"]:
            raise HTTPException(404, "Không tìm thấy file kết quả")
        media = "image/png" if name.endswith(".png") else None
        return FileResponse(
            store.folder(identifier) / name, media_type=media, filename=None if media else name
        )

    @app.post("/api/career/advice", response_model=ProfileResult)
    @app.post("/api/salary/predict", response_model=ProfileResult)
    def advise(profile: Profile):
        raw = profile.model_dump()
        options = AnalysisRequest(dataset_id="0" * 32)
        mapping = {k: k for k in ["role", "level", "experience_years", "location", "skills"]}
        row = normalize_row(raw, mapping, options)
        return salary_service().advise(row)

    # Serving the Vite build on the same origin avoids a second server for the demo.
    frontend = ROOT / "frontend/dist"
    if frontend.exists():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    else:

        @app.get("/", include_in_schema=False)
        def setup_notice():
            return JSONResponse(
                {
                    "detail": "Build frontend bằng npm ci và npm run build, rồi khởi động lại API",
                    "docs": "/docs",
                }
            )

    return app


app = create_app()

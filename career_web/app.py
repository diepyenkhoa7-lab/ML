"""FastAPI serves a Vue3 build and a single-worker, inference-only local API."""

import io
import logging
import zipfile
from contextlib import asynccontextmanager
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from career_ai.data import FEATURES, ROOT, UNITS

from . import repository
from .config import FRONTEND, MAX_BYTES, MAX_ROWS, MODEL_RUN
from .jobs import JobService
from .schemas import AnalysisRequest, Market, ProfileRequest
from .uploads import export_frame, mapped_rows, save_upload

logger = logging.getLogger(__name__)


def create_app(service=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.jobs = service or JobService()
        await run_in_threadpool(repository.ensure_charts)
        yield
        app.state.jobs.executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="CareerLens API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        origin = request.headers.get("origin")
        if (
            request.method not in ["GET", "HEAD", "OPTIONS"]
            and origin
            and origin
            not in [
                "http://127.0.0.1:8000",
                "http://localhost:8000",
                "http://127.0.0.1:5173",
                "http://localhost:5173",
            ]
        ):
            return JSONResponse(status_code=403, content={"detail": "Nguồn yêu cầu không hợp lệ."})
        length = request.headers.get("content-length", "0")
        if length.isdigit() and int(length) > MAX_BYTES + 1024 * 1024:
            return JSONResponse(status_code=413, content={"detail": "File vượt giới hạn10MB."})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.exception_handler(ValueError)
    async def invalid_data(request, exc):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(FileNotFoundError)
    async def missing_file(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(OverflowError)
    async def busy(request, exc):
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    @app.get("/api/health")
    def health(request: Request):
        return dict(
            status="ok",
            model_available=(MODEL_RUN / "qwen.lora.h5").exists(),
            model_loaded=request.app.state.jobs.model_loaded,
            max_rows=MAX_ROWS,
            model_version=f"llm:{MODEL_RUN.name}",
        )

    @app.get("/api/overview")
    def overview(market: Market = "vietnam"):
        return repository.overview(market)

    @app.get("/api/records")
    def records(
        market: Market = "vietnam",
        q: str = Query("", max_length=120),
        role: str = Query("", max_length=200),
        location: str = Query("", max_length=200),
        page: int = Query(1, ge=1),
        size: int = Query(15, ge=1, le=100),
    ):
        return repository.browse(market, q, role, location, page, size)[1]

    @app.get("/api/data/download")
    def download_data(
        market: Market = "vietnam",
        q: str = Query("", max_length=120),
        role: str = Query("", max_length=200),
        location: str = Query("", max_length=200),
    ):
        frame = repository.browse(market, q, role, location)[0]
        frame = frame[FEATURES + ["salary", "source_dataset"]].assign(unit=UNITS[market])
        return StreamingResponse(
            iter(["\ufeff" + export_frame(frame).to_csv(index=False)]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{market}_train.csv"'},
        )

    @app.get("/api/metrics")
    def metrics():
        return repository.model_metrics()

    @app.get("/api/charts/data/{market}/{kind}")
    def data_chart(market: Market, kind: str):
        if kind not in repository.CHARTS:
            raise HTTPException(404, "Không tìm thấy biểu đồ.")
        path = ROOT / "outputs/eda" / f"{market}_{kind}.png"
        if not path.exists():
            raise HTTPException(404, "Biểu đồ chưa sẵn sàng.")
        return FileResponse(path, media_type="image/png")

    @app.post("/api/uploads", status_code=201)
    async def upload(file: UploadFile):
        content = await file.read(MAX_BYTES + 1)
        await file.close()
        if len(content) > MAX_BYTES:
            raise HTTPException(413, "File vượt giới hạn10MB.")
        try:
            return await run_in_threadpool(save_upload, content, file.filename)
        except (pd.errors.ParserError, UnicodeError, OSError, zipfile.BadZipFile) as exc:
            raise HTTPException(422, "Không đọc được file. Kiểm tra định dạng/UTF-8.") from exc

    @app.post("/api/analyses", status_code=202)
    def analyze(body: AnalysisRequest, request: Request):
        filename, rows = mapped_rows(body)
        return request.app.state.jobs.submit(rows, filename, body.include_advice)

    @app.post("/api/profiles", status_code=202)
    def profile(body: ProfileRequest, request: Request):
        row = body.model_dump(exclude={"include_advice"})
        return request.app.state.jobs.submit([row], "Hồ sơ nghề nghiệp", body.include_advice)

    @app.get("/api/jobs")
    def jobs(request: Request):
        return request.app.state.jobs.list()

    @app.get("/api/jobs/{identifier}")
    def job(identifier: str, request: Request):
        return request.app.state.jobs.get(identifier)

    @app.get("/api/jobs/{identifier}/results")
    def job_results(identifier: str, request: Request):
        status = request.app.state.jobs.get(identifier)
        if status["status"] != "completed":
            raise HTTPException(409, "Tác vụ chưa hoàn tất.")
        return repository.read_json(request.app.state.jobs.folder / identifier / "results.json")

    @app.get("/api/jobs/{identifier}/download/{format}")
    def job_download(identifier: str, format: Literal["csv", "xlsx", "json"], request: Request):
        status = request.app.state.jobs.get(identifier)
        if status["status"] != "completed":
            raise HTTPException(409, "Tác vụ chưa hoàn tất.")
        path = request.app.state.jobs.folder / identifier / f"predictions.{format}"
        return FileResponse(path, filename=f"career_lens_{identifier[:8]}.{format}")

    @app.get("/api/jobs/{identifier}/charts/{market}/{kind}")
    def job_chart(identifier: str, market: Market, kind: str, request: Request):
        request.app.state.jobs.get(identifier)
        if kind not in repository.CHARTS:
            raise HTTPException(404, "Không tìm thấy biểu đồ.")
        path = request.app.state.jobs.folder / identifier / "figures" / f"{market}_{kind}.png"
        if not path.exists():
            raise HTTPException(404, "Không có dữ liệu hợp lệ để vẽ biểu đồ.")
        return FileResponse(path, media_type="image/png", filename=path.name)

    @app.get("/api/examples/{format}")
    def example(format: Literal["csv", "json", "xlsx"]):
        frame = repository.training_data().groupby("market").head(1)[FEATURES]
        if format == "json":
            return JSONResponse(
                repository.records(frame),
                headers={"Content-Disposition": 'attachment; filename="profiles_example.json"'},
            )
        content = io.BytesIO()
        if format == "xlsx":
            frame.to_excel(content, index=False)
        else:
            content.write(("\ufeff" + frame.to_csv(index=False)).encode("utf-8"))
        content.seek(0)
        return StreamingResponse(
            content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="profiles_example.{format}"'},
        )

    if (FRONTEND / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon():
        return FileResponse(FRONTEND / "favicon.svg", media_type="image/svg+xml")

    @app.get("/", include_in_schema=False)
    def index():
        if not (FRONTEND / "index.html").exists():
            raise HTTPException(503, "Frontend chưa build. Chạy npm run build trong frontend/.")
        return FileResponse(FRONTEND / "index.html", headers={"Cache-Control": "no-cache"})

    return app


app = create_app()

"""Local bounded datasets and atomic job states. User content never enters source publication."""

import hashlib
import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import BoundedSemaphore

from backend.app.schemas import JobState
from backend.app.services.analysis import analyze, write_json
from backend.app.services.contracts import digest, strict_json
from backend.app.services.data import ROOT, read_table, suggest_mapping, text


class JobBusyError(Exception):
    pass


class AppStore:
    def __init__(self, root=None):
        self.root = Path(root or ROOT / "outputs/app_runtime")
        self.root.mkdir(parents=True, exist_ok=True)
        self.slots = BoundedSemaphore(2)  # One running job and at most one waiting.
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="career-analysis")

    def recover(self):
        # Isolate one corrupt record without preventing healthy jobs from reopening.
        for path in self.root.glob("*/state.json"):
            try:
                value = self.read_state(path)
            except (ValueError, TypeError, KeyError):
                if not re.fullmatch(r"[a-f0-9]{32}", path.parent.name):
                    logging.getLogger(__name__).warning("Invalid job folder: %s", path.parent)
                    continue
                path.rename(path.with_name(f"state.corrupt.{uuid.uuid4().hex}.json"))
                value = JobState(
                    id=path.parent.name,
                    status="failed",
                    stage="Dữ liệu trạng thái bị hỏng",
                    error="Đã giữ bản lỗi để kiểm tra; hãy tạo lượt phân tích mới",
                ).model_dump()
            if value["status"] in {"running", "queued"}:
                value.update(
                    status="failed", error="Máy chủ đã khởi động lại; hãy tạo lượt phân tích mới"
                )
            write_json(path, value)

    @staticmethod
    def read_state(path):
        value = JobState.model_validate(strict_json(path.read_text())).model_dump()
        if value["id"] != path.parent.name:
            raise ValueError("Trạng thái không khớp mã job")
        return value

    def folder(self, identifier):
        if not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise FileNotFoundError("Không tìm thấy dữ liệu/job")
        path = self.root / identifier
        if not path.is_dir():
            raise FileNotFoundError("Không tìm thấy dữ liệu/job")
        return path

    def ingest(self, content, filename, provenance="File do người dùng nhập"):
        rows = read_table(content, filename)
        return self.save_dataset(rows, filename, hashlib.sha256(content).hexdigest(), provenance)

    def save_dataset(self, rows, filename, sha, provenance):
        identifier = uuid.uuid4().hex
        folder = self.root / identifier
        folder.mkdir()
        dataset = dict(
            dataset_id=identifier,
            filename=Path(filename).name,
            rows=rows,
            columns=list(rows[0]),
            input_sha256=sha,
            provenance=provenance,
        )
        dataset["schema_version"] = "career.dataset.v1"
        dataset["snapshot_sha256"] = digest(dataset)
        write_json(folder / "dataset.json", dataset)
        return dict(
            dataset_id=identifier,
            filename=dataset["filename"],
            row_count=len(rows),
            columns=dataset["columns"],
            preview=[
                {
                    k: (v[:500] + "…" if isinstance(v, str) and len(v) > 500 else v)
                    for k, v in row.items()
                }
                for row in rows[:6]
            ],
            suggested_mapping=suggest_mapping(dataset["columns"]),
            provenance=provenance,
        )

    def demo(self):
        from backend.app.services.salary import salary_service

        service = salary_service()
        frame = service.train.head(48)[
            [
                "record_id",
                "role",
                "level",
                "experience_years",
                "location",
                "skills",
                "salary_monthly_vnd",
            ]
        ]
        content = frame.to_csv(index=False).encode()
        return self.ingest(
            content,
            f"vn_developer_demo_{len(frame)}.csv",
            f"{len(frame)} tin từ snapshot train model {service.experiment}, "
            "nhãn silver; minh họa, không phải holdout độc lập",
        )

    def load_dataset(self, identifier):
        value = strict_json((self.folder(identifier) / "dataset.json").read_text())
        recorded = value.get("snapshot_sha256")
        unsigned = {k: v for k, v in value.items() if k != "snapshot_sha256"}
        if (
            value.get("schema_version") != "career.dataset.v1"
            or recorded != digest(unsigned)
            or value.get("dataset_id") != identifier
        ):
            raise ValueError(
                "Dữ liệu lưu không còn được kiểm chứng hoặc thuộc phiên bản cũ; nhập lại file"
            )
        return value

    def submit(self, options):
        if not self.slots.acquire(blocking=False):
            raise JobBusyError("Đã có 2 lượt đang xử lý/chờ; đợi hoàn tất rồi thử lại")
        try:
            dataset = self.load_dataset(options.dataset_id)
            if set(options.mapping.values()) - set(dataset["columns"]):
                raise ValueError("Ghép cột không tồn tại trong bảng")
            has_identity = any(k in options.mapping for k in ["role", "title"])
            if not has_identity and not (options.use_gemma and "description" in options.mapping):
                raise ValueError("Cần cột vai trò/chức danh hoặc bật Gemma với cột mô tả")
            if options.use_gemma:
                column = options.mapping.get("description")
                if not column:
                    raise ValueError("Cần ghép cột mô tả khi bật Gemma")
                count = sum(bool(text(row.get(column))) for row in dataset["rows"])
                if count > 20:
                    raise ValueError("Mỗi lượt Gemma tối đa 20 mô tả")
            identifier = uuid.uuid4().hex
            folder = self.root / identifier
            folder.mkdir()
            state = JobState(id=identifier, status="queued", stage="Đang xếp lịch").model_dump()
            write_json(folder / "state.json", state)
            self.pool.submit(self._execute, folder, state.copy(), dataset, options)
            return state
        except BaseException:
            self.slots.release()
            raise

    def _execute(self, folder, state, dataset, options):
        def progress(stage, percent):
            state.update(status="running", stage=stage, progress=percent)
            write_json(folder / "state.json", state)

        try:
            report = analyze(dataset, options, folder, progress)
            state.update(status="completed", stage="Hoàn tất", progress=100, result=report)
        except Exception as exc:
            # Persist failure, never fabricate partial results or leave an endless spinner.
            state.update(status="failed", stage="Không hoàn tất", error=str(exc))
        try:
            write_json(folder / "state.json", state)
        finally:
            self.slots.release()

    def state(self, identifier):
        path = self.folder(identifier) / "state.json"
        if not path.exists():
            raise FileNotFoundError("Không tìm thấy job")
        return self.read_state(path)

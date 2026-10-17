"""Local bounded datasets and atomic job states. User content never enters source publication."""

import hashlib
import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.app.schemas import JobState
from backend.app.services.analysis import analyze, write_json
from backend.app.services.data import ROOT, read_table, suggest_mapping


class AppStore:
    def __init__(self, root=None):
        self.root = Path(root or ROOT / "outputs/app_runtime")
        self.root.mkdir(parents=True, exist_ok=True)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="career-analysis")

    def recover(self):
        # A process restart cannot silently leave a job running forever.
        for state in self.root.glob("*/state.json"):
            value = json.loads(state.read_text())
            if value["status"] in {"running", "queued"}:
                value.update(
                    status="failed", error="Máy chủ đã khởi động lại; hãy tạo lượt phân tích mới"
                )
                write_json(state, value)

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
        import pandas as pd

        path = ROOT / "data/splits/v1.0.1/vn_developer/train.csv"
        frame = pd.read_csv(path).head(48)[
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
            "vn_developer_demo_48.csv",
            "48 tin thật từ train v1.0.1, nhãn silver; minh họa, không phải holdout độc lập",
        )

    def submit(self, options):
        dataset = json.loads((self.folder(options.dataset_id) / "dataset.json").read_text())
        if set(options.mapping.values()) - set(dataset["columns"]):
            raise ValueError("Ghép cột không tồn tại trong bảng")
        if not any(k in options.mapping for k in ["role", "title", "description"]):
            raise ValueError("Cần chọn cột vai trò, chức danh hoặc mô tả")
        identifier = uuid.uuid4().hex
        folder = self.root / identifier
        folder.mkdir()
        state = JobState(id=identifier, status="queued", stage="Đang xếp lịch").model_dump()
        write_json(folder / "state.json", state)
        self.pool.submit(self._execute, folder, state, dataset, options)
        return state

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
        write_json(folder / "state.json", state)

    def state(self, identifier):
        path = self.folder(identifier) / "state.json"
        if not path.exists():
            raise FileNotFoundError("Không tìm thấy job")
        return json.loads(path.read_text())

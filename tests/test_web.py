"""API/queue contracts. Fixture predictions do not measure AI quality."""

import io
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from career_ai.data import FEATURES
from career_web.app import create_app
from career_web.jobs import JobService
from career_web.schemas import AnalysisRequest
from career_web.uploads import export_frame, mapped_rows, save_upload


def fixture_processor(row, advice):
    if not row.get("role"):
        raise ValueError("Missing role")
    return dict(
        **{k: row[k] for k in FEATURES},
        prediction=100.0,
        baseline_prediction=90.0,
        unit="VND/month",
        model_version="contract-fixture",
    )


class WebContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = JobService(self.root / "jobs", fixture_processor)
        self.patch = patch("career_web.uploads.WEB_OUTPUT", self.root)
        self.patch.start()
        self.client = TestClient(create_app(self.service), base_url="http://127.0.0.1")
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.service.executor.shutdown(wait=True)
        self.patch.stop()
        self.tmp.cleanup()

    def test_browse_metrics_and_literal_search(self):
        summary = self.client.get("/api/overview?market=vietnam")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()["samples"], 155)
        self.assertEqual(summary.json()["unit"], "VND/month")
        self.assertEqual(self.client.get("/api/records?market=vietnam&size=2").json()["size"], 2)
        self.assertEqual(self.client.get("/api/records?q=%5B%5D").status_code, 200)
        self.assertEqual(
            self.client.get("/api/metrics").json()["model_version"], "llm:qwen_20261023T082631"
        )
        self.assertEqual(self.client.get("/api/overview?market=wrong").status_code, 422)

    def test_file_validation_and_local_origin(self):
        for name, body in [
            ("x.txt", b"hello"),
            ("x.xlsx", b"not a zip"),
            ("x.json", b"{}"),
            ("x.json", b"[]"),
        ]:
            response = self.client.post("/api/uploads", files={"file": (name, body)})
            self.assertEqual(response.status_code, 422)
        response = self.client.post(
            "/api/profiles", json={}, headers={"Origin": "https://evil.test"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/api/jobs/not-an-id").status_code, 404)
        self.assertEqual(self.client.get("/api/charts/data/vietnam/not-a-chart").status_code, 404)

    def test_real_upload_readers_and_queued_row_errors(self):
        rows = [
            dict(
                market="vietnam",
                role="Backend Developer",
                location="Hà Nội",
                experience_years=3,
                skills="python;sql",
            ),
            dict(
                market="vietnam", role=None, location="Hà Nội", experience_years=3, skills="python"
            ),
        ]
        frame = pd.DataFrame(rows)
        excel = io.BytesIO()
        frame.to_excel(excel, index=False)
        for extension, data in [
            ("json", json.dumps(rows).encode()),
            ("csv", frame.to_csv(index=False).encode()),
            ("xlsx", excel.getvalue()),
        ]:
            response = self.client.post("/api/uploads", files={"file": (f"rows.{extension}", data)})
            self.assertEqual(response.status_code, 201, response.text)
            upload = response.json()
            response = self.client.post(
                "/api/analyses",
                json=dict(
                    upload_id=upload["id"],
                    mapping=upload["mapping"],
                    market="vietnam",
                    include_advice=False,
                ),
            )
            self.assertEqual(response.status_code, 202, response.text)
            identifier = response.json()["id"]
            for _ in range(100):
                status = self.client.get(f"/api/jobs/{identifier}").json()
                if status["status"] not in ["running", "queued"]:
                    break
                time.sleep(0.05)
            self.assertEqual(status["status"], "completed", status)
            self.assertEqual((status["valid"], status["errors"]), (1, 1))
            result = self.client.get(f"/api/jobs/{identifier}/results").json()
            self.assertEqual(result["rows"][0]["model_version"], "contract-fixture")
            for format in ["json", "csv", "xlsx"]:
                self.assertEqual(
                    self.client.get(f"/api/jobs/{identifier}/download/{format}").status_code, 200
                )

    def test_column_mapping_and_spreadsheet_literals(self):
        upload = save_upload(
            b"job_title,WorkExp,Country,skills\nDev,2,Germany,python\n",
            "a.csv",
            self.root / "uploads",
        )
        request = AnalysisRequest(
            upload_id=upload["id"], mapping=upload["mapping"], market="international"
        )
        _, rows = mapped_rows(request, self.root / "uploads")
        self.assertEqual(rows[0]["role"], "Dev")
        self.assertNotIn("salary", rows[0])
        safe = export_frame(pd.DataFrame([dict(role="=1+1", salary=-1)]))
        self.assertEqual(safe.role.iloc[0], "'=1+1")
        self.assertEqual(safe.salary.iloc[0], -1)

    def test_restart_marks_orphaned_jobs(self):
        from career_auto.state import write

        path = self.root / "other/abc/status.json"
        write(path, dict(status="running", created_at="now"))
        service = JobService(self.root / "other", fixture_processor)
        self.assertEqual(json.loads(path.read_text())["status"], "interrupted")
        service.executor.shutdown(wait=True)

    def test_upload_and_advice_limits_do_not_silently_truncate(self):
        body = b"role,experience_years,skills\n" + b"Dev,1,python\n" * 501
        response = self.client.post("/api/uploads", files={"file": ("too_many.csv", body)})
        self.assertEqual(response.status_code, 422)
        self.assertIn("501", response.json()["detail"])
        with self.assertRaises(ValueError):
            self.service.submit([{}] * 21, "advice", include_advice=True)

    def test_queue_has_backpressure_and_no_duplicate_worker(self):
        release = threading.Event()

        def blocked(row, advice):
            release.wait(5)
            raise ValueError("contract invalid row")

        self.service.processor = blocked
        try:
            for _ in range(3):
                response = self.client.post(
                    "/api/profiles",
                    json={"market": "vietnam", "location": "Hà Nội", "include_advice": False},
                )
                self.assertEqual(response.status_code, 202)
            response = self.client.post(
                "/api/profiles",
                json={"market": "vietnam", "location": "Hà Nội", "include_advice": False},
            )
            self.assertEqual(response.status_code, 429)
        finally:
            release.set()

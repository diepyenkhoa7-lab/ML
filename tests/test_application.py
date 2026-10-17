"""Application acceptance checks against actual persisted salary pipelines."""

import hashlib
import io
import json
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch

import joblib
import pandas as pd
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from backend.app.main import create_app
from backend.app.schemas import AnalysisRequest
from backend.app.services.data import ROOT, normalize_row, read_table, skills_from, suggest_mapping
from backend.app.services.salary import SalaryService


class GemmaGuardTests(unittest.TestCase):
    def test_active_training_prevents_worker_launch(self):
        from backend.app.services.gemma import extract_cards

        with (
            patch(
                "backend.app.services.gemma.availability",
                return_value={
                    "available": True,
                    "training_active": True,
                    "training_check_error": False,
                },
            ),
            patch("backend.app.services.gemma.subprocess.run") as launch,
        ):
            with self.assertRaisesRegex(ValueError, "đang train"):
                extract_cards(["sample"])
            launch.assert_not_called()

    def test_unknown_gpu_state_is_not_reported_idle(self):
        from backend.app.services.gemma import availability

        with patch("backend.app.services.gemma.subprocess.run", side_effect=OSError):
            state = availability()
        self.assertTrue(state["training_check_error"])
        self.assertTrue(state["training_active"])


class ImportContractTests(unittest.TestCase):
    def test_csv_xlsx_json_keep_same_values_and_column_mapping(self):
        frame = pd.DataFrame(
            [dict(role="Backend Developer", experience_years=2, skills="Python;SQL")]
        )
        buffer = io.BytesIO()
        frame.to_excel(buffer, index=False)
        versions = [
            (frame.to_csv(index=False).encode(), "jobs.csv"),
            (buffer.getvalue(), "jobs.xlsx"),
            (frame.to_json(orient="records").encode(), "jobs.json"),
        ]
        for content, filename in versions:
            with self.subTest(filename=filename):
                rows = read_table(content, filename)
                self.assertEqual(rows[0]["experience_years"], 2)
                self.assertEqual(suggest_mapping(list(rows[0]))["role"], "role")

    def test_reject_model_nested_json_duplicate_columns_and_large_table(self):
        for content, name in [
            (b"not a model", "model.pkl"),
            (b'[{"x":{"a":1}}]', "jobs.json"),
            (b"a,a\n1,2\n", "jobs.csv"),
            (b"x\n" + b"1\n" * 2001, "jobs.csv"),
        ]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                read_table(content, name)
        with self.assertRaises(ValueError):
            skills_from([1, 2])

    def test_native_salary_requires_explicit_currency_and_period(self):
        raw = dict(role="Backend Developer", skills="Python, SQL", salary=240000000)
        mapping = {key: key for key in raw}
        missing = normalize_row(raw, mapping, AnalysisRequest(dataset_id="0" * 32))
        self.assertIsNone(missing["salary_monthly_vnd"])
        known = normalize_row(
            raw, mapping, AnalysisRequest(dataset_id="0" * 32, currency="VND", period="year")
        )
        self.assertEqual(known["salary_monthly_vnd"], 20e6)
        usd = normalize_row(
            raw, mapping, AnalysisRequest(dataset_id="0" * 32, currency="USD", period="year")
        )
        self.assertIsNone(usd["salary_monthly_vnd"])
        mixed = normalize_row(
            dict(raw, salary="20 triệu VND hoặc 1000 USD/tháng"),
            mapping,
            AnalysisRequest(dataset_id="0" * 32, currency="VND", period="month"),
        )
        self.assertIsNone(mixed["salary_monthly_vnd"])

    def test_prediction_matches_original_pipeline_with_no_model_mutation(self):
        folder = ROOT / "models/salary/bd9af2fa002caae8"
        before = hashlib.sha256((folder / "best_model.joblib").read_bytes()).hexdigest()
        source = pd.read_csv(ROOT / "data/splits/v1.0.1/vn_developer/train.csv").head(12)
        rows = [
            dict(
                role=r.role,
                level=r.level,
                location=r.location,
                experience_years=r.experience_years,
                skills=r.skills.split(";"),
            )
            for r in source.itertuples()
        ]
        actual = SalaryService().predict(rows)["random_forest"]
        expected = joblib.load(folder / "best_model.joblib").predict(
            source[["experience_years", "role", "level", "location", "skills"]]
        )
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=6)
        self.assertEqual(
            before, hashlib.sha256((folder / "best_model.joblib").read_bytes()).hexdigest()
        )


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app(self.directory.name)
        self.client = TestClient(self.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.directory.cleanup()

    def run_job(self, frame, **options):
        response = self.client.post(
            "/api/datasets",
            files={"file": ("jobs.csv", frame.to_csv(index=False).encode(), "text/csv")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        preview = response.json()
        started = self.client.post(
            "/api/analyses",
            json=dict(
                dataset_id=preview["dataset_id"], mapping=preview["suggested_mapping"], **options
            ),
        )
        self.assertEqual(started.status_code, 202, started.text)
        identifier = started.json()["id"]
        for _ in range(300):
            state = self.client.get("/api/analyses/" + identifier).json()
            if state["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
        self.assertEqual(state["status"], "completed", state)
        return identifier, state["result"]

    def test_batch_charts_errors_duplicate_exports_and_formula_safety(self):
        first = dict(
            role="Backend Developer",
            level="Junior",
            experience_years=2,
            location="Hà Nội",
            skills="Python;SQL",
            salary_monthly_vnd=20e6,
            posted_date="2026-10-01",
            note="=1+1",
        )
        frame = pd.DataFrame(
            [
                first,
                first,
                dict(first, experience_years=3, salary_monthly_vnd=25e6),
                dict(
                    first,
                    role="Frontend Developer",
                    skills="JavaScript;React",
                    salary_monthly_vnd=22e6,
                ),
                dict(first, role="Data Analyst"),
                dict(first, experience_years=-1),
            ]
        )
        identifier, result = self.run_job(frame)
        self.assertEqual(result["summary"]["predicted"], 4)
        self.assertEqual(result["summary"]["invalid"], 2)
        self.assertEqual(result["summary"]["duplicates"], 1)
        self.assertEqual(result["metrics"]["random_forest"]["samples"], 3)
        self.assertIn("posting_trend", [c["id"] for c in result["charts"]])
        endpoint = f"/api/analyses/{identifier}/artifacts/"
        image = self.client.get(endpoint + result["charts"][0]["file"])
        self.assertTrue(image.content.startswith(b"\x89PNG"))
        archive = zipfile.ZipFile(io.BytesIO(self.client.get(endpoint + "analysis.zip").content))
        self.assertIsNone(archive.testzip())
        manifest = json.loads(archive.read("manifest.json"))
        for name, sha in manifest["files"].items():
            self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), sha)
        csv_rows = pd.read_csv(io.BytesIO(archive.read("results.csv")))
        self.assertEqual(len(csv_rows), 6)
        self.assertEqual(csv_rows.iloc[0]["input_note"], "'=1+1")
        workbook = load_workbook(io.BytesIO(archive.read("results.xlsx")))
        for cell in workbook.active[2]:
            self.assertNotEqual(cell.data_type, "f")
        values = self.client.get(f"/api/analyses/{identifier}/rows?offset=0&limit=100").json()[
            "rows"
        ]
        self.assertEqual(values[1]["duplicate_of"], 1)
        self.assertEqual(values[4]["status"], "invalid")
        self.assertEqual(self.client.get(endpoint + "dataset.json").status_code, 404)

    def test_no_salary_no_date_does_not_fabricate_metrics_or_trend(self):
        frame = pd.DataFrame(
            [dict(role="Backend Developer", level="Junior", skills="Python", experience_years=2)]
        )
        _, result = self.run_job(frame)
        self.assertEqual(result["metrics"], {})
        self.assertEqual(result["summary"]["labeled"], 0)
        self.assertNotIn("posting_trend", [c["id"] for c in result["charts"]])
        self.assertFalse(any(c["id"].endswith("_observed") for c in result["charts"]))

    def test_profile_advice_is_computed_and_supported(self):
        result = self.client.post(
            "/api/career/advice",
            json=dict(
                role="Backend Developer",
                level="Junior",
                experience_years=3,
                location="Hà Nội",
                skills=["Python", "SQL"],
            ),
        )
        self.assertEqual(result.status_code, 200, result.text)
        value = result.json()
        self.assertGreater(value["predictions"]["random_forest"], 0)
        self.assertTrue(
            all(
                r["train_support"] >= 5
                and r["role_support"] >= 5
                and r["skill"] not in {"python", "sql"}
                for r in value["recommendations"]
            )
        )
        self.assertEqual(
            self.client.post("/api/career/advice", json=dict(role="Accountant")).status_code, 422
        )

    def test_ridge_selected_in_api_exports_and_per_model_metrics(self):
        profile = dict(
            role="Backend Developer",
            level="Employee",
            location="Hà Nội",
            skills=["Python"],
            experience_years=3,
        )
        response = self.client.post("/api/career/advice", json=profile).json()
        self.assertEqual(response["selected_model"], "ridge")
        frame = pd.DataFrame([dict(profile, skills="Python", salary_monthly_vnd=20e6)])
        identifier, result = self.run_job(frame)
        row = self.client.get(f"/api/analyses/{identifier}/rows").json()["rows"][0]
        self.assertEqual(row["predicted_salary_vnd"], row["ridge_salary_vnd"])
        self.assertEqual(row["comparison_salary_vnd"], row["random_forest_salary_vnd"])
        self.assertEqual(row["error_vnd"], row["ridge_salary_vnd"] - 20e6)
        self.assertEqual(
            result["metrics"]["random_forest"]["mae_vnd"],
            abs(row["random_forest_salary_vnd"] - 20e6),
        )
        self.assertEqual(result["model"]["experiment_id"], "v2_042e3aa1a886")
        self.assertEqual(result["model"]["historical_test"]["samples"], 30)

    def test_queue_returns_429_and_retry_hint(self):
        store = self.app.state.store
        self.assertTrue(store.slots.acquire(blocking=False))
        self.assertTrue(store.slots.acquire(blocking=False))
        try:
            response = self.client.post("/api/analyses", json={"dataset_id": "0" * 32})
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["retry-after"], "5")
        finally:
            store.slots.release()
            store.slots.release()

    def test_requested_gemma_without_nonempty_description_records_not_used(self):
        frame = pd.DataFrame([dict(role="Backend Developer", description="", skills="Python")])
        with patch("backend.app.services.analysis.extract_cards") as extract:
            identifier, result = self.run_job(frame, use_gemma=True)
        extract.assert_not_called()
        self.assertTrue(result["gemma_execution"]["requested"])
        self.assertFalse(result["gemma_execution"]["used"])
        manifest = self.client.get(f"/api/analyses/{identifier}/artifacts/manifest.json").json()
        self.assertIsNone(manifest["adapter"])
        self.assertIn("train_snapshot_sha256", manifest["salary_provenance"])
        self.assertEqual(len(manifest["dataset_snapshot_sha256"]), 64)

    def test_input_validation_and_local_origin(self):
        self.assertEqual(
            self.client.post("/api/datasets", files={"file": ("x.pkl", b"fake")}).status_code, 422
        )
        self.assertEqual(
            self.client.post(
                "/api/datasets/demo", headers={"Origin": "https://outside.example"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/datasets/demo", headers={"Origin": "http://[invalid"}
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get("/api/analyses/not-a-uuid").status_code, 404)
        self.assertEqual(self.client.get("/api/analyses/" + "0" * 32).status_code, 404)
        self.assertEqual(
            self.client.post("/api/analyses", json={"dataset_id": "../../"}).status_code, 422
        )


if __name__ == "__main__":
    unittest.main()

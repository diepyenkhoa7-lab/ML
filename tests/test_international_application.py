"""International serving acceptance: frozen models, units, grouped splits and exports."""

import hashlib
import io
import json
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas import AnalysisRequest
from backend.app.services.data import ROOT, normalize_row
from backend.app.services.international import international_service
from backend.app.services.international_analysis import analyze_international
from backend.app.services.research import chart_path, overview


class InternationalContractTests(unittest.TestCase):
    def test_profile_parity_recommendations_and_no_market_reference(self):
        model = international_service()
        raw = dict(
            role="Developer, back-end",
            country="United States of America",
            experience_years=3,
            skills=["Python", "SQL"],
        )
        result = model.advise(raw)
        self.assertEqual(result["unit"], "USD/year")
        self.assertIsNone(result["market_reference"])
        self.assertEqual(result["selected_model"], "random_forest")
        expected = model.predict([model.normalize(raw)])
        self.assertEqual(result["predictions"], {k: round(v[0]) for k, v in expected.items()})
        for item in result["recommendations"]:
            self.assertGreaterEqual(item["role_support"], 5)
            variant = dict(raw, skills=raw["skills"] + [item["skill"]])
            prediction = model.predict([model.normalize(variant)])[model.selected_model][0]
            self.assertEqual(
                item["predicted_delta_usd_year"],
                round(prediction - expected[model.selected_model][0]),
            )

    def test_frozen_hashes_disjoint_groups_and_validation_selection(self):
        for experiment, protocol in [
            ("global_survey_v1_7f2c2dbf6989", "global_survey_protocol.json"),
            ("open_aijobs_v1_ceea75a58f85", "open_aijobs_protocol.json"),
        ]:
            manifest = json.loads((ROOT / "data/splits" / experiment / "manifest.json").read_text())
            self.assertEqual(
                hashlib.sha256((ROOT / "configs" / protocol).read_bytes()).hexdigest(),
                manifest["protocol_sha256"],
            )
            groups = []
            for item in manifest["files"].values():
                path = ROOT / item["path"]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
                frame = pd.read_csv(path)
                self.assertEqual(len(frame), item["rows"])
                groups.append(set(frame.profile_group))
            for i, group in enumerate(groups):
                for other in groups[i + 1 :]:
                    self.assertFalse(group & other)
            selection = json.loads(
                (ROOT / "outputs/metrics" / experiment / "selection.json").read_text()
            )
            expected = min(
                selection["selected"],
                key=lambda k: (
                    selection["selected"][k]["mae_usd_year"],
                    selection["selected"][k]["rmse_usd_year"],
                ),
            )
            self.assertEqual(selection["selected_family"], expected)

    def test_research_units_chart_whitelist_and_png_integrity(self):
        view = overview()
        self.assertEqual(view["international"]["dataset"]["rows"], 10261)
        self.assertEqual(view["benchmark"]["unit"], "VND/month")
        self.assertEqual({b["unit"] for b in view["additional_benchmarks"]}, {"USD/year"})
        for chart in view["charts"] + view["international"]["charts"]:
            self.assertEqual(chart_path(chart["id"]).read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        with self.assertRaises(FileNotFoundError):
            chart_path("global_arbitrary")

    def test_known_annual_usd_never_becomes_vnd_label(self):
        raw = dict(role="Backend Developer", salary_annual_usd=100000)
        result = normalize_row(
            raw,
            {"role": "role", "salary": "salary_annual_usd"},
            AnalysisRequest(dataset_id="0" * 32, currency="VND", period="month"),
        )
        self.assertIsNone(result["salary_monthly_vnd"])

    def test_global_rejections_keep_diagnostics_and_exclude_metrics(self):
        row = dict(
            role="Developer, back-end",
            country="United States of America",
            experience_years=3,
            skills="Python",
            salary_monthly_vnd=20000000,
        )
        dataset = dict(
            rows=[row],
            columns=list(row),
            filename="units.csv",
            provenance="test",
            input_sha256="a" * 64,
            snapshot_sha256="b" * 64,
        )
        options = AnalysisRequest(
            dataset_id="0" * 32,
            market="international_survey",
            mapping={k if k != "salary_monthly_vnd" else "salary": k for k in row},
            currency="USD",
            period="year",
        )
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(
                international_service(),
                "predict",
                return_value={"ridge": [np.nan], "random_forest": [50000.0]},
            ),
        ):
            folder = Path(temporary)
            report = analyze_international(dataset, options, folder, lambda *_: None)
            result = json.loads((folder / "results.json").read_text())[0]
            self.assertIsNone(result["salary_annual_usd"])
            self.assertEqual(result["prediction_diagnostic"]["ridge"], "nan")
            self.assertEqual(report["summary"]["invalid"], 1)
            self.assertEqual(report["metrics"], {})
            self.assertTrue(any("1 dòng" in w for w in report["warnings"]))
        with self.assertRaisesRegex(ValueError, "Gemma"):
            analyze_international(
                dataset, options.model_copy(update={"use_gemma": True}), ROOT, lambda *_: None
            )

    def test_api_batch_export_units_duplicate_invalid_and_templates(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            TestClient(create_app(temporary)) as client,
        ):
            self.assertEqual(client.get("/api/international/meta").json()["unit"], "USD/year")
            for ext in ["csv", "xlsx", "json"]:
                self.assertEqual(
                    client.get("/api/templates/international_demo." + ext).status_code, 200
                )
            demo = client.post("/api/datasets/demo?market=international_survey").json()
            self.assertEqual(demo["row_count"], 48)
            self.assertIn("không phải holdout", demo["provenance"])
            first = dict(
                role="Developer, back-end",
                country="United States of America",
                experience_years=3,
                skills="Python;SQL",
                salary_annual_usd=100000,
            )
            frame = pd.DataFrame(
                [
                    first,
                    first,
                    dict(first, salary_annual_usd=110000, experience_years=4),
                    dict(first, country="Atlantis"),
                    dict(first, skills=[1, 2]),
                ]
            )
            uploaded = client.post(
                "/api/datasets",
                files={
                    "file": (
                        "profiles.json",
                        frame.to_json(orient="records").encode(),
                        "application/json",
                    )
                },
            ).json()
            response = client.post(
                "/api/analyses",
                json=dict(
                    dataset_id=uploaded["dataset_id"],
                    mapping=uploaded["suggested_mapping"],
                    market="international_survey",
                ),
            )
            self.assertEqual(response.status_code, 202, response.text)
            identifier = response.json()["id"]
            for _ in range(300):
                state = client.get("/api/analyses/" + identifier).json()
                if state["status"] in {"completed", "failed"}:
                    break
                time.sleep(0.05)
            self.assertEqual(state["status"], "completed", state)
            report = state["result"]
            self.assertEqual(report["unit"], "USD/year")
            self.assertEqual(report["summary"]["duplicates"], 1)
            self.assertEqual(report["summary"]["invalid"], 2)
            self.assertEqual(report["metrics"]["ridge"]["samples"], 2)
            self.assertNotIn("mae_vnd", report["metrics"]["ridge"])
            rows = client.get(f"/api/analyses/{identifier}/rows").json()["rows"]
            self.assertNotIn("predicted_salary_vnd", rows[0])
            self.assertIsNone(rows[-1]["predicted_salary_usd_year"])
            self.assertTrue(any("danh sách chuỗi" in error for error in rows[-1]["errors"]))
            archive = client.get(f"/api/analyses/{identifier}/artifacts/analysis.zip").content
            with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                self.assertIsNone(zipped.testzip())
                manifest = json.loads(zipped.read("manifest.json"))
                self.assertEqual(manifest["unit"], "USD/year")
                for name, digest in manifest["files"].items():
                    self.assertEqual(hashlib.sha256(zipped.read(name)).hexdigest(), digest)
                self.assertIn(
                    "predicted_salary_usd_year", zipped.read("results.csv").decode("utf-8-sig")
                )
            rejected = client.post(
                "/api/career/advice",
                json=dict(
                    role=first["role"],
                    experience_years=3,
                    skills=["Python"],
                    market="international_survey",
                    country="Atlantis",
                ),
            )
            self.assertEqual(rejected.status_code, 422)
            self.assertIn("quốc gia", rejected.json()["detail"])


if __name__ == "__main__":
    unittest.main()

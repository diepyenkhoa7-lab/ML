"""Salary-v2 labels stay explicit about weak periods and prediction-time features."""

import unittest

from scripts.prepare_salary_v2 import extract_skills, salary_label


class SalaryV2LabelTests(unittest.TestCase):
    def row(self, **changes):
        return dict(
            job_title="Backend Developer",
            salary="20 - 30 triệu",
            benefits="",
            requirements="",
            job_description="",
            **changes,
        )

    def test_missing_period_is_weak_and_matching_month_evidence_is_strict(self):
        label, reason = salary_label(self.row())
        self.assertEqual(label[1], "assumed_month_train_only")
        raw = self.row()
        raw["benefits"] = "Mức lương 20–30 triệu/tháng; thưởng khác tính riêng."
        label, reason = salary_label(raw)
        self.assertEqual(label[:2], (25e6, "explicit_month"))
        self.assertIsNone(reason)

    def test_mismatched_other_amount_does_not_certify_month(self):
        raw = self.row()
        raw["benefits"] = "Lương 10–15 triệu/tháng"
        self.assertEqual(salary_label(raw)[0][1], "assumed_month_train_only")

    def test_censored_industrial_foreign_and_annual_are_not_point_labels(self):
        for changes in [
            dict(job_title="Backend upto 50 triệu", salary="50 triệu"),
            dict(salary="Từ 20 triệu"),
            dict(salary="1000–2000 USD/tháng"),
            dict(salary="240 triệu/năm"),
            dict(job_title="Lập trình PLC"),
            dict(salary="20 triệu/tháng/năm"),
        ]:
            raw = self.row()
            raw.update(changes)
            with self.subTest(changes=changes):
                self.assertIsNone(salary_label(raw)[0])
        raw = self.row()
        raw.update(salary="50 triệu", benefits="Lương up to 50 triệu/tháng")
        self.assertIsNone(salary_label(raw)[0])

    def test_skill_extractor_uses_boundaries_and_no_salary_feature(self):
        skills = extract_skills("Python, PostgreSQL, C++, C#; JavaScript. Annual salary 90000.")
        self.assertIn("Python", skills)
        self.assertIn("C++", skills)
        self.assertIn("C#", skills)
        self.assertNotIn("Java", skills)
        self.assertFalse(any("90000" in s or "salary" in s for s in skills))


class MarketReferenceTests(unittest.TestCase):
    def test_reference_is_explicit_aggregate_and_never_replaces_prediction(self):
        from backend.app.services.market import market_reference

        reference = market_reference("Backend Developer", 3.5, 27123456)
        self.assertEqual(reference["median_vnd_month"], 30100000)
        self.assertEqual(reference["prediction_minus_median_vnd"], 27123456 - 30100000)
        self.assertIn("không dùng để sửa", reference["caution"])
        self.assertFalse(market_reference("Software Developer", 3, 20e6)["available"])
        self.assertFalse(market_reference("Backend Developer", None, 20e6)["available"])


class SalaryV2ServingTests(unittest.TestCase):
    def test_active_model_selected_by_validation_and_preserves_pipeline_predictions(self):
        import json

        import joblib
        import numpy as np
        import pandas as pd

        from backend.app.services.salary import FEATURES, ROOT, salary_service

        service = salary_service()
        self.assertEqual(service.experiment, "v2_042e3aa1a886")
        self.assertEqual(service.selected_model, "ridge")
        source = service.train.head(20).copy()
        rows = []
        for raw in source.to_dict("records"):
            rows.append(
                dict(
                    role=raw["role"],
                    level=raw["level"],
                    location=raw["location"],
                    experience_years=raw["experience_years"],
                    skills=raw["skills"].split(";") if pd.notna(raw["skills"]) else [],
                )
            )
        actual = service.predict(rows)
        for family in ["ridge", "random_forest"]:
            path = ROOT / service.manifest["artifacts"][family]["path"]
            expected = joblib.load(path).predict(service.features(rows)[FEATURES])
            np.testing.assert_allclose(actual[family], expected, rtol=1e-12)
        meta = json.loads((ROOT / service.manifest["evaluation"]["path"]).read_text())
        self.assertTrue(meta["promotion_eligible"])
        self.assertEqual(service.historical_test, meta["test"]["ridge"])
        self.assertLess(
            service.historical_test["mae_vnd"], meta["test"]["v1_random_forest"]["mae_vnd"]
        )

    def test_explicit_holdouts_and_train_company_disjointness(self):
        import json

        import pandas as pd

        from backend.app.services.salary import ROOT
        from scripts.clean_data import checksum

        folder = ROOT / "data/splits/v2.1.0/vn_developer"
        manifest = json.loads((folder / "manifest.json").read_text())
        groups = {}
        for name, item in manifest["files"].items():
            self.assertEqual(checksum(ROOT / item["path"]), item["sha256"])
            frame = pd.read_csv(ROOT / item["path"])
            groups[name] = set(frame.leakage_group_id)
            if name in {"valid", "test"}:
                self.assertTrue(frame.label_quality.eq("explicit_month").all())
        held = groups["valid"] | groups["test"]
        self.assertFalse(groups["valid"] & groups["test"])
        self.assertFalse(groups["train"] & held)
        self.assertFalse(groups["weak_train"] & held)


if __name__ == "__main__":
    unittest.main()

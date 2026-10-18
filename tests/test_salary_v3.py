"""Evidence contracts for the next salary experiment, including observed source failures."""

import unittest

from scripts.salary_v3_labels import direct_label, title_level


class DirectMonthlyLabelTests(unittest.TestCase):
    def row(self, benefits, **changes):
        return dict(
            job_title="Backend Developer",
            salary="20-30 triệu",
            benefits=benefits,
            job_description="",
            **changes,
        )

    def test_direct_body_label_replaces_bucket_with_explicit_evidence(self):
        label, reason = direct_label(self.row("Mức lương: 21 - 27 triệu đồng/tháng."))
        self.assertIsNone(reason)
        self.assertEqual(label["salary_monthly_vnd"], 24e6)
        self.assertTrue(label["header_differs"])
        self.assertEqual(label["field"], "benefits")

    def test_monthly_bonus_or_month_13_does_not_certify_salary(self):
        for clause in [
            "Lương 20-30 triệu; thưởng hàng tháng",
            "Lương 20-30 triệu. Lương tháng 13",
            "Phụ cấp 2-3 triệu/tháng",
            "Lương 20-30 triệu/năm",
        ]:
            self.assertIsNone(direct_label(self.row(clause))[0])

    def test_censored_foreign_net_conflicting_and_unbounded_are_quarantined(self):
        for clause in [
            "Lương up to 20-30 triệu/tháng",
            "Lương 1000-2000 USD/tháng",
            "Lương 20-30 triệu NET/tháng",
            "Lương từ 30 triệu/tháng",
            "Lương 20-30 triệu/tháng; lương 25-35 triệu/tháng",
        ]:
            with self.subTest(clause=clause):
                self.assertIsNone(direct_label(self.row(clause))[0])

    def test_m_shorthand_and_month_before_range_are_anchored(self):
        for clause in ["Lương tháng 10M - 15M, thưởng riêng", "Lương 10-15M/tháng"]:
            self.assertEqual(direct_label(self.row(clause))[0]["salary_monthly_vnd"], 12.5e6)

    def test_explicit_title_seniority_wins_generic_position_but_mixed_is_unknown(self):
        self.assertEqual(title_level("Nhân viên", "Senior Backend Developer"), "Senior")
        self.assertEqual(title_level("Nhân viên", "Junior/Middle Developer"), "Unknown")

    def test_v31_preserves_explicit_month_metadata_and_rejects_conflicts(self):
        from scripts.salary_v31_labels import direct_label as v31_label

        raw = self.row("")
        raw["salary"] = "20000000 - 30000000 VND MONTH"
        self.assertEqual(v31_label(raw)[0]["salary_monthly_vnd"], 25e6)
        raw["benefits"] = "Lương 21-27 triệu/tháng"
        self.assertEqual(v31_label(raw)[1], "conflicting_direct_monthly_ranges")
        raw["salary"] = "20000000 - 30000000 VND"
        raw["benefits"] = ""
        self.assertIsNone(v31_label(raw)[0])

    def test_public_metadata_experience_mismatch_is_not_trusted(self):
        from scripts.prepare_salary_v31 import public_record

        raw = dict(
            url="https://example.test/job/123",
            job_posting=dict(
                title="Full Stack Developer",
                datePosted="2026-10-16",
                baseSalary=dict(
                    currency="VND", value=dict(unitText="MONTH", minValue=23e6, maxValue=28e6)
                ),
                hiringOrganization=dict(name="Example company"),
                description="Từ 1 - 3 năm kinh nghiệm phát triển ứng dụng.",
                experienceRequirements=dict(monthsOfExperience="60"),
            ),
        )
        self.assertEqual(public_record(raw)[1], "missing_or_conflicting_experience")

    def test_failed_experiments_cannot_be_loaded_as_web_salary_model(self):
        from backend.app.services.salary import SalaryService

        for experiment in ["v3_b5ae152b9dd5", "v31_b089fdf458a5"]:
            with (
                self.subTest(experiment=experiment),
                self.assertRaisesRegex(ValueError, "nghiệm thu"),
            ):
                SalaryService(experiment)

    def test_frozen_strict_splits_and_annotation_do_not_leak_holdouts(self):
        import json

        import pandas as pd

        from backend.app.services.salary import ROOT
        from scripts.clean_data import checksum

        folder = ROOT / "data/splits/v3.1.0/vn_developer"
        manifest = json.loads((folder / "manifest.json").read_text())
        parts = {}
        for name, item in manifest["files"].items():
            path = ROOT / item["path"]
            self.assertEqual(checksum(path), item["sha256"])
            parts[name] = pd.read_csv(path)
            self.assertFalse(parts[name].label_quality.str.contains("assumed").any())
        training = pd.concat([parts["train"], parts["older_train"]])
        self.assertFalse(set(training.leakage_group_id) & set(parts["valid"].leakage_group_id))
        self.assertFalse(
            set(parts["test"].leakage_group_id)
            & (set(training.leakage_group_id) | set(parts["valid"].leakage_group_id))
        )
        queue = ROOT / "data/annotation/v3.1.0/salary_review_queue.jsonl"
        records = [json.loads(line) for line in queue.read_text().splitlines()]
        self.assertEqual({r["record_id"] for r in records}, set(training.record_id))
        self.assertTrue(all(r["gold"] is None and r["review_status"] == "pending" for r in records))
        self.assertTrue(all("messages" not in r for r in records))


if __name__ == "__main__":
    unittest.main()

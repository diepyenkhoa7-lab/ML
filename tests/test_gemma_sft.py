import importlib
import unittest


class GemmaSFTTests(unittest.TestCase):
    def module(self):
        return importlib.import_module("scripts.prepare_gemma_sft")

    def row(self, **changes):
        value = dict(
            record_id="vietjobs_2025:1",
            source_dataset="vietjobs_2025",
            title="Backend Python Developer",
            location_raw="Hà Nội",
            location="Hà Nội",
            experience_raw="3 năm",
            experience_years=3.0,
            skills_raw="['Python', 'SQL']",
            skills_json='["Python", "SQL"]',
            salary_raw="20.0 - 30.0 triệu",
            salary_min=20e6,
            salary_max=30e6,
            currency="VND",
            salary_period="month",
            role="Backend Developer",
            company=None,
            leakage_group_id="g1",
        )
        value.update(changes)
        return value

    def test_job_card_preserves_native_units_and_traceability(self):
        m = self.module()
        example = m.make_example(
            self.row(
                salary_min=200e6,
                salary_max=500e6,
                salary_period="year",
                salary_raw="200tr-500tr ₫/năm",
                source_dataset="user_vietnam_it_jobs",
            ),
            "original",
        )
        self.assertEqual(example["source_record_id"], "vietjobs_2025:1")
        self.assertEqual(example["group_id"], "g1")
        label = m.json.loads(example["messages"][-1]["content"])
        self.assertEqual(label["salary_min"], 200e6)
        self.assertEqual(label["salary_period"], "year")
        self.assertNotIn("29166666", example["messages"][-1]["content"])
        self.assertEqual(label["skills"], ["Python", "SQL"])

    def test_safe_missing_field_variants_do_not_hide_evidence_in_title(self):
        m = self.module()
        example = m.make_example(self.row(), "omit_salary")
        label = m.json.loads(example["messages"][-1]["content"])
        self.assertTrue(
            all(label[k] is None for k in ["salary_min", "salary_max", "currency", "salary_period"])
        )
        self.assertNotIn("20.0 - 30.0", example["messages"][-2]["content"])
        self.assertIsNone(
            m.make_example(self.row(title="Developer lương 20-30 triệu"), "omit_salary")
        )
        self.assertIsNone(
            m.make_example(self.row(title="Python Developer 3 năm kinh nghiệm"), "omit_experience")
        )
        example = m.make_example(self.row(), "omit_experience")
        label = m.json.loads(example["messages"][-1]["content"])
        self.assertIsNone(label["experience_years"])

    def test_schema_rejects_invalid_targets_and_missing_keys(self):
        m = self.module()
        label = m.json.loads(m.make_example(self.row(), "original")["messages"][-1]["content"])
        m.validate_label(label)
        bad = dict(label, salary_min=-1)
        with self.assertRaises(ValueError):
            m.validate_label(bad)
        bad = dict(label)
        bad.pop("currency")
        with self.assertRaises(ValueError):
            m.validate_label(bad)


class GemmaTrainingGateTests(unittest.TestCase):
    def test_default_command_never_starts_training(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch

        from scripts import gemma_train

        with (
            patch.object(
                gemma_train, "build_plan", return_value={"status": "awaiting_human_confirmation"}
            ),
            patch.object(gemma_train.Path, "write_text"),
            patch.object(gemma_train.subprocess, "Popen") as launch,
            redirect_stdout(StringIO()),
        ):
            self.assertEqual(gemma_train.main([]), 0)
            launch.assert_not_called()

    def test_group_leakage_and_conflicting_targets_are_rejected(self):
        import json
        import tempfile
        from pathlib import Path

        from scripts.validate_sft import validate_corpus

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for split, label in [("train", "A"), ("valid", "B"), ("test", "C")]:
                row = {
                    "source_record_id": split,
                    "group_id": "shared-group",
                    "messages": [
                        {"role": "user", "content": "Same job"},
                        {"role": "assistant", "content": label},
                    ],
                }
                (path / f"{split}.jsonl").write_text(json.dumps(row) + "\n")
            result = validate_corpus(path)
            self.assertFalse(result["ok"])
            self.assertTrue(any("group_id overlaps" in e for e in result["errors"]))
            self.assertTrue(any("conflicting targets" in e for e in result["errors"]))


class ExtractionMetricTests(unittest.TestCase):
    def test_invalid_json_counts_as_wrong_instead_of_dropping_row(self):
        import json

        from scripts.evaluate_gemma import score
        from scripts.prepare_gemma_sft import make_example

        row = make_example(GemmaSFTTests().row(), "original")
        good = dict(
            index=0, source_record_id=row["source_record_id"], output=row["messages"][-1]["content"]
        )
        result = score([row], [good])
        self.assertEqual(result["json_validity"], 1)
        self.assertEqual(result["skill_micro_f1"], 1)
        self.assertTrue(all(v == 1 for v in result["field_exact_accuracy"].values()))
        bad = dict(good, output="not JSON")
        result = score([row], [bad])
        self.assertEqual(result["json_validity"], 0)
        self.assertEqual(result["skill_micro_f1"], 0)
        self.assertTrue(all(v == 0 for v in result["field_exact_accuracy"].values()))
        partial = dict(good, output=json.dumps({"skills": ["Python"]}))
        result = score([row], [partial])
        self.assertAlmostEqual(result["skill_micro_f1"], 2 / 3)
        self.assertEqual(result["schema_validity"], 0)


if __name__ == "__main__":
    unittest.main()

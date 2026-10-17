import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.select_gemma_adapter import load_evaluation, promotion, quality, targets_met


class GemmaSelectionTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads(Path("configs/gemma_tuning_protocol.json").read_text())
        self.metrics = dict(
            field_exact_accuracy={key: 0.95 for key in range(8)},
            json_validity=1.0,
            schema_validity=0.98,
            skill_micro_f1=0.92,
        )

    def test_targets_and_weighted_score(self):
        values = quality(self.metrics)
        self.assertAlmostEqual(values["selection_score"], 0.947)
        self.assertTrue(targets_met(values, self.protocol))
        self.assertFalse(targets_met(dict(values, skill_micro_f1=0.91), self.protocol))

    def test_higher_composite_cannot_override_skill_regression(self):
        current = quality(self.metrics)
        candidate = dict(current, selection_score=0.99, skill_micro_f1=0.89)
        promoted, reasons = promotion(current, candidate, self.protocol)
        self.assertFalse(promoted)
        self.assertIn("skill_micro_f1 regression exceeds guardrail", reasons)
        self.assertFalse(promotion(current, dict(current), self.protocol)[0])
        self.assertTrue(promotion(current, dict(current, selection_score=0.96), self.protocol)[0])

    def test_test_metrics_never_enter_validation_selection(self):
        with patch.object(Path, "read_text", return_value='{"split":"test"}'):
            with self.assertRaisesRegex(ValueError, "Wrong selection split"):
                load_evaluation(Path("pretend-test"))

    def test_nonfinite_metrics_rejected(self):
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            quality(dict(self.metrics, skill_micro_f1=float("nan")))

    def test_duplicate_skills_and_inferred_zero_remain_visible_as_errors(self):
        from scripts.evaluate_gemma import score

        target = dict(
            role="Backend Developer",
            location="Hà Nội",
            experience_years=None,
            skills=["Python"],
            salary_min=None,
            salary_max=None,
            currency=None,
            salary_period=None,
        )
        row = dict(source_record_id="regression", messages=[dict(content=json.dumps(target))])
        prediction = dict(
            index=0,
            source_record_id="regression",
            output=json.dumps(dict(target, skills=["Python", "Python"], experience_years=0)),
        )
        result = score([row], [prediction])
        self.assertEqual(result["skill_micro_f1"], 1)
        self.assertEqual(result["schema_validity"], 0)
        self.assertEqual(result["field_exact_accuracy"]["experience_years"], 0)


if __name__ == "__main__":
    unittest.main()

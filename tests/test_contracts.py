import json
import unittest

import numpy as np

from career_ai.data import inverse, load, prompt, target
from career_ai.vn_labels import salary_label


class Contracts(unittest.TestCase):
    def test_split_groups_are_disjoint(self):
        frames = [load(s) for s in ["train", "valid", "test"]]
        for i, a in enumerate(frames):
            for b in frames[i + 1 :]:
                self.assertFalse(set(a.group) & set(b.group))

    def test_salary_never_enters_prompt(self):
        row = load("train").iloc[0].to_dict()
        text = prompt(row)
        self.assertNotIn("salary", json.loads(text.split("\n", 1)[1]))
        altered = dict(row, salary=123456789)
        self.assertEqual(prompt(row), prompt(altered))

    def test_units_round_trip(self):
        f = load("train")
        np.testing.assert_allclose(inverse(target(f), f.market), f.salary, rtol=1e-6)

    def test_missing_month_is_weak_not_strict(self):
        label, _ = salary_label(
            dict(
                job_title="Python Developer",
                salary="20 - 30 triệu",
                benefits="",
                requirements="",
                job_description="",
            )
        )
        self.assertEqual(label[1], "assumed_month_train_only")


if __name__ == "__main__":
    unittest.main()


class ProfileValidation(unittest.TestCase):
    def test_invalid_types_and_units_rejected(self):
        from career_ai.data import validate_profile

        row = dict(
            market="vietnam",
            role="Backend Developer",
            location="Hà Nội",
            experience_years=3,
            skills=["Python"],
        )
        self.assertEqual(validate_profile(row)["skills"], "python")
        for change in [
            dict(market="USD"),
            dict(experience_years=float("nan")),
            dict(skills=[12]),
            dict(location=""),
        ]:
            with self.assertRaises((ValueError, TypeError)):
                validate_profile(dict(row, **change))


class EvaluationContracts(unittest.TestCase):
    def test_language_groups_follow_partition(self):
        from career_ai.data import load_language

        for split in ["train", "valid", "test"]:
            groups = set(load(split).group)
            examples = load_language(split)
            self.assertTrue(examples)
            self.assertTrue(all(e["group"] in groups for e in examples))
            self.assertTrue(all(e["label_quality"] == "source_derived_silver" for e in examples))

    def test_metrics_keep_units_and_small_groups(self):
        import pandas as pd

        from career_ai.evaluation import metrics

        frame = pd.DataFrame(
            [
                dict(market="vietnam", role="backend", experience_years=2, salary=20e6),
                dict(market="international", role="backend", experience_years=5, salary=100000),
            ]
        )
        result = metrics(frame, [21e6, 90000])
        self.assertEqual(result["by_market"]["vietnam"]["mae"], 1e6)
        self.assertEqual(result["by_market"]["international"]["mae"], 10000)
        self.assertIsNone(result["by_market"]["vietnam"]["r2"])

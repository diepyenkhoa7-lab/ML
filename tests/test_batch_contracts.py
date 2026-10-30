import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from career_ai.inputs import missing, read_profiles
from career_ai.language import evaluate_language, normalize_skill_names, validate_recommendations


class BatchContracts(unittest.TestCase):
    def test_advice_alias_requires_canonical_evidence(self):
        value = dict(skills=["AWS", "Rust"], explanation="Liên hệ quan sát")
        evidence = [dict(skill="amazon web services (aws)"), dict(skill="rust")]
        normalized = normalize_skill_names(value, evidence)
        self.assertEqual(validate_recommendations(normalized, evidence), evidence)
        with self.assertRaises(ValueError):
            validate_recommendations(normalize_skill_names(value, evidence[1:]), evidence[1:])

    def test_csv_json_xlsx_agree_and_missing_experience_is_none(self):
        rows = [
            dict(
                market="vietnam",
                role="Backend Developer",
                location="Hà Nội",
                experience_years=0,
                skills="",
            ),
            dict(
                market="international",
                role="Developer",
                location="Germany",
                experience_years=None,
                skills="python",
            ),
        ]
        frame = pd.DataFrame(rows)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "profiles.json").write_text(json.dumps(rows))
            frame.to_csv(root / "profiles.csv", index=False)
            frame.to_excel(root / "profiles.xlsx", index=False)
            for suffix in ["csv", "json", "xlsx"]:
                value = read_profiles(root / ("profiles." + suffix))
                self.assertEqual(len(value), 2)
                self.assertEqual(value.iloc[0].experience_years, 0)
                self.assertIsNone(value.iloc[1].experience_years)
                self.assertFalse(missing(value.iloc[0].experience_years))

    def test_language_failure_never_gets_perfect_empty_skill_f1(self):
        item = dict(prompt="", answer=dict(role=None, experience_years=None, skills=[]))
        with patch("career_ai.language.extract", side_effect=ValueError("invalid JSON")):
            result = evaluate_language(None, [item])
        self.assertEqual(result["json_schema_rate"], 0)
        self.assertEqual(result["skill_f1"], 0)
        self.assertIsNone(evaluate_language(None, [])["skill_f1"])

    def test_llm_cannot_select_unsupported_skills_or_invent_statistics(self):
        evidence = [dict(skill="python", support=20, observed_difference=100)]
        result = validate_recommendations(
            dict(skills=["python"], explanation="Observed only"), evidence
        )
        self.assertEqual(result, evidence)
        for value in [
            dict(skills=["rust"], explanation="..."),
            dict(skills=["python", "python"], explanation="..."),
            dict(skills=["python"], explanation=None),
        ]:
            with self.assertRaises(ValueError):
                validate_recommendations(value, evidence)


class GenerationPostprocess(unittest.TestCase):
    def test_generation_uses_token_prompt_stripping(self):
        from types import SimpleNamespace
        from unittest.mock import Mock

        import numpy as np

        from career_ai.language import generate_json

        lm = SimpleNamespace(
            preprocessor=SimpleNamespace(tokenizer=lambda text: np.arange(10)),
            generate=Mock(return_value='{"answer": "tiếng Việt"}'),
        )
        self.assertEqual(generate_json(lm, "Hồ sơ"), {"answer": "tiếng Việt"})
        self.assertTrue(lm.generate.call_args.kwargs["strip_prompt"])

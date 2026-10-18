import unittest

from backend.app.schemas import AnalysisRequest
from backend.app.services.data import normalize_row


class SourceGroundingTests(unittest.TestCase):
    def test_hallucinated_and_generic_skills_do_not_become_prediction_features(self):
        source = "Laravel, PHP, Git, MySQL, RESTful API. Routing, middleware and testing."
        extracted = dict(
            role="Backend Developer",
            location="TP.HCM",
            experience_years=1,
            skills=["PHP", "Express (implied)", "SQL", "Routing"],
        )
        row = normalize_row(
            {"description": source},
            {"description": "description"},
            AnalysisRequest(dataset_id="0" * 32),
            extracted,
        )
        self.assertEqual(set(row["skills"]), {"Laravel", "PHP", "Git", "MySQL", "REST API"})
        self.assertEqual(row["extraction"], extracted)
        self.assertNotIn("SQL", row["skills"])
        self.assertEqual(row["skill_evidence"]["evidence"]["MySQL"], "MySQL")

    def test_explicit_user_skills_override_description_inventory(self):
        row = normalize_row(
            {"description": "Python", "skills": "Zig;Rust", "role": "Backend Developer"},
            {k: k for k in ["description", "skills", "role"]},
            AnalysisRequest(dataset_id="0" * 32),
            {"skills": ["Python"]},
        )
        self.assertEqual(set(row["skills"]), {"Zig", "Rust"})
        self.assertIsNone(row["skill_evidence"])


if __name__ == "__main__":
    unittest.main()

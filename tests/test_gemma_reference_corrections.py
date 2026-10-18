import json
import unittest

from scripts.adjudicate_gemma_corrections import adjudicate
from scripts.refine_gemma_references import (
    experience_with_words,
    literal_skills,
    proposed_correction,
)


class ReferenceCorrectionTests(unittest.TestCase):
    def test_word_numbers_and_month_units(self):
        self.assertEqual(experience_with_words("Có ít nhất một năm kinh nghiệm")[0], 1)
        self.assertAlmostEqual(
            experience_with_words("Có 10 tháng kinh nghiệm liên quan")[0], 10 / 12
        )
        self.assertEqual(experience_with_words("two years of experience")[0], 2)
        self.assertEqual(experience_with_words("Python4–6+ năm kinh nghiệm thực chiến")[0], 4)
        self.assertEqual(experience_with_words("1+ years of experience in React")[0], 1)
        self.assertIsNone(experience_with_words("Sinh viên năm thứ 4, có kinh nghiệm Python")[0])

    def test_conflicting_experience_abstains(self):
        self.assertIsNone(
            experience_with_words("Một năm kinh nghiệm Java, hai năm kinh nghiệm SQL")[0]
        )
        self.assertIsNone(experience_with_words("Senior Python Developer")[0])

    def test_literal_skills_no_inferred_prerequisites(self):
        skills, evidence = literal_skills("ONNX, TensorRT, OpenVINO, BERT, Deep Learning, RESTAPI")
        self.assertEqual(
            set(skills), {"ONNX", "TensorRT", "OpenVINO", "BERT", "Deep Learning", "REST API"}
        )
        self.assertEqual(evidence["REST API"], "RESTAPI")
        self.assertNotIn("Python", skills)
        skills, _ = literal_skills("React Native; ASP.NET Web API; JavaScript")
        self.assertNotIn("React", skills)
        self.assertNotIn("Java", skills)
        self.assertIn("ASP.NET Web API", skills)
        self.assertNotIn("ASP.NET", skills)

    def test_address_and_salary_do_not_create_labels(self):
        row = {
            "source_record_id": "test:1",
            "split": "train",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Chức danh: Developer\nĐịa điểm: Tòa nhà BERT, Python\n"
                        "Lương nguồn: 10 năm kinh nghiệm\n"
                        "Yêu cầu trích nguyên văn: Có ít nhất một năm kinh nghiệm, dùng ONNX"
                    ),
                },
                {
                    "role": "assistant",
                    "content": json.dumps({"skills": [], "experience_years": None}),
                },
            ],
        }
        result = proposed_correction(row)
        self.assertEqual(result["changes"]["skills"]["after"], ["ONNX"])
        self.assertEqual(result["changes"]["experience_years"]["after"], 1)
        self.assertEqual(result["status"], "pending_adjudication")

    def test_adjudication_preserves_overall_and_specific_framework(self):
        result = adjudicate({"source_record_id": "tinixai:4622", "changes": {}})
        self.assertEqual(result["status"], "rejected_correction_keep_existing")
        proposal = {
            "source_record_id": "tinixai:277770",
            "changes": {
                "skills": {"after": ["Ant Design"], "evidence": {"Ant Design": "Ant Design"}}
            },
        }
        result = adjudicate(proposal)
        self.assertEqual(result["changes"]["skills"]["after"], ["Ant Design Mobile"])
        self.assertEqual(proposal["changes"]["skills"]["after"], ["Ant Design"])
        self.assertFalse(result["human_gold"])


if __name__ == "__main__":
    unittest.main()

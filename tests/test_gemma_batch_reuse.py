import json
import unittest

from backend.app.services.contracts import digest
from scripts.app_gemma_extract import extract_card_items


class Tokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return messages[-1]["content"]

    def encode(self, prompt):
        return list(prompt)


class BatchReuseTests(unittest.TestCase):
    def test_duplicate_rows_generate_once_and_keep_all_row_identities(self):
        calls = []
        label = dict(
            role="Backend Developer",
            location=None,
            experience_years=2.0,
            skills=["Python"],
            salary_min=None,
            salary_max=None,
            currency=None,
            salary_period=None,
        )

        def generate(*args, **kwargs):
            calls.append(kwargs["prompt"])
            return json.dumps(label)

        cards = ["A", "B", "A", "B", "A"]
        items, provenance = extract_card_items(cards, Tokenizer(), None, generate, None)
        self.assertEqual(calls, ["A", "B"])
        self.assertEqual(provenance["generation_calls"], "2")
        self.assertEqual(provenance["reused_rows"], "3")
        self.assertEqual([item["index"] for item in items], list(range(5)))
        self.assertEqual([item["input_sha256"] for item in items], [digest(c) for c in cards])
        self.assertTrue(all(item["value"] == label for item in items))

    def test_errors_still_return_each_row_without_repeated_generation(self):
        calls = []

        def generate(*args, **kwargs):
            calls.append(1)
            return "invalid JSON"

        cards = ["A", "A", "x" * 1000, "x" * 1000]
        items, provenance = extract_card_items(cards, Tokenizer(), None, generate, None)
        self.assertEqual(len(calls), 1)
        self.assertTrue(all(item["value"] is None and item["error"] for item in items))
        self.assertEqual(provenance["generation_calls"], "1")


if __name__ == "__main__":
    unittest.main()

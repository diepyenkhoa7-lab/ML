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
    def test_context_extension_keeps_full_prompt_and_rejects_overflow(self):
        calls = []

        def generate(*args, **kwargs):
            calls.append(kwargs["prompt"])
            return "invalid JSON"

        cards = ["x" * 1500, "y" * 4000]
        items, provenance = extract_card_items(
            cards, Tokenizer(), None, generate, None, context_limit=4096
        )
        self.assertEqual(calls[0], cards[0])
        self.assertEqual(len(calls), 2)
        self.assertEqual(items[0]["raw_output"], "invalid JSON")
        self.assertIsNone(items[1]["raw_output"])
        self.assertIn("4,096", items[1]["error"])
        self.assertEqual(provenance["generation_calls"], "2")

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
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(item["value"] is None and item["error"] for item in items))
        self.assertEqual(provenance["generation_calls"], "2")
        self.assertEqual(provenance["schema_retries"], "1")

    def test_retry_keeps_both_raw_outputs_instead_of_repairing_json(self):
        valid = dict(
            role=None,
            location=None,
            experience_years=None,
            skills=["Python"],
            salary_min=None,
            salary_max=None,
            currency=None,
            salary_period=None,
        )
        duplicate = dict(valid, skills=["Python", "Python"])
        outputs = [json.dumps(duplicate), json.dumps(valid)]
        sequence = iter(outputs)
        items, provenance = extract_card_items(
            ["A", "A"], Tokenizer(), None, lambda *a, **kw: next(sequence), None
        )
        self.assertEqual(items[0]["attempts"], outputs)
        self.assertEqual(items[1]["attempts"], outputs)
        self.assertEqual(items[0]["raw_output"], outputs[-1])
        self.assertEqual(items[0]["value"], valid)
        self.assertIsNone(items[0]["error"])
        self.assertEqual(provenance["generation_calls"], "2")
        self.assertEqual(provenance["reused_rows"], "1")


if __name__ == "__main__":
    unittest.main()

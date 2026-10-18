import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.clean_data import checksum
from scripts.gemma_train import check_transition_budget
from scripts.prepare_gemma_corrected import corrected_label
from scripts.rescore_gemma_references import assert_same_prompts
from scripts.validate_sft import validate_corpus


class CorrectedCorpusTests(unittest.TestCase):
    def test_cumulative_trial_budget_does_not_reset_with_a_new_protocol(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prior = root / "prior.json"
            prior.write_text('{"max_candidates":1}')
            protocol = root / "next.json"
            protocol.write_text(
                json.dumps(
                    dict(
                        max_candidates=3,
                        max_combined_candidates=2,
                        prior_protocol_file="prior.json",
                        prior_protocol_sha256=checksum(prior),
                    )
                )
            )
            transition = dict(path="next.json", sha256=checksum(protocol))
            plan = dict(resume=dict(data_transition=transition))
            for name, value in [("old", checksum(prior)), ("current", checksum(protocol))]:
                path = root / f"outputs/training_logs/gemma_{name}"
                path.mkdir(parents=True)
                (path / "run.json").write_text(
                    json.dumps(dict(resume=dict(data_transition=dict(sha256=value))))
                )
            with self.assertRaisesRegex(ValueError, "Combined trial budget exhausted"):
                check_transition_budget(plan, root)

    def test_corrected_corpus_preserves_prompts_groups_and_replay(self):
        root = Path("data/finetune_reviewed")
        for split in ["train", "valid", "test"]:
            old = [
                json.loads(x) for x in (root / "v2.0.0" / f"{split}.jsonl").read_text().splitlines()
            ]
            new = [
                json.loads(x) for x in (root / "v2.2.0" / f"{split}.jsonl").read_text().splitlines()
            ]
            assert_same_prompts(old, new)
            for before, after in zip(old, new, strict=True):
                if before["source_dataset"] != "tinixai_reviewed":
                    self.assertEqual(before, after)
                else:
                    label, _ = corrected_label(before)
                    self.assertEqual(json.loads(after["messages"][-1]["content"]), label)
        self.assertTrue(validate_corpus(root / "v2.2.0", strict=True)["ok"])

    def test_cached_prediction_reuse_rejects_changed_input(self):
        row = dict(
            source_record_id="x",
            group_id="g",
            split="valid",
            messages=[dict(role="user", content="same"), dict(role="assistant", content="old")],
        )
        new = copy.deepcopy(row)
        new["messages"][-1]["content"] = "new reference"
        assert_same_prompts([row], [new])
        new["messages"][0]["content"] = "different input"
        with self.assertRaisesRegex(AssertionError, "prompt changed"):
            assert_same_prompts([row], [new])


if __name__ == "__main__":
    unittest.main()

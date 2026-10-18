"""Reviewed-source semantics, corpus isolation, and explicit adapter lineage."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_gemma_labels import explicit_experience, extraction_role, grounded_skills


class ReviewedGemmaTests(unittest.TestCase):
    def test_new_score_gain_cannot_override_legacy_skill_regression(self):
        from scripts.compare_reviewed_gemma import validation_gates

        rule = json.loads(Path("configs/gemma_reviewed_protocol.json").read_text())["selection"]
        baseline = dict(
            selection_score=0.94, schema_validity=1.0, json_validity=1.0, skill_micro_f1=0.94
        )
        new = dict(baseline, selection_score=0.97)
        regressed = dict(baseline, skill_micro_f1=0.89)
        gates = validation_gates(baseline, new, baseline, regressed, rule)
        self.assertTrue(gates["new_score_gain"])
        self.assertFalse(gates["legacy_skill_guard"])
        self.assertFalse(all(gates.values()))

    def test_reviewed_protocol_refuses_a_second_training_trial(self):
        from scripts.clean_data import checksum
        from scripts.gemma_train import check_transition_budget

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "protocol.json"
            path.write_text('{"max_candidates":1}')
            transition = dict(path="protocol.json", sha256=checksum(path))
            plan = dict(resume=dict(data_transition=transition))
            check_transition_budget(plan, root)
            run = root / "outputs/training_logs/gemma_example"
            run.mkdir(parents=True)
            (run / "run.json").write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                check_transition_budget(plan, root)

    def test_experience_uses_visible_evidence_and_abstains_on_conflict(self):
        self.assertEqual(explicit_experience("Senior developer")[0], None)
        self.assertEqual(explicit_experience("Không yêu cầu kinh nghiệm")[0], 0)
        self.assertEqual(explicit_experience("Có 1–3 năm kinh nghiệm")[0], 1)
        self.assertEqual(
            explicit_experience("2 năm kinh nghiệm và 1 năm kinh nghiệm Python")[0], None
        )
        self.assertEqual(explicit_experience("kinh nghiệm từ 2 năm trở lên")[0], 2)

    def test_grounded_skill_spans_do_not_invent_prerequisites(self):
        skills, evidence = grounded_skills(
            "JavaScript, C++, C#, Spring Boot, React Native, RESTful API"
        )
        self.assertNotIn("Java", skills)
        self.assertNotIn("C", skills)
        self.assertNotIn("React", skills)
        self.assertIn("REST API", skills)
        self.assertEqual(evidence["React Native"], "React Native")
        self.assertEqual(grounded_skills("R&D; go to the office")[0], [])

    def test_ai_product_experience_does_not_relabel_an_app_developer(self):
        self.assertEqual(extraction_role("Kỹ Sư Lập Trình AI"), "ML Engineer")
        self.assertEqual(
            extraction_role("Developer có kinh nghiệm sản phẩm AI"), "Software Developer"
        )

    def test_review_is_not_human_gold_and_rejected_ids_do_not_train(self):
        from scripts.review_gemma_labels import REJECTED, ROOT
        from scripts.validate_sft import validate_corpus

        folder = ROOT / "data/annotation/gemma_v2.0.0"
        records = [json.loads(line) for line in (folder / "review.jsonl").read_text().splitlines()]
        self.assertEqual(len(records), 214)
        self.assertTrue(all(row["gold"] is None for row in records))
        self.assertFalse(any(row["status"] == "pending" for row in records))
        corpus = ROOT / "data/finetune_reviewed/v2.0.0"
        self.assertTrue(validate_corpus(corpus, strict=True)["ok"])
        actual = {
            int(row["source_record_id"].split(":")[1])
            for split in ["train", "valid", "test"]
            for line in (corpus / f"{split}.jsonl").read_text().splitlines()
            if (row := json.loads(line))["source_dataset"] == "tinixai_reviewed"
        }
        self.assertFalse(actual & set(REJECTED))
        self.assertEqual(len(actual), 201)

    def test_changed_corpus_requires_hash_pinned_transition(self):
        from scripts.clean_data import checksum
        from scripts.gemma_train import resume_metadata

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["parent", "new", "outputs/gemma_preparation"]:
                (root / name).mkdir(parents=True)
            weight = root / "parent/adapters.safetensors"
            weight.write_bytes(b"parent weights")
            corpus = root / "new/manifest.json"
            corpus.write_text('{"version":2}')
            config = dict(
                resume_adapter_file="parent/adapters.safetensors",
                num_layers=4,
                fine_tune_type="lora",
                lora_parameters={"rank": 8},
                data="new",
                learning_rate=1e-5,
                iters=501,
            )
            (root / "parent/adapter_config.json").write_text(json.dumps(config))
            (root / "parent/manifest.json").write_text(
                json.dumps(
                    dict(
                        adapter=dict(sha256=checksum(weight)),
                        sft_manifest_sha256="old-corpus",
                        base_revision="r1",
                        completed_iterations=100,
                    )
                )
            )
            (root / "outputs/gemma_preparation/weights.json").write_text('{"revision":"r1"}')
            with self.assertRaisesRegex(AssertionError, "transition protocol"):
                resume_metadata(config, root)
            protocol = dict(
                parent_adapter_file=config["resume_adapter_file"],
                parent_adapter_sha256=checksum(weight),
                parent_sft_manifest_sha256="old-corpus",
                new_sft_manifest_sha256=checksum(corpus),
                candidate_learning_rate=1e-5,
                candidate_iterations=501,
                old_test_policy="never_reopen",
            )
            path = root / "protocol.json"
            path.write_text(json.dumps(protocol))
            config["data_transition_protocol"] = "protocol.json"
            self.assertEqual(
                resume_metadata(config, root)["data_transition"]["sha256"], checksum(path)
            )
            corpus.write_text("tampered")
            with self.assertRaises(AssertionError):
                resume_metadata(config, root)


if __name__ == "__main__":
    unittest.main()

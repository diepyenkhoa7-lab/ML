"""Coordinator/checkpoint contract tests; these do not measure model quality."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from career_auto import checkpoints, coordinator
from career_auto.state import read, write


class ArrayWeights:
    """Serialization fixture only, never used as an AI model."""

    def __init__(self):
        self.value = np.array([1.0, 2.0], dtype="float32")

    def _save(self, path):
        with open(path, "wb") as stream:
            np.save(stream, self.value)

    def _load(self, path):
        with open(path, "rb") as stream:
            self.value = np.load(stream, allow_pickle=False)

    save_lora_weights = _save
    load_lora_weights = _load
    save_weights = _save
    load_weights = _load


class OptimizerCheckpointContracts(unittest.TestCase):
    def test_real_optimizer_slots_and_cursor_restore_without_training(self):
        import keras
        import tensorflow as tf

        optimizer = keras.optimizers.AdamW(2e-5)
        optimizer.build([tf.Variable([1.0, 2.0])])
        optimizer.iterations.assign(7)
        optimizer.variables[-1].assign([3.0, 4.0])
        backbone, head = ArrayWeights(), ArrayWeights()
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            cursor = dict(epoch=1, phase="language", next_index=24)
            identity = dict(config=dict(rank=8), source="immutable")
            checkpoints.save(run, backbone, head, optimizer, cursor, identity)
            optimizer.iterations.assign(0)
            optimizer.variables[-1].assign([0.0, 0.0])
            backbone.value[:] = 9
            restored = checkpoints.restore(run, backbone, head, optimizer, identity)
            self.assertEqual(restored, cursor)
            self.assertEqual(int(optimizer.iterations), 7)
            np.testing.assert_array_equal(optimizer.variables[-1].numpy(), [3.0, 4.0])
            np.testing.assert_array_equal(backbone.value, [1.0, 2.0])
            with self.assertRaises(ValueError):
                checkpoints.restore(run, backbone, head, optimizer, dict(source="changed"))
            latest = read(run / "checkpoints/latest.json")["directory"]
            (run / "checkpoints" / latest / "optimizer.npz").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                checkpoints.restore(run, backbone, head, optimizer, identity)


class CoordinatorContracts(unittest.TestCase):
    def test_reference_reload_precedes_validation_and_model_selection(self):
        state = {}
        coordinator.handle_finished_job(state, dict(action="validate_baseline"))
        self.assertEqual(state["status"], "check_reference")
        coordinator.handle_finished_job(state, dict(action="check_reference"))
        self.assertEqual(state["status"], "validate_reference")
        self.assertNotIn("best_run", state)

    def test_small_improvements_do_not_reset_patience(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = dict(consecutive_no_improvement=0)
            with patch.object(coordinator, "ROOT", root):
                for name, score in [("reference", 100.0), ("a", 99.5), ("b", 99.0)]:
                    write(root / name / "llm_history.json", [dict(selection_score=score)])
                    coordinator.record_candidate(state, name, 2e-5, reference=name == "reference")
            self.assertEqual(state["consecutive_no_improvement"], 2)
            self.assertEqual(state["best_run"], "b")

    def test_cli_default_patch_is_deferred_and_valid_python(self):
        original = Path("career_ai/__main__.py").read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "career_ai").mkdir()
            (root / "out").mkdir()
            target = root / "career_ai/__main__.py"
            target.write_text(original)
            with (
                patch.object(coordinator, "ROOT", root),
                patch.object(coordinator, "FOLDER", root / "out"),
            ):
                state = {}
                coordinator.install_validation_default(state)
            changed = target.read_text()
            compile(changed, str(target), "exec")
            self.assertIn('default="valid"', changed)
            self.assertIn("from career_auto.evaluation import evaluate", changed)
            self.assertTrue(state["validation_default_installed"])
        self.assertEqual(Path("career_ai/__main__.py").read_text(), original)

    def test_smoke_and_unauthorized_test_are_rejected_before_loading_model(self):
        from career_auto import evaluation

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            write(run / "llm.json", dict(limited_trial=True))
            with self.assertRaises(ValueError):
                evaluation.evaluate(run)
            write(run / "llm.json", dict(limited_trial=False))
            write(run / "state.json", dict(test_authorized=False))
            with patch.object(evaluation, "FOLDER", run), self.assertRaises(ValueError):
                evaluation.evaluate(run, split="test")


class ResumeSchedulingContracts(unittest.TestCase):
    def test_finished_epoch_restore_is_not_mid_epoch_resume_evidence(self):
        from career_auto.verify_smoke import resumed_mid_epoch

        finished = dict(
            restored=True,
            optimizer_iterations=4,
            cursor=dict(epoch=1, phase="numeric", next_index=0),
        )
        midpoint = dict(
            restored=True,
            optimizer_iterations=2,
            cursor=dict(epoch=0, phase="numeric", next_index=16),
        )
        self.assertFalse(resumed_mid_epoch([finished]))
        self.assertTrue(resumed_mid_epoch([midpoint, finished]))
        self.assertFalse(resumed_mid_epoch([dict(midpoint, restored=False)]))

    def _schedule(self, used=0, no_improvement=0, closed=False):
        from contextlib import nullcontext

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "outputs/auto_dev"
            policy = dict(
                dataset_manifest_sha256="fixed",
                max_additional_experiments=3,
                max_epochs=1,
                search_closed=closed,
                patience=2,
                experiments=[dict(id="low", rank=8, learning_rate=2e-5)],
            )
            state = dict(
                status="choose_next_trial",
                additional_experiments_used=used,
                consecutive_no_improvement=no_improvement,
                trials=[],
                best_run="outputs/reference",
                retries={},
            )
            write(root / "configs/auto_goal.json", policy)
            write(root / "data/tensorflow_v1/manifest.json", dict(raw={}))
            write(folder / "state.json", state)
            with (
                patch.object(coordinator, "ROOT", root),
                patch.object(coordinator, "FOLDER", folder),
                patch.object(coordinator, "STATE", folder / "state.json"),
                patch.object(coordinator, "lock", return_value=nullcontext()),
                patch("career_ai.data.digest", return_value="fixed"),
                patch.object(coordinator, "start") as start,
            ):
                result = coordinator.tick()
                arguments = start.call_args
                if arguments is not None:
                    self.assertEqual(read(folder / "low.config.json")["epochs"], 1)
            return result, arguments

    def test_smoke_is_scheduled_to_pause_after_two_real_optimizer_updates(self):
        state, arguments = self._schedule()
        self.assertEqual(state["additional_experiments_used"], 1)
        self.assertEqual(arguments.args[1], "smoke")
        self.assertEqual(arguments.args[2][-2:], ["--checkpoint-stop-after", "2"])
        self.assertTrue(arguments.kwargs["training"])

    def test_quota_or_patience_closes_search_without_starting_another_model(self):
        for used, patience in [(3, 0), (2, 2)]:
            state, arguments = self._schedule(used, patience)
            self.assertIsNone(arguments)
            self.assertEqual(state["status"], "finalize")
            self.assertTrue(state["test_authorized"])
            self.assertEqual(state["selected_run"], "outputs/reference")

    def test_explicit_user_selection_closes_search_before_unused_quota(self):
        state, arguments = self._schedule(closed=True)
        self.assertIsNone(arguments)
        self.assertEqual(state["additional_experiments_used"], 0)
        self.assertEqual(state["selected_run"], "outputs/reference")


class HandoffMetricContracts(unittest.TestCase):
    def test_final_checkpoint_reload_is_scheduled_before_test(self):
        from contextlib import nullcontext

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "outputs/auto_dev"
            write(
                root / "configs/auto_goal.json",
                dict(dataset_manifest_sha256="fixed", baseline_run="outputs/baseline"),
            )
            write(root / "data/tensorflow_v1/manifest.json", dict(raw={}))
            write(
                folder / "state.json",
                dict(status="finalize", selected_run="outputs/winner", final_step=0),
            )
            with (
                patch.object(coordinator, "ROOT", root),
                patch.object(coordinator, "FOLDER", folder),
                patch.object(coordinator, "STATE", folder / "state.json"),
                patch.object(coordinator, "lock", return_value=nullcontext()),
                patch("career_ai.data.digest", return_value="fixed"),
                patch.object(coordinator, "start") as start,
            ):
                coordinator.tick()
            self.assertEqual(start.call_args.args[1], "final_reload")
            self.assertEqual(start.call_args.args[2][0], "scripts/check_saved_run.py")

    def test_final_notebooks_select_explicit_artifacts_without_retraining(self):
        import nbformat

        from career_auto import notebook_handoff

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notebooks").mkdir()
            for source in Path("notebooks").glob("*.ipynb"):
                (root / "notebooks" / source.name).write_bytes(source.read_bytes())
            folder = root / "outputs/auto_dev"
            write(folder / "state.json", dict(selected_run="outputs/winner", final_step=4))
            with (
                patch.object(notebook_handoff, "ROOT", root),
                patch.object(notebook_handoff, "FOLDER", folder),
            ):
                notebook_handoff.prepare()
                notebook_handoff.prepare()
            for path in (root / "notebooks").glob("*.ipynb"):
                book = nbformat.read(path, as_version=4)
                for cell in book.cells:
                    if cell.cell_type == "code":
                        compile(cell.source, path.name, "exec")
                if path.name.startswith("04"):
                    code = "\n".join(c.source for c in book.cells)
                    self.assertNotIn("glob(", code)
                    self.assertIn("llm_test_metrics.json", code)
                    self.assertEqual(len(book.cells), 3)
                if path.name.startswith("03"):
                    self.assertIn("RUN_TRAINING=False", book.cells[-1].source)
                    self.assertIn("training_processes()", book.cells[-1].source)

    def test_extraction_fields_are_individual_and_nulls_do_not_inflate_known_accuracy(self):
        from career_auto.language_evaluation import evaluate_language

        examples = [
            dict(prompt="a", answer=dict(role="Backend", experience_years=None, skills=["python"])),
            dict(prompt="b", answer=dict(role="Backend", experience_years=5, skills=["sql"])),
        ]
        actual = [
            dict(role="Backend", experience_years=3, skills=["python"]),
            dict(role="Other", experience_years=5, skills=["sql"]),
        ]
        with patch("career_auto.language_evaluation.extract", side_effect=actual):
            result = evaluate_language(None, examples)
        self.assertEqual(result["field_accuracy_by_name"], dict(role=0.5, experience_years=0.5))
        self.assertEqual(result["known_field_samples"]["experience_years"], 1)
        self.assertEqual(result["known_field_accuracy"]["experience_years"], 1)
        self.assertIn("silver", result["label_quality"])

    def test_failed_generation_counts_as_failure_and_empty_eval_has_no_score(self):
        from career_auto.language_evaluation import evaluate_language

        item = dict(prompt="a", answer=dict(role="Backend", experience_years=3, skills=["python"]))
        with patch("career_auto.language_evaluation.extract", side_effect=ValueError("invalid")):
            result = evaluate_language(None, [item])
        self.assertEqual(result["json_schema_rate"], 0)
        self.assertEqual(result["skill_f1"], 0)
        self.assertEqual(result["field_accuracy_by_name"]["role"], 0)
        self.assertIsNone(evaluate_language(None, [])["skill_f1"])

    def test_report_refuses_to_finish_before_test_demo_and_notebooks(self):
        from career_auto import report

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for state in [
                dict(test_authorized=False, final_step=6),
                dict(test_authorized=True, final_step=5),
            ]:
                write(folder / "state.json", state)
                with patch.object(report, "FOLDER", folder), self.assertRaises(ValueError):
                    report.report()

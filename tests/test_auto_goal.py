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

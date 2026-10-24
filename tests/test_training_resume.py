"""Software lifecycle regression only: mocked Qwen, no gradient updates or AI score."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd

from career_auto.state import read, write


class CompletedCheckpointResume(unittest.TestCase):
    def test_completed_epoch_checkpoint_recreates_missing_history_without_training(self):
        import keras
        import tensorflow as tf

        from career_auto import training

        config = dict(rank=8, learning_rate=2e-5, epochs=1)
        frozen = dict(config=config, dataset="fixture", source={}, versions={})
        history = [dict(epoch=1, selection_score=0.5)]
        cursor = dict(
            epoch=1,
            phase="numeric",
            next_index=0,
            best=0.5,
            best_dir="best_epoch_1",
            history=history,
            language_updates=1,
        )
        model = SimpleNamespace(
            backbone=SimpleNamespace(
                enable_lora=Mock(), trainable_weights=[keras.Variable([1.0], name="fixture_lora")]
            )
        )
        frame = pd.DataFrame([dict(market="vietnam"), dict(market="international")])

        def restore(run, backbone, head, optimizer, identity):
            optimizer.iterations.assign(7)
            return cursor

        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            write(run / "lineage.json", dict(status="failed", **frozen))
            best = run / cursor["best_dir"]
            best.mkdir()
            for name in ["qwen.lora.h5", "salary_head.keras", "reload_probe.json"]:
                (best / name).write_bytes(b"software-fixture-not-model-weights")
            with (
                patch.object(training, "identity", return_value=frozen),
                patch.object(training, "qwen_load", return_value=model),
                patch.object(training, "load", return_value=frame),
                patch.object(training, "load_language", return_value=[]),
                patch.object(training, "tokenize", return_value={}),
                patch.object(training, "pooled", return_value=tf.zeros((1, 4))),
                patch.object(training.checkpoints, "restore", side_effect=restore),
                patch.object(training, "validation") as validation,
            ):
                training.train(config, run, resume=True)
            validation.assert_not_called()
            self.assertEqual(read(run / "llm_history.json"), history)
            self.assertEqual(read(run / "lineage.json")["status"], "completed")
            self.assertEqual(read(run / "llm.json")["selection_score"], 0.5)

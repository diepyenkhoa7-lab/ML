"""Plot contracts only; no AI-quality claim is made by these tests."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from career_auto import coordinator
from career_auto.charts import charts


class ChartContracts(unittest.TestCase):
    def test_distinct_observations_with_same_features_are_counted_separately(self):
        row = dict(
            market="vietnam", role="Backend", location="Hanoi", experience_years=3, skills="python"
        )
        frame = pd.DataFrame([dict(row, salary=20e6), dict(row, salary=30e6)])
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            charts(frame, folder)
            stats = pd.read_csv(folder / "vietnam_skill_income.csv")
            self.assertEqual(stats.iloc[0]["count"], 2)
            self.assertEqual(stats.iloc[0]["median"], 25e6)
            self.assertTrue(stats.iloc[0]["low_support"])
            self.assertEqual(len(list(folder.glob("*.png"))), 5)

    def test_chart_patch_is_deferred_idempotent_and_retains_original(self):
        current = Path("career_ai/charts.py").read_text()
        # Exercise migration even after the real checkout already uses the delegate.
        original = '"""Legacy chart fixture."""\n\ndef charts(frame, folder):\n    pass\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "career_ai").mkdir()
            folder = root / "out"
            folder.mkdir()
            target = root / "career_ai/charts.py"
            target.write_text(original)
            with (
                patch.object(coordinator, "ROOT", root),
                patch.object(coordinator, "FOLDER", folder),
            ):
                state = {}
                coordinator.install_analysis_charts(state)
                coordinator.install_analysis_charts(state)
            compile(target.read_text(), str(target), "exec")
            self.assertEqual(
                (folder / "legacy_charts_before_analysis_fix.py").read_text(), original
            )
            self.assertTrue(state["analysis_charts_installed"])
        self.assertEqual(Path("career_ai/charts.py").read_text(), current)

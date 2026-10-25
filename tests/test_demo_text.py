"""Software contract only: fake CLI output does not measure extraction quality."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from career_auto.demo import text_demo


class TextDemoContracts(unittest.TestCase):
    def test_requires_both_market_predictions_and_preserves_batch_output(self):
        profiles = [
            dict(
                market="vietnam",
                location="Hà Nội",
                role="Developer",
                experience_years=3,
                skills="python;sql",
                salary=999999,
            ),
            dict(
                market="international",
                location="Germany",
                role="Developer",
                experience_years=3,
                skills="python;sql",
                salary=999999,
            ),
        ]
        with tempfile.TemporaryDirectory() as directory, patch.object(sys, "argv", []):
            root = Path(directory)
            run, folder = root / "run", root / "demo"
            run.mkdir()
            folder.mkdir()
            (run / "predictions.json").write_text("[]")
            (run / "predictions.csv").write_text("original batch")

            def cli():
                rows = json.loads(Path(sys.argv[-1]).read_text())
                self.assertTrue(
                    all("salary" not in r and "999999" not in r["description"] for r in rows)
                )
                result = [
                    dict(
                        **r,
                        prediction=10,
                        model_version="fixture",
                        unit="VND/month" if r["market"] == "vietnam" else "USD/year",
                        error=None,
                    )
                    for r in rows
                ]
                (run / "predictions.json").write_text(json.dumps(result))
                (run / "predictions.csv").write_text("text output")

            result = text_demo(run, folder, profiles, cli)
            self.assertTrue(result["passed"])
            self.assertFalse(result["quality_metric"])
            self.assertEqual((run / "predictions.json").read_text(), "[]")
            self.assertEqual((run / "predictions.csv").read_text(), "original batch")
            self.assertEqual(len(json.loads((folder / "text_predictions.json").read_text())), 2)

            def failed_cli():
                (run / "predictions.json").write_text('[{"error":"invalid JSON"},{}]')

            with self.assertRaises(ValueError):
                text_demo(run, folder, profiles, failed_cli)

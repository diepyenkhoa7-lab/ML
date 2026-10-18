import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.services.gemma import availability, extract_cards
from scripts.gpu_lock import gpu_is_busy, gpu_lock


class GpuAvailabilityTests(unittest.TestCase):
    def test_probe_detects_evaluation_and_does_not_release_its_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gpu.lock"
            self.assertFalse(gpu_is_busy(path))
            with gpu_lock(path):
                self.assertTrue(gpu_is_busy(path))
                with self.assertRaises(ValueError):
                    with gpu_lock(path):
                        self.fail("Probe released another workload's lock")
            self.assertFalse(gpu_is_busy(path))

    def test_non_training_gpu_workload_is_reported_as_busy(self):
        with (
            patch(
                "backend.app.services.gemma.subprocess.run",
                return_value=subprocess.CompletedProcess([], 1, "", ""),
            ),
            patch("backend.app.services.gemma.gpu_is_busy", return_value=True),
        ):
            status = availability()
        self.assertFalse(status["training_active"])
        self.assertTrue(status["gpu_busy"])

    def test_busy_gpu_rejects_extraction_before_spawning_worker(self):
        with (
            patch(
                "backend.app.services.gemma.availability",
                return_value=dict(available=True, training_active=False, gpu_busy=True),
            ),
            patch("backend.app.services.gemma.subprocess.run") as spawn,
        ):
            with self.assertRaisesRegex(ValueError, "GPU đang đánh giá"):
                extract_cards(["card"])
            spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()

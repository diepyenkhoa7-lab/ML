"""Regressions at persistence, worker transport and execution boundaries; no ML training."""

import io
import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from openpyxl import Workbook

from backend.app.schemas import AnalysisRequest, JobState
from backend.app.services.contracts import GemmaLabel, digest, strict_json
from backend.app.services.data import read_table
from backend.app.services.gemma import extract_cards
from backend.app.services.salary import SalaryService
from backend.app.services.store import AppStore, JobBusyError
from scripts.gpu_lock import gpu_lock

LABEL = dict(
    role="Backend Developer",
    location="Hà Nội",
    experience_years=3,
    skills=["Python"],
    salary_min=None,
    salary_max=None,
    currency=None,
    salary_period=None,
)


class TransportTests(unittest.TestCase):
    def worker(self, command, **kwargs):
        request = json.loads(Path(command[command.index("--input") + 1]).read_text())
        payload = dict(
            schema_version="career.gemma.batch.v1",
            request_id=request["request_id"],
            items=[
                dict(
                    index=i,
                    input_sha256=digest(card),
                    value=LABEL,
                    raw_output=json.dumps(LABEL),
                    error=None,
                )
                for i, card in enumerate(request["cards"])
            ],
            provenance=dict(
                adapter="test",
                adapter_sha256="a" * 64,
                base_weight_sha256="b" * 64,
                system_prompt_sha256="c" * 64,
            ),
        )
        self.mutate(payload)
        Path(command[command.index("--output") + 1]).write_text(json.dumps(payload))
        return subprocess.CompletedProcess(command, 0, "worker stdout", "")

    def test_reject_missing_extra_reordered_and_wrong_request_results(self):
        mutations = [
            lambda p: p["items"].pop(),
            lambda p: p["items"].append(p["items"][0]),
            lambda p: p["items"].reverse(),
            lambda p: p.update(request_id="0" * 32),
            lambda p: p["items"][0].update(input_sha256="0" * 64),
        ]
        for mutate in mutations:
            self.mutate = mutate
            with (
                self.subTest(mutate=mutate),
                tempfile.TemporaryDirectory() as d,
                patch(
                    "backend.app.services.gemma.availability",
                    return_value=dict(available=True, training_active=False),
                ),
                patch("backend.app.services.gemma.subprocess.run", side_effect=self.worker),
            ):
                with self.assertRaisesRegex(ValueError, "sai hợp đồng"):
                    extract_cards(["first", "second"], audit_folder=d)
                self.assertTrue((Path(d) / "gemma_invalid_transport.txt").exists())
                self.assertEqual(
                    json.loads((Path(d) / "gemma_worker.json").read_text())["returncode"], 0
                )

    def test_valid_transport_retains_raw_output_without_repair(self):
        self.mutate = lambda p: None
        with (
            patch(
                "backend.app.services.gemma.availability",
                return_value=dict(available=True, training_active=False),
            ),
            patch(
                "backend.app.services.gemma.subprocess.run",
                side_effect=self.worker,
            ),
        ):
            batch = extract_cards(["first", "second"])
        self.assertEqual(len(batch["items"]), 2)
        self.assertEqual(batch["items"][0]["raw_output"], json.dumps(LABEL))

    def test_worker_failure_retains_stderr(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch(
                "backend.app.services.gemma.availability",
                return_value=dict(available=True, training_active=False),
            ),
            patch(
                "backend.app.services.gemma.subprocess.run",
                return_value=subprocess.CompletedProcess([], 7, "", "checksum mismatch"),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "không thực hiện"):
                extract_cards(["card"], audit_folder=d)
            diagnostic = json.loads((Path(d) / "gemma_worker.json").read_text())
            self.assertEqual(diagnostic["stderr"], "checksum mismatch")
            self.assertEqual(diagnostic["returncode"], 7)

    def test_label_does_not_coerce_or_repair_and_rejects_incoherent_salary(self):
        for value in [
            dict(LABEL, experience_years="3"),
            dict(LABEL, experience_years=True),
            dict(LABEL, salary_period="month"),
            dict(LABEL, extra="x"),
        ]:
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                GemmaLabel.model_validate(value)
        self.assertEqual(GemmaLabel.model_validate(LABEL).experience_years, 3)

    def test_json_and_xlsx_reject_ambiguous_headers_and_nonfinite_numbers(self):
        for value in ['[{"role":"a","role":"b"}]', '[{"x":NaN}]', '[{"x":Infinity}]']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                read_table(value.encode(), "x.json")
        workbook = Workbook()
        workbook.active.append(["role", "role"])
        workbook.active.append(["a", "b"])
        buffer = io.BytesIO()
        workbook.save(buffer)
        with self.assertRaisesRegex(ValueError, "trùng"):
            read_table(buffer.getvalue(), "x.xlsx")
        with self.assertRaises(ValueError):
            strict_json('{"a":1,"a":2}')


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = AppStore(self.directory.name)
        preview = self.store.ingest(b"role\nBackend Developer\n", "jobs.csv")
        self.options = AnalysisRequest(dataset_id=preview["dataset_id"], mapping={"role": "role"})

    def tearDown(self):
        self.store.pool.shutdown(wait=True)
        self.directory.cleanup()

    def test_tampered_and_legacy_datasets_cannot_reuse_old_provenance(self):
        path = self.store.folder(self.options.dataset_id) / "dataset.json"
        original = strict_json(path.read_text())
        self.assertEqual(self.store.load_dataset(self.options.dataset_id), original)
        for change in [
            lambda d: d["rows"][0].update(role="Accountant"),
            lambda d: d.pop("schema_version"),
        ]:
            changed = json.loads(json.dumps(original))
            change(changed)
            path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "nhập lại file"):
                self.store.submit(self.options)
        # Failed validation must release both admission slots.
        path.write_text(json.dumps(original))
        self.assertTrue(self.store.slots.acquire(blocking=False))
        self.assertTrue(self.store.slots.acquire(blocking=False))
        self.store.slots.release()
        self.store.slots.release()

    def test_bounded_queue_rejects_without_creating_orphan_and_releases_on_failure(self):
        entered, release = threading.Event(), threading.Event()

        def blocked(*args):
            entered.set()
            release.wait(10)
            raise ValueError("explicit failed worker")

        with patch("backend.app.services.store.analyze", side_effect=blocked):
            try:
                first = self.store.submit(self.options)
                self.assertTrue(entered.wait(2))
                second = self.store.submit(self.options)
                folders = set(self.store.root.iterdir())
                with self.assertRaises(JobBusyError):
                    self.store.submit(self.options)
                self.assertEqual(folders, set(self.store.root.iterdir()))
            finally:
                release.set()
            self.store.pool.shutdown(wait=True)
        self.assertEqual(self.store.state(first["id"])["status"], "failed")
        self.assertEqual(self.store.state(second["id"])["status"], "failed")
        self.assertTrue(self.store.slots.acquire(blocking=False))
        self.store.slots.release()

    def test_recovery_quarantines_corruption_preserves_completed_and_fails_orphans(self):
        for identifier, data in [
            ("a" * 32, "{"),
            ("b" * 32, JobState(id="b" * 32, status="queued", stage="q").model_dump_json()),
            (
                "c" * 32,
                JobState(id="c" * 32, status="completed", stage="ok", result={}).model_dump_json(),
            ),
        ]:
            folder = self.store.root / identifier
            folder.mkdir()
            (folder / "state.json").write_text(data)
        self.store.recover()
        self.assertEqual(self.store.state("a" * 32)["status"], "failed")
        self.assertEqual(self.store.state("b" * 32)["status"], "failed")
        self.assertEqual(self.store.state("c" * 32)["status"], "completed")
        self.assertEqual(
            next((self.store.root / ("a" * 32)).glob("state.corrupt.*.json")).read_text(), "{"
        )

    def test_description_only_requires_explicit_gemma(self):
        with self.assertRaisesRegex(ValueError, "bật Gemma"):
            self.store.submit(self.options.model_copy(update={"mapping": {"description": "role"}}))


class ModelEvidenceTests(unittest.TestCase):
    def test_skill_evidence_reproduces_original_fitted_pipeline(self):
        service = SalaryService()
        expected = pd.read_csv(
            "outputs/metrics/salary_bd9af2fa002caae8/ridge_skill_associations_train.csv"
        )
        actual = service.associations.set_index("skill").sort_index()
        expected = expected.set_index("skill").sort_index()
        pd.testing.assert_frame_equal(
            actual[["train_rows", "coefficient_vnd"]],
            expected[["train_rows", "coefficient_vnd"]],
            check_exact=False,
        )
        self.assertTrue(service.associations.train_rows.ge(5).all())

    def test_changed_train_fails_before_advice(self):
        original = Path.read_bytes

        def modified(path):
            value = original(path)
            return value + b"\n" if path.as_posix().endswith("vn_developer/train.csv") else value

        with patch.object(Path, "read_bytes", modified):
            with self.assertRaisesRegex(ValueError, "Train snapshot checksum mismatch"):
                SalaryService()

    def test_training_plan_stays_available_but_busy_confirmed_launch_never_spawns(self):
        from scripts import gemma_train

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            lock = root / "gpu.lock"
            with (
                patch.object(gemma_train, "ROOT", root),
                patch.object(gemma_train, "build_plan", return_value={"config": {}}),
                patch.object(gemma_train, "gpu_lock", side_effect=lambda: gpu_lock(lock)),
                patch("scripts.gemma_train.subprocess.Popen") as spawn,
                patch("builtins.print"),
                gpu_lock(lock),
            ):
                self.assertEqual(gemma_train.main([]), 0)
                with self.assertRaisesRegex(ValueError, "GPU Gemma"):
                    gemma_train.main(["--confirm-training"])
                spawn.assert_not_called()
                self.assertFalse((root / "outputs/training_logs").exists())

    def test_gpu_lock_rejects_overlap_and_releases_on_exception(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "gpu.lock"
            with self.assertRaisesRegex(RuntimeError, "test failure"):
                with gpu_lock(path):
                    with self.assertRaisesRegex(ValueError, "GPU Gemma"):
                        with gpu_lock(path):
                            self.fail("Two managed workloads acquired the GPU")
                    raise RuntimeError("test failure")
            with gpu_lock(path):
                pass


if __name__ == "__main__":
    unittest.main()

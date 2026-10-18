import tempfile
import unittest

from backend.app.services.salary import salary_service
from backend.app.services.store import AppStore


class DemoProvenanceTests(unittest.TestCase):
    def test_demo_records_the_actual_active_training_model(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AppStore(directory)
            try:
                preview = store.demo()
                self.assertIn(salary_service().experiment, preview["provenance"])
                self.assertIn("không phải holdout", preview["provenance"])
                self.assertEqual(preview["row_count"], min(48, len(salary_service().train)))
            finally:
                store.pool.shutdown(wait=True)


if __name__ == "__main__":
    unittest.main()

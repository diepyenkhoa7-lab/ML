"""Inspect actual worker liveness as well as persisted progress, using stdlib only."""

import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
result = {}
for name, relative in [
    ("worker", "outputs/background_status.json"),
    ("environment", ".cache/tf_environment_status.json"),
    ("pipeline", "outputs/latest_pipeline.json"),
]:
    path = root / relative
    if path.exists():
        result[name] = json.loads(path.read_text())
worker = result.get("worker", {})
alive = False
if worker.get("pid"):
    try:
        os.kill(worker["pid"], 0)
        alive = True
    except PermissionError:
        alive = None
    except ProcessLookupError:
        pass
result["worker_alive"] = alive
if alive is None:
    result["effective_status"] = "liveness_unverified"
elif not alive and worker.get("status") not in [None, "completed", "failed", "interrupted"]:
    result["effective_status"] = "interrupted"
else:
    result["effective_status"] = worker.get("status", "not_started")
print(json.dumps(result, indent=2))

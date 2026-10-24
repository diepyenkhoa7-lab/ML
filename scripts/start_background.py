"""Start one detached training worker without tying it to a terminal session."""

import json
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
(root / ".cache").mkdir(exist_ok=True)
status_file = root / "outputs/background_status.json"
if status_file.exists():
    previous = json.loads(status_file.read_text())
    if previous.get("status") not in ["completed", "failed", "interrupted"]:
        try:
            os.kill(previous["pid"], 0)
        except PermissionError:
            raise SystemExit(
                "Cannot verify the existing worker; inspect it before starting another"
            )
        except ProcessLookupError:
            pass
        else:
            raise SystemExit(
                "A training worker is already alive; inspect outputs/background_status.json"
            )
with (root / ".cache/background_stdout.log").open("a") as out:
    with (root / ".cache/background_stderr.log").open("a") as err:
        worker = subprocess.Popen(
            [str(root / ".venv-tf/bin/python"), str(root / "scripts/run_background.py")],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
(root / ".cache/background.pid").write_text(str(worker.pid) + "\n")
print("Started detached worker", worker.pid)

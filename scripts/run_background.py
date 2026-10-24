"""One-shot macOS launchd entry point: finish environment/download, then train."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state_file = root / "outputs/background_status.json"
state_file.parent.mkdir(exist_ok=True)
state = dict(started_at=datetime.now(UTC).isoformat(), pid=os.getpid())


def status(value, **fields):
    state.update(status=value, updated_at=datetime.now(UTC).isoformat(), **fields)
    state_file.write_text(json.dumps(state, indent=2) + "\n")


try:
    status("preparing_environment_and_weights")
    with (root / ".cache/qwen_background.log").open("a") as log:
        downloader = subprocess.Popen(
            [str(root / ".venv/bin/python"), "scripts/download_qwen_ranges.py"],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        status("preparing_environment_and_weights", downloader_pid=downloader.pid)
        if not (root / ".cache/tf_environment_ready.json").exists():
            subprocess.run(
                [sys.executable, "scripts/bootstrap_environment.py"], cwd=root, check=True
            )
        status("running_training_pipeline")
        pipeline = subprocess.Popen([sys.executable, "scripts/run_training_pipeline.py"], cwd=root)
        status("running_training_pipeline", pipeline_pid=pipeline.pid)
        # Detect a failed downloader while the numeric baseline is still running.
        while pipeline.poll() is None:
            try:
                pipeline.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if downloader.poll() is not None and downloader.returncode != 0:
                    pipeline.terminate()
                    pipeline.wait()
                    raise RuntimeError(f"Qwen download failed: exit {downloader.returncode}")
        if pipeline.returncode != 0:
            raise RuntimeError(f"Training pipeline failed: exit {pipeline.returncode}")
        downloader.wait()
        if downloader.returncode != 0:
            raise RuntimeError("Weight downloader failed")
    status("completed")
except BaseException as exc:
    if "downloader" in globals() and downloader.poll() is None:
        downloader.terminate()
        downloader.wait()
    status("failed", error=f"{type(exc).__name__}: {exc}")
    raise

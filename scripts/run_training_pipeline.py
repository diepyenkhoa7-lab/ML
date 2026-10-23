"""Run real experiments only after dependencies and pinned pretrained weights are ready."""

import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
control = root / "outputs" / ("pipeline_" + run_id)
control.mkdir(parents=True, exist_ok=False)
os.environ["KERAS_BACKEND"] = "tensorflow"
os.environ["MPLCONFIGDIR"] = str(root / ".cache/matplotlib")
os.environ["HF_HOME"] = str(root / ".cache/huggingface")
status = dict(status="running", started_at=datetime.now(UTC).isoformat())


def phase(name):
    status.update(phase=name, updated_at=datetime.now(UTC).isoformat())
    (control / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    (root / "outputs/latest_pipeline.json").write_text(
        json.dumps(dict(directory=str(control.relative_to(root)), **status), indent=2) + "\n"
    )
    print(name, flush=True)


def execute(name, arguments):
    phase(name)
    with (control / f"{name}.log").open("w") as log:
        subprocess.run(
            [sys.executable, *arguments], cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True
        )


try:
    phase("waiting_for_environment")
    deadline = time.monotonic() + 10800
    while not (root / ".cache/tf_environment_ready.json").exists():
        environment_status = root / ".cache/tf_environment_status.json"
        if environment_status.exists():
            state = json.loads(environment_status.read_text())
            if state["status"] == "failed":
                raise RuntimeError(state["error"])
        if time.monotonic() > deadline:
            raise TimeoutError("Environment not ready after three hours")
        time.sleep(10)
    if importlib.util.find_spec("tensorflow") is None:
        raise RuntimeError("Environment ready marker exists but TensorFlow is unavailable")
    execute("compatibility", ["scripts/check_tensorflow.py"])
    baseline = root / "outputs" / ("baseline_" + run_id)
    execute("train_baseline", ["-m", "career_ai", "train-baseline", "--run", str(baseline)])
    execute(
        "evaluate_baseline",
        ["-m", "career_ai", "evaluate", "--model", "baseline", "--run", str(baseline)],
    )
    execute("notebooks_baseline", ["scripts/execute_notebooks.py"])
    phase("waiting_for_qwen_weights")
    deadline = time.monotonic() + 86400
    while not json.loads((root / "configs/qwen_source.json").read_text()).get("download_complete"):
        if time.monotonic() > deadline:
            raise TimeoutError("Qwen download not complete after 24 hours")
        time.sleep(10)
    smoke = root / "outputs" / ("qwen_smoke_" + run_id)
    execute(
        "qwen_smoke",
        ["-m", "career_ai", "train-llm", "--run", str(smoke), "--epochs", "1", "--limit", "20"],
    )
    execute(
        "qwen_reload_inference",
        ["-m", "career_ai", "predict", "--run", str(smoke), "--input", "data/profiles_demo.json"],
    )
    qwen = root / "outputs" / ("qwen_" + run_id)
    execute(
        "train_qwen_full", ["-m", "career_ai", "train-llm", "--run", str(qwen), "--epochs", "2"]
    )
    execute("evaluate_qwen", ["-m", "career_ai", "evaluate", "--run", str(qwen), "--language-eval"])
    execute(
        "analyze",
        ["-m", "career_ai", "analyze", "--run", str(qwen), "--input", "data/profiles_demo.json"],
    )
    execute(
        "advise",
        ["-m", "career_ai", "advise", "--run", str(qwen), "--input", "data/profiles_demo.json"],
    )
    execute("notebooks_final", ["scripts/execute_notebooks.py"])
    status["status"] = "completed"
    phase("completed")
except BaseException as exc:
    status.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    phase("failed")
    raise

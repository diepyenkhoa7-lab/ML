"""Finish an existing dependency installation, then verify and lock the new environment."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
installer_pid = int(sys.argv[1])
control = root / ".cache/tf_environment_status.json"
control.parent.mkdir(exist_ok=True)


def status(state, **extra):
    control.write_text(json.dumps(dict(status=state, **extra), indent=2) + "\n")


try:
    status("waiting_for_existing_installer")
    deadline = time.monotonic() + 7200
    while True:
        try:
            os.kill(installer_pid, 0)
        except ProcessLookupError:
            break
        if time.monotonic() > deadline:
            raise TimeoutError("Dependency installation exceeded two hours")
        time.sleep(10)
    status("finishing_requirements")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=root, check=True
    )
    subprocess.run([sys.executable, "-m", "pip", "check"], cwd=root, check=True)
    status("checking_cpu")
    with (root / ".cache/tf_cpu_check.log").open("w") as log:
        subprocess.run(
            [sys.executable, "scripts/check_tensorflow.py"],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    status("checking_metal")
    selection = "CPU"
    with (root / ".cache/tf_metal_check.log").open("w") as log:
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "tensorflow-metal==1.2.0"],
            cwd=root,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        metal = (
            subprocess.run(
                [sys.executable, "scripts/check_tensorflow.py", "--device", "gpu"],
                cwd=root,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            if install.returncode == 0
            else None
        )
    if metal is not None and metal.returncode == 0:
        selection = "Metal GPU (tiny Qwen compatibility passed; pretrained still pending)"
    else:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "tensorflow-metal"],
            cwd=root,
            check=True,
        )
        subprocess.run([sys.executable, "scripts/check_tensorflow.py"], cwd=root, check=True)
    lock = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], cwd=root)
    (root / "requirements-lock-tf-macos-arm64.txt").write_bytes(lock)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--prefix",
            str(root / ".venv-tf"),
            "--name",
            "career-ai-tf",
            "--display-name",
            "Python (Career AI TensorFlow)",
        ],
        cwd=root,
        check=True,
    )
    status("ready", device_selection=selection)
    (root / ".cache/tf_environment_ready.json").write_text(control.read_text())
except BaseException as exc:
    status("failed", error=f"{type(exc).__name__}: {exc}")
    raise

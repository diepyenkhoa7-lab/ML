"""Execute salary notebooks with a durable transcript; never starts Gemma training."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", choices=["01_eda", "02_salary_models"])
    args = parser.parse_args()
    names = [args.notebook] if args.notebook else ["01_eda", "02_salary_models"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = ROOT / "outputs/training_logs" / ("salary_" + stamp)
    folder.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key, value in {
        "IPYTHONDIR": ".cache/ipython",
        "JUPYTER_RUNTIME_DIR": ".cache/jupyter/runtime",
        "MPLCONFIGDIR": ".cache/matplotlib",
    }.items():
        env[key] = str(ROOT / value)
    report = {"kind": "salary_notebooks", "gemma_training": False, "runs": []}
    with (folder / "console.log").open("w") as log:
        for name in names:
            command = [
                sys.executable,
                "-m",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                str(ROOT / "notebooks" / f"{name}.ipynb"),
                "--output",
                f"{name}.executed.ipynb",
                "--output-dir",
                str(folder),
                "--ExecutePreprocessor.timeout=900",
                "--ExecutePreprocessor.kernel_name=it-career-insight",
            ]
            entry = {"command": command, "started_at_utc": datetime.now(timezone.utc).isoformat()}
            print(f"Running {name}; log: {folder}", flush=True)
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in process.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
            entry.update(
                returncode=process.wait(), finished_at_utc=datetime.now(timezone.utc).isoformat()
            )
            report["runs"].append(entry)
            (folder / "run.json").write_text(json.dumps(report, indent=2) + "\n")
            if entry["returncode"]:
                raise SystemExit(entry["returncode"])
    print(f"Completed. Evidence: {folder}", flush=True)


if __name__ == "__main__":
    main()

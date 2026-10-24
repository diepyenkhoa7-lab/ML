"""Check actual persisted predictions against values captured before saving."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--run", type=Path, required=True)
parser.add_argument("--model", choices=["baseline", "llm"], required=True)
args = parser.parse_args()
if args.model == "llm" and args.run.name.startswith("qwen_smoke"):
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("check_qwen_pretrained.py"))], check=True
    )
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def check():
    import numpy as np
    import pandas as pd

    from career_ai.models import predict

    probe = json.loads((args.run / "reload_probe.json").read_text())
    values = predict(pd.DataFrame(probe["profiles"]), args.run, args.model)
    np.testing.assert_allclose(values, probe["predictions"], rtol=1e-5, atol=1e-3)
    (args.run / "fresh_process_reload.json").write_text(
        json.dumps(
            dict(
                passed=True,
                profiles=len(values),
                rtol=1e-5,
                model=args.model,
            )
        )
        + "\n"
    )
    print("Fresh-process prediction parity passed", flush=True)


check()

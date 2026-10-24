"""Require a genuine mid-epoch optimizer restore before full training is allowed."""

import argparse
import subprocess
import sys
from pathlib import Path

from .state import ROOT, read, write


def resumed_mid_epoch(events):
    return any(
        event.get("restored")
        and event.get("optimizer_iterations") == 2
        and event.get("cursor", {}).get("epoch") == 0
        and event.get("cursor", {}).get("phase") == "numeric"
        and event.get("cursor", {}).get("next_index") == 16
        for event in events
    )


def verify(run):
    if not read(run / "weight_update_check.json").get("actual_lora_changed"):
        raise ValueError("No actual LoRA weight update was verified")
    if not resumed_mid_epoch(read(run / "resume_events.json")):
        raise ValueError("Smoke did not restore its mid-epoch optimizer checkpoint")
    if read(run / "lineage.json")["status"] != "completed":
        raise ValueError("Resumed smoke did not finish")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/check_saved_run.py"),
            "--model",
            "llm",
            "--run",
            str(run),
        ],
        cwd=ROOT,
        check=True,
    )
    write(
        run / "smoke_acceptance.json",
        dict(
            actual_lora_update=True,
            mid_epoch_optimizer_resume=True,
            completed_after_resume=True,
            fresh_process_prediction_parity=True,
            quality_metric=False,
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    verify(parser.parse_args().run)

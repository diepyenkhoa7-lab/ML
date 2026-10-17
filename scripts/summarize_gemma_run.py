"""Verify a completed Gemma trial and export its observed losses and adapter manifest."""

import argparse
import csv
import json
import math
import os
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    folder = (ROOT / args.run).resolve()
    record = json.loads((folder / "run.json").read_text())
    assert record["status"] == "completed" and record["returncode"] == 0
    config = json.loads((ROOT / "data/finetune/manifest.json").read_text())
    import yaml

    runtime = yaml.safe_load((folder / "config.yaml").read_text())
    adapter = Path(runtime["adapter_path"])
    plain = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", (folder / "console.log").read_text())
    events = []
    for line in plain.splitlines():
        match = re.match(r"^\s*(\d+)\s+(?:(val)\s+)?([\d.]+)(?:\s|$)", line)
        if match:
            iteration, validation, loss = match.groups()
            value = float(loss)
            assert math.isfinite(value)
            events.append(
                dict(
                    iteration=int(iteration),
                    kind="valid" if validation else "train",
                    loss_rounded_to_3dp=value,
                )
            )
    train = [e for e in events if e["kind"] == "train"]
    valid = [e for e in events if e["kind"] == "valid"]
    assert train and valid and train[-1]["iteration"] == runtime["iters"]
    weights = adapter / "adapters.safetensors"
    with weights.open("rb") as stream:
        length = struct.unpack("<Q", stream.read(8))[0]
        header = json.loads(stream.read(length))
    tensors = {k: v for k, v in header.items() if k != "__metadata__"}
    end = max(v["data_offsets"][1] for v in tensors.values())
    assert weights.stat().st_size == 8 + length + end
    adapter_manifest = {
        "base_model": "google/gemma-4-E4B-it",
        "base_revision": json.loads((ROOT / "outputs/gemma_preparation/weights.json").read_text())[
            "revision"
        ],
        "run": str(folder.relative_to(ROOT)),
        "config_sha256": checksum(folder / "config.yaml"),
        "sft_manifest_sha256": checksum(ROOT / "data/finetune/manifest.json"),
        "data_quality": config["quality"],
        "completed_iterations": runtime["iters"],
        "selection": "predeclared final 100-step trial; not selected using test",
        "adapter": {
            "path": str(weights.relative_to(ROOT)),
            "bytes": weights.stat().st_size,
            "sha256": checksum(weights),
            "tensors": len(tensors),
        },
        "adapter_config_sha256": checksum(adapter / "adapter_config.json"),
        "training_completed": True,
        "human_confirmation": "User explicitly replied: xac nhan",
    }
    (adapter / "manifest.json").write_text(
        json.dumps(adapter_manifest, ensure_ascii=False, indent=2) + "\n"
    )
    with (folder / "loss_history.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=["iteration", "kind", "loss_rounded_to_3dp"])
        writer.writeheader()
        writer.writerows(events)
    summary = {
        "status": "completed",
        "iterations": runtime["iters"],
        "gemma_training_started": True,
        "human_confirmation_received": True,
        "run": str(folder.relative_to(ROOT)),
        "adapter_manifest": str((adapter / "manifest.json").relative_to(ROOT)),
        "first_train_loss": train[0]["loss_rounded_to_3dp"],
        "last_train_loss": train[-1]["loss_rounded_to_3dp"],
        "first_validation_loss": valid[0]["loss_rounded_to_3dp"],
        "last_validation_loss": valid[-1]["loss_rounded_to_3dp"],
        "validation_batches_per_event": runtime["val_batches"],
        "validation_timing": "MLX measures before optimizer update at the displayed iteration",
        "loss_precision": "rounded to 3 decimals in console; not extraction accuracy",
        "test_used": False,
    }
    (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "outputs/gemma_preparation/training_status.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for label, values in [("Train", train), ("Validation (5 batches)", valid)]:
        ax.plot(
            [e["iteration"] for e in values],
            [e["loss_rounded_to_3dp"] for e in values],
            marker="o",
            label=label,
        )
    ax.set(title="Gemma LoRA trial: observed loss", xlabel="Displayed iteration", ylabel="Loss")
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "loss_curve.png", dpi=150)
    plt.close(fig)
    (folder / "REPORT.md").write_text(
        f"# Gemma trial — {folder.name}\n\n"
        f"Completed {runtime['iters']} iterations; rank 8 / 4 layers / batch 1 / context 1024.\n"
        f"Train loss: {summary['first_train_loss']} → {summary['last_train_loss']}.\n"
        f"Validation loss: {summary['first_validation_loss']} → {summary['last_validation_loss']} "
        "on 5 validation batches per event (before the displayed optimizer update).\n\n"
        "Losses are rounded console observations, not extraction accuracy. Test was not used.\n"
        "Labels are silver job-card fields, not independently reviewed gold.\n"
        f"Adapter: `{adapter_manifest['adapter']['path']}`.\n"
        "Full config, console, loss CSV, curve and checksums are stored with this run.\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

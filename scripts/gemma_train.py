"""Prepare a Gemma training plan; launch only with an explicit human-confirmed flag."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.gpu_lock import gpu_lock  # noqa: E402
from scripts.validate_sft import validate_corpus  # noqa: E402


def resume_metadata(config, root=ROOT):
    root = root.resolve()
    value = config.get("resume_adapter_file")
    if not value:
        return None
    path = (root / value).resolve()
    manifest = json.loads((path.parent / "manifest.json").read_text())
    previous = json.loads((path.parent / "adapter_config.json").read_text())
    assert checksum(path) == manifest["adapter"]["sha256"], "Parent adapter checksum mismatch"
    for key in ["num_layers", "fine_tune_type", "lora_parameters"]:
        assert config[key] == previous[key], f"Incompatible resumed adapter: {key}"
    assert manifest["sft_manifest_sha256"] == checksum(
        root / config.get("data", "data/finetune") / "manifest.json"
    )
    evidence = json.loads((root / "outputs/gemma_preparation/weights.json").read_text())
    assert manifest["base_revision"] == evidence["revision"]
    return {
        "path": str(path.relative_to(root)),
        "sha256": manifest["adapter"]["sha256"],
        "parent_total_optimizer_steps": manifest.get(
            "total_optimizer_steps", manifest["completed_iterations"]
        ),
        "mode": "adapter_weights_only_optimizer_reinitialized",
    }


def build_plan(config_path):
    config = yaml.safe_load(config_path.read_text())
    model = ROOT / config["model"]
    data = ROOT / config["data"]
    strict = data.resolve() != (ROOT / "data/examples/finetune").resolve()
    result = validate_corpus(data, strict=strict)
    if not result["ok"]:
        raise ValueError(result["errors"])
    evidence = json.loads((ROOT / "outputs/gemma_preparation/weights.json").read_text())
    assert evidence["official_checksum_match"]
    assert (model / "model.safetensors").stat().st_size == evidence["weights"][model.name]["bytes"]
    assert (model / "manifest.json").is_file()
    if strict:
        manifest = json.loads((data / "manifest.json").read_text())
        assert config["max_seq_length"] >= max(
            item["max_tokens"] for item in manifest["splits"].values()
        ), "Would truncate SFT samples"
    assert config["mask_prompt"] and config["train"] and config["fine_tune_type"] == "lora"
    return {
        "status": "awaiting_human_confirmation",
        "gemma_training_started": False,
        "config": config,
        "config_sha256": checksum(config_path),
        "resume": resume_metadata(config),
        "corpus_validation": result,
        "weight_evidence": "outputs/gemma_preparation/weights.json",
        "weight_check": "recorded official SHA256 verified; current size checked; rehash on launch",
        "expected_outputs": [
            "adapters/gemma-jobs/<run_id>/adapters.safetensors",
            "adapters/gemma-jobs/<run_id>/adapter_config.json",
            "outputs/training_logs/gemma_<run_id>/console.log",
            "outputs/training_logs/gemma_<run_id>/run.json",
        ],
        "limits": [
            "Silver job-card labels, not human gold or full original ads",
            "Training compatibility, throughput and adapter quality not yet verified",
            "Loss is not extraction accuracy; evaluate JSON validity, field accuracy and Skill F1",
            "Do not tune using test; compare base and fixed adapter on test after validation",
        ],
        "launch_after_user_confirmation_only": (
            f".venv/bin/python scripts/gemma_train.py --config "
            f"{config_path.relative_to(ROOT)} --confirm-training"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/gemma_train.yaml"))
    parser.add_argument(
        "--confirm-training",
        action="store_true",
        help="Use ONLY after the human approves this plan",
    )
    parser.add_argument("--confirmation-note", help="Record the user's explicit training request")
    parser.add_argument(
        "--summarize", action="store_true", help="Verify/export losses after success"
    )
    args = parser.parse_args(argv)
    path = (ROOT / args.config).resolve()
    plan = build_plan(path)
    destination = ROOT / "outputs/gemma_preparation" / f"{path.stem}_plan.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    if not args.confirm_training:
        print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
        print("PLAN ONLY. No Gemma training started. Await explicit user confirmation.")
        return 0
    with gpu_lock():
        return train(plan, args)


def train(plan, args):
    weight = ROOT / plan["config"]["model"] / "model.safetensors"
    evidence = json.loads((ROOT / plan["weight_evidence"]).read_text())
    assert checksum(weight) == evidence["weights"][weight.parent.name]["sha256"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = ROOT / "outputs/training_logs" / f"gemma_{stamp}"
    log_dir.mkdir(parents=True, exist_ok=False)
    config = dict(plan["config"])
    config["adapter_path"] = str(ROOT / "adapters/gemma-jobs" / stamp)
    config["model"], config["data"] = str(ROOT / config["model"]), str(ROOT / config["data"])
    if config.get("resume_adapter_file"):
        config["resume_adapter_file"] = str((ROOT / config["resume_adapter_file"]).resolve())
    runtime_config = log_dir / "config.yaml"
    runtime_config.write_text(yaml.safe_dump(config, sort_keys=False))
    command = [sys.executable, "-u", "-m", "mlx_lm", "lora", "--config", str(runtime_config)]
    record = dict(
        plan,
        status="running",
        gemma_training_started=True,
        command=command,
        human_confirmation_received=True,
        human_confirmation_text=args.confirmation_note,
        started_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    record_path = log_dir / "run.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(
        f"REAL TRAINING: {config['iters']} iterations; data={config['data']}; "
        f"log={log_dir}; adapter={config['adapter_path']}",
        flush=True,
    )
    with (log_dir / "console.log").open("w") as log:
        process = subprocess.Popen(
            command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
            code = process.wait()
        except BaseException:
            process.terminate()
            process.wait()
            record.update(status="interrupted")
            record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
            raise
    record.update(
        status="completed" if code == 0 else "failed",
        returncode=code,
        finished_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    if code == 0 and args.summarize:
        from scripts.summarize_gemma_run import main as summarize

        summarize(["--run", str(log_dir.relative_to(ROOT))])
    return code


if __name__ == "__main__":
    raise SystemExit(main())

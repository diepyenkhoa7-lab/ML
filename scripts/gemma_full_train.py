"""Prepare all available extraction JSONL and train complete epochs only when explicitly invoked."""

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.gemma_train import main as train_main  # noqa: E402
from scripts.validate_sft import validate_corpus  # noqa: E402

FULL_DATA = Path("data/finetune_full/v1.0.0")


def epoch_schedule(rows, batch_size, epochs):
    if min(rows, batch_size, epochs) < 1:
        raise ValueError("Rows, batch size and epochs must be positive")
    if rows % batch_size:
        raise ValueError(
            "MLX drops an incomplete final batch; use a batch size dividing train rows"
        )
    return {
        "train_examples": rows,
        "batch_size": batch_size,
        "epochs": epochs,
        "steps_per_epoch": rows // batch_size,
        "iterations": epochs * (rows // batch_size),
    }


def prepare_full_corpus():
    source = ROOT / "data/finetune"
    result = validate_corpus(source, strict=True)
    if not result["ok"]:
        raise ValueError(result["errors"])
    destination = ROOT / FULL_DATA
    destination.mkdir(parents=True, exist_ok=True)
    for name in ["train.jsonl", "valid.jsonl", "test.jsonl", "manifest.json"]:
        original, exported = source / name, destination / name
        if exported.exists():
            assert checksum(exported) == checksum(original), "Preserve/version modified full corpus"
        else:
            shutil.copyfile(original, exported)
    ready = validate_corpus(destination, strict=True)
    assert ready["ok"], ready["errors"]
    manifest = json.loads((destination / "manifest.json").read_text())
    report = {
        "source": "data/finetune",
        "dataset": str(FULL_DATA),
        "counts": ready["counts"],
        "train_split_only": True,
        "validation_and_test_excluded_from_gradients": True,
        "full_definition": (
            "Every train JSONL example once per epoch; not all raw CSVs or full-parameter tuning"
        ),
        "label_quality": "silver_source_fields",
        "source_records": {
            part: item["source_records"] for part, item in manifest["splits"].items()
        },
        "files": {
            name: checksum(destination / name)
            for name in ["train.jsonl", "valid.jsonl", "test.jsonl", "manifest.json"]
        },
    }
    (destination / "full_training.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument(
        "--confirm-training",
        action="store_true",
        help="Explicit full-training command; make gemma-adapter supplies this flag",
    )
    args = parser.parse_args(argv)
    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    corpus = prepare_full_corpus()
    config = yaml.safe_load((ROOT / "configs/gemma_full.yaml").read_text())
    schedule = epoch_schedule(corpus["counts"]["train"], config["batch_size"], args.epochs)
    config.update(
        data=str(FULL_DATA),
        iters=schedule["iterations"],
        steps_per_eval=schedule["steps_per_epoch"],
    )
    prep = ROOT / "outputs/gemma_preparation"
    runtime = prep / f"gemma_full_{args.epochs}epochs.yaml"
    runtime.write_text(yaml.safe_dump(config, sort_keys=False))
    plan = dict(
        schedule,
        dataset=corpus,
        config=str(runtime.relative_to(ROOT)),
        training_started=False,
        mode="full_dataset_lora_epochs",
        start_from="official base model; no existing adapter overwritten",
        human_confirmation="Explicit invocation of make gemma-adapter starts training",
    )
    (prep / f"gemma_full_{args.epochs}epochs_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    )
    if args.confirm_training:
        print(
            f"TRAIN THAT: {args.epochs} epoch(s), {schedule['train_examples']} train examples, "
            f"{schedule['iterations']} optimizer steps. Validation/test stay separate.",
            flush=True,
        )
    else:
        print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    command = ["--config", str(runtime.relative_to(ROOT))]
    if args.confirm_training:
        command += [
            "--confirm-training",
            "--summarize",
            "--confirmation-note",
            f"User invoked make gemma-adapter EPOCHS={args.epochs}",
        ]
    return train_main(command)


if __name__ == "__main__":
    raise SystemExit(main())

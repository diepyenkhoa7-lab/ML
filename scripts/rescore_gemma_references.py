"""Reuse cached generation only when source prompts and recorded hashes match."""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.evaluate_gemma import score  # noqa: E402


def assert_same_prompts(original, corrected):
    assert len(original) == len(corrected), "Reference size changed"
    for old, new in zip(original, corrected, strict=True):
        for field in ["source_record_id", "group_id", "split"]:
            assert old[field] == new[field], f"Source/group/order changed: {field}"
        assert old["messages"][:-1] == new["messages"][:-1], "Generation prompt changed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--old-data", type=Path, required=True)
    parser.add_argument("--new-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve existing evaluation")
    metrics = json.loads((args.evaluation / "metrics.json").read_text())
    assert metrics["split"] == "valid", "Reference rescore is validation-only"
    old_path, new_path = args.old_data / "valid.jsonl", args.new_data / "valid.jsonl"
    assert metrics["dataset_sha256"] == checksum(old_path)
    original = [json.loads(x) for x in old_path.read_text().splitlines()]
    corrected = [json.loads(x) for x in new_path.read_text().splitlines()]
    assert_same_prompts(original, corrected)
    predictions_path = args.evaluation / "predictions.jsonl"
    predictions = [json.loads(x) for x in predictions_path.read_text().splitlines()]
    assert all(metrics[key] == value for key, value in score(original, predictions).items())
    assert checksum(ROOT / metrics["adapter"] / "adapters.safetensors") == metrics["adapter_sha256"]
    metrics.update(score(corrected, predictions))
    metrics.update(
        dataset_sha256=checksum(new_path),
        reference_rescore=dict(
            original_metrics_sha256=checksum(args.evaluation / "metrics.json"),
            original_dataset_sha256=checksum(old_path),
            predictions_sha256=checksum(predictions_path),
            identical_prompts_verified=True,
            inference_run=False,
            warning="Reference changes only, not model improvement",
        ),
    )
    args.output.mkdir(parents=True)
    shutil.copy2(predictions_path, args.output / "predictions.jsonl")
    (args.output / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

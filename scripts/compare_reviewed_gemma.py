"""Compare one frozen reviewed-data candidate; old test is never loaded here."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.evaluate_gemma import score  # noqa: E402
from scripts.select_gemma_adapter import quality  # noqa: E402


def checked_metrics(folder, data, split):
    folder = ROOT / folder
    source = ROOT / data / f"{split}.jsonl"
    metrics = json.loads((folder / "metrics.json").read_text())
    assert metrics["split"] == split and metrics["dataset_sha256"] == checksum(source)
    assert metrics["generation"] == dict(
        temperature=0.0, max_tokens=256, seed=42, enable_thinking=False
    )
    adapter = ROOT / metrics["adapter"] / "adapters.safetensors"
    assert checksum(adapter) == metrics["adapter_sha256"]
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    predictions = [
        json.loads(line) for line in (folder / "predictions.jsonl").read_text().splitlines()
    ]
    rescored = score(rows, predictions)
    assert all(metrics[key] == value for key, value in rescored.items())
    return metrics, quality(metrics)


def validation_gates(baseline_new, candidate_new, baseline_old, candidate_old, rule):
    return dict(
        new_score_gain=candidate_new["selection_score"]
        >= baseline_new["selection_score"] + rule["minimum_new_validation_score_gain"],
        new_schema_floor=candidate_new["schema_validity"] >= rule["minimum_new_validation_schema"],
        new_json_not_worse=candidate_new["json_validity"] >= baseline_new["json_validity"],
        legacy_json_not_worse=candidate_old["json_validity"] >= baseline_old["json_validity"],
        legacy_score_guard=candidate_old["selection_score"]
        >= baseline_old["selection_score"] - rule["old_validation_max_score_drop"],
        legacy_skill_guard=candidate_old["skill_micro_f1"]
        >= baseline_old["skill_micro_f1"] - rule["old_validation_max_skill_f1_drop"],
        legacy_schema_guard=candidate_old["schema_validity"]
        >= baseline_old["schema_validity"] - rule["old_validation_max_schema_drop"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--with-new-test", action="store_true")
    parser.add_argument("--data", type=Path, default=Path("data/finetune_reviewed/v2.0.0"))
    parser.add_argument(
        "--protocol", type=Path, default=Path("configs/gemma_reviewed_protocol.json")
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/metrics/gemma_reviewed_v2"))
    args = parser.parse_args()
    directory = ROOT / args.output
    protocol_path = ROOT / args.protocol
    protocol = json.loads(protocol_path.read_text())
    dataset = args.data
    if "dataset" in protocol:
        assert str(dataset) == protocol["dataset"]
        assert str(args.output) == protocol["evaluation_directory"]
    assert checksum(ROOT / dataset / "manifest.json") == protocol["new_sft_manifest_sha256"]
    new_base, bn = checked_metrics(directory / "baseline_new_valid", dataset, "valid")
    new_candidate, cn = checked_metrics(directory / "candidate_new_valid", dataset, "valid")
    old_base, bo = checked_metrics(
        Path("outputs/metrics/gemma_20261017T105728Z_adapter_valid"), Path("data/finetune"), "valid"
    )
    old_candidate, co = checked_metrics(
        directory / "candidate_legacy_valid", Path("data/finetune"), "valid"
    )
    assert (
        new_base["adapter_sha256"]
        == old_base["adapter_sha256"]
        == protocol["parent_adapter_sha256"]
    )
    assert (
        new_candidate["adapter_sha256"]
        == old_candidate["adapter_sha256"]
        == checksum(ROOT / args.candidate / "adapters.safetensors")
    )
    assert (
        new_base["model_manifest_sha256"]
        == new_candidate["model_manifest_sha256"]
        == old_base["model_manifest_sha256"]
        == old_candidate["model_manifest_sha256"]
    )
    manifest = json.loads((ROOT / args.candidate / "manifest.json").read_text())
    assert manifest["sft_manifest_sha256"] == protocol["new_sft_manifest_sha256"]
    assert manifest["resume"]["data_transition"]["sha256"] == checksum(protocol_path)
    gates = validation_gates(bn, cn, bo, co, protocol["selection"])
    if protocol["selection"].get("new_experience_must_not_decrease"):
        gates["new_experience_guard"] = (
            new_candidate["field_exact_accuracy"]["experience_years"]
            >= new_base["field_exact_accuracy"]["experience_years"]
        )
    result = dict(
        status="validation_completed",
        candidate=str(args.candidate),
        protocol_sha256=checksum(protocol_path),
        candidate_sha256=new_candidate["adapter_sha256"],
        baseline_new=bn,
        candidate_new=cn,
        baseline_legacy=bo,
        candidate_legacy=co,
        validation_gates=gates,
        validation_passed=all(gates.values()),
        old_test_used=False,
        active_adapter_changed=False,
        limits="AI-reviewed silver references; extraction quality, not salary-regression MAE",
    )
    selection_path = directory / "selection.json"
    if selection_path.exists():
        previous = json.loads(selection_path.read_text())
        assert previous == result, "Preserve locked validation selection"
    else:
        selection_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.with_new_test:
        assert result["validation_passed"], "Do not open test after failed validation"
        test_base, tb = checked_metrics(directory / "baseline_new_test", dataset, "test")
        test_candidate, tc = checked_metrics(directory / "candidate_new_test", dataset, "test")
        assert test_base["adapter_sha256"] == new_base["adapter_sha256"]
        assert test_candidate["adapter_sha256"] == new_candidate["adapter_sha256"]
        rule = protocol["test_guardrails"]
        test_gates = dict(
            enough_sources=test_candidate["independent_source_records"]
            >= rule["minimum_independent_test_sources"],
            score_not_worse=tc["selection_score"] >= tb["selection_score"],
            skill_guard=tc["skill_micro_f1"]
            >= tb["skill_micro_f1"] - rule["skill_f1_must_not_drop_more_than"],
            schema_guard=tc["schema_validity"]
            >= tb["schema_validity"] - rule["schema_must_not_drop_more_than"],
        )
        result.update(
            status="new_test_completed",
            baseline_new_test=tb,
            candidate_new_test=tc,
            test_gates=test_gates,
            promotion_eligible=all(test_gates.values()),
        )
        path = directory / "final_evaluation.json"
        if path.exists():
            assert json.loads(path.read_text()) == result, "Preserve completed test decision"
        else:
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

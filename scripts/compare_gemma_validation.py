"""Compare frozen validation predictions; preserve strict scores and diagnose JSON fences."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_gemma import score  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    source = ROOT / "data/finetune/valid.jsonl"
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    result = {
        "split": "valid",
        "examples": len(rows),
        "source_records": len({row["source_record_id"] for row in rows}),
        "test_used": False,
        "models": {},
    }
    for kind in ["base", "adapter"]:
        folder = ROOT / "outputs/metrics" / f"gemma_{args.run_id}_{kind}_valid"
        metrics = json.loads((folder / "metrics.json").read_text())
        predictions = [
            json.loads(line) for line in (folder / "predictions.jsonl").read_text().splitlines()
        ]
        strict = score(rows, predictions)
        assert strict["field_exact_accuracy"] == metrics["field_exact_accuracy"]
        normalized = []
        removed = 0
        for prediction in predictions:
            value = prediction["output"].strip()
            match = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", value, re.IGNORECASE)
            if match:
                value = match.group(1)
                removed += 1
            normalized.append(dict(prediction, output=value))
        result["models"][kind] = {
            "strict": strict,
            "fence_only_diagnostic": score(rows, normalized),
            "markdown_fences_removed": removed,
            "metrics_path": str((folder / "metrics.json").relative_to(ROOT)),
            "adapter_sha256": metrics["adapter_sha256"],
        }
        original_indices = [i for i, row in enumerate(rows) if row["variant"] == "original"]
        original_rows = [rows[i] for i in original_indices]
        original_predictions = [
            dict(normalized[i], index=j) for j, i in enumerate(original_indices)
        ]
        result["models"][kind]["original_cards_fence_diagnostic"] = score(
            original_rows, original_predictions
        )
    output = ROOT / "outputs/metrics" / f"gemma_{args.run_id}_comparison"
    output.mkdir(parents=True, exist_ok=True)
    result["diagnostic_method"] = (
        "Primary scores parse raw output as strict JSON. Diagnostic only removes one enclosing "
        "Markdown JSON fence; no JSON repair, unit conversion or content edits. "
        "Same rule for both models."
    )
    result["limits"] = (
        "Silver job-card labels; variants are not independent jobs; validation, not holdout test"
    )
    (output / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = [
        f"# Gemma validation — {args.run_id}",
        "",
        f"{result['examples']} variants from {result['source_records']} source cards. "
        "Test untouched.",
        "",
        "| Model | Raw JSON valid | Raw schema valid | Mean field accuracy | Skill F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for kind, item in result["models"].items():
        metric = item["strict"]
        mean = sum(metric["field_exact_accuracy"].values()) / 8
        lines.append(
            f"| {kind} | {metric['json_validity']:.3f} | {metric['schema_validity']:.3f} | "
            f"{mean:.3f} | {metric['skill_micro_f1']:.3f} |"
        )
    lines += [
        "",
        "Raw JSON is the required output contract. Formatting failures count as wrong.",
        "The diagnostic below removes Markdown fences to separate formatting from content.",
        "",
        "| Model | Fences removed | Diagnostic mean field accuracy | Diagnostic Skill F1 |",
        "|---|---:|---:|---:|",
    ]
    for kind, item in result["models"].items():
        metric = item["fence_only_diagnostic"]
        mean = sum(metric["field_exact_accuracy"].values()) / 8
        lines.append(
            f"| {kind} | {item['markdown_fences_removed']} | {mean:.3f} | "
            f"{metric['skill_micro_f1']:.3f} |"
        )
    lines += [
        "",
        "Exact per-field scores and raw predictions are retained beside these results.",
        "Silver references are not independent human gold. This is not career-advice evaluation.",
        "The final 100-step adapter was fixed before evaluation; no further training occurred.",
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

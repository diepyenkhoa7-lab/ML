"""Select adapters using frozen validation only; report raw errors without repairing outputs."""

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.evaluate_gemma import score  # noqa: E402
from scripts.prepare_gemma_sft import validate_label  # noqa: E402


def quality(metrics):
    fields = metrics["field_exact_accuracy"]
    mean = sum(fields.values()) / len(fields)
    values = dict(
        mean_field_exact_accuracy=mean,
        json_validity=metrics["json_validity"],
        schema_validity=metrics["schema_validity"],
        skill_micro_f1=metrics["skill_micro_f1"],
    )
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in values.values()):
        raise ValueError("Non-finite or out-of-range metrics")
    return dict(
        values,
        selection_score=0.5 * mean
        + 0.3 * values["skill_micro_f1"]
        + 0.2 * values["schema_validity"],
    )


def promotion(current, candidate, protocol):
    guard = protocol["guardrails"]
    reasons = []
    if candidate["selection_score"] - current["selection_score"] < protocol["promotion_min_delta"]:
        reasons.append("score gain below minimum delta")
    if (
        guard["json_validity_must_not_decrease"]
        and candidate["json_validity"] < current["json_validity"]
    ):
        reasons.append("JSON validity decreased")
    for key, limit in [
        ("mean_field_exact_accuracy", "max_mean_field_accuracy_drop"),
        ("skill_micro_f1", "max_skill_f1_drop"),
    ]:
        if current[key] - candidate[key] > guard[limit]:
            reasons.append(f"{key} regression exceeds guardrail")
    return not reasons, reasons


def targets_met(values, protocol):
    return all(values[key] >= minimum for key, minimum in protocol["targets"].items())


def load_evaluation(directory, split="valid"):
    metrics = json.loads((directory / "metrics.json").read_text())
    source = ROOT / "data/finetune" / f"{split}.jsonl"
    if metrics["split"] != split or metrics["dataset_sha256"] != checksum(source):
        raise ValueError("Wrong selection split or dataset checksum")
    if checksum(ROOT / metrics["adapter"] / "adapters.safetensors") != metrics["adapter_sha256"]:
        raise ValueError("Adapter changed since evaluation")
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    predictions = [
        json.loads(line) for line in (directory / "predictions.jsonl").read_text().splitlines()
    ]
    rescored = score(rows, predictions)
    for key, value in rescored.items():
        if metrics[key] != value:
            raise ValueError(f"Stored score differs from raw predictions: {key}")
    return metrics, rows, predictions


def diagnostics(rows, predictions):
    errors, numeric, slices = [], {}, {}
    for row, prediction in zip(rows, predictions):
        individual = score([row], [dict(prediction, index=0)])
        wrong = [key for key, value in individual["field_exact_accuracy"].items() if value != 1]
        schema_error = None
        try:
            actual = json.loads(prediction["output"].strip())
            validate_label(actual)
        except (ValueError, TypeError, AttributeError) as exc:
            schema_error = str(exc)
            try:
                actual = json.loads(prediction["output"].strip())
            except (ValueError, TypeError):
                actual = {}
        expected = json.loads(row["messages"][-1]["content"])
        if wrong or schema_error:
            errors.append(
                dict(
                    index=prediction["index"],
                    source_record_id=row["source_record_id"],
                    variant=row.get("variant"),
                    wrong_fields=wrong,
                    schema_error=schema_error,
                    expected=expected,
                    actual=actual,
                )
            )
        if isinstance(actual, dict):
            for key in ["salary_min", "salary_max", "experience_years"]:
                a, b = expected[key], actual.get(key)
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in [a, b]):
                    continue
                unit = (
                    "years"
                    if key == "experience_years"
                    else f"{expected['currency']}/{expected['salary_period']}"
                )
                if key != "experience_years" and any(
                    actual.get(k) != expected[k] for k in ["currency", "salary_period"]
                ):
                    continue
                numeric.setdefault(f"{key}:{unit}", []).append(abs(a - b))
        variant = row.get("variant", "unknown")
        slices.setdefault(variant, ([], []))
        slices[variant][0].append(row)
        slices[variant][1].append(dict(prediction, index=len(slices[variant][1])))
    return dict(
        errors=errors,
        numeric_error_diagnostic={
            key: dict(paired_non_null_same_unit_examples=len(values), mae=sum(values) / len(values))
            for key, values in numeric.items()
        },
        numeric_error_limits=(
            "Paired numeric values only; missing/wrong-unit predictions excluded here "
            "but penalized in primary field accuracy"
        ),
        slices={name: score(*pair) for name, pair in slices.items()},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluations",
        type=Path,
        nargs="+",
        required=True,
        help="Baseline then candidates in chronological order",
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/metrics/gemma_tuning"))
    args = parser.parse_args()
    protocol = json.loads((ROOT / "configs/gemma_tuning_protocol.json").read_text())
    if len(args.evaluations) > protocol["max_candidates"] + 1:
        raise ValueError("Candidate budget exceeded")
    records, best, stale, stop = [], None, 0, None
    for directory in args.evaluations:
        if stop:
            raise ValueError(f"An evaluation was added after the stopping rule: {stop}")
        metrics, rows, predictions = load_evaluation(ROOT / directory)
        if records and any(
            metrics[key] != records[0][key]
            for key in ["generation", "model_manifest_sha256", "dataset_sha256"]
        ):
            raise ValueError("Evaluation conditions differ")
        if not records and metrics["adapter"] != protocol["baseline_adapter"]:
            raise ValueError("Baseline differs from locked protocol")
        values = quality(metrics)
        promoted, reasons = (
            (True, ["baseline"]) if best is None else promotion(best, values, protocol)
        )
        record = dict(
            metrics, **values, evaluation=str(directory), promoted=promoted, reasons=reasons
        )
        if promoted:
            best, stale = record, 0
        else:
            stale += 1
        records.append(record)
        detail = diagnostics(rows, predictions)
        (ROOT / directory / "error_analysis.json").write_text(
            json.dumps(detail, ensure_ascii=False, indent=2) + "\n"
        )
        if targets_met(best, protocol):
            stop = "validation targets met"
        elif stale >= protocol["patience"]:
            stop = "two consecutive candidates without sufficient improvement"
        elif len(records) - 1 >= protocol["max_candidates"]:
            stop = "candidate budget exhausted"
    result = dict(
        protocol_sha256=checksum(ROOT / "configs/gemma_tuning_protocol.json"),
        protocol=protocol,
        selected_adapter=best["adapter"],
        selected_evaluation=best["evaluation"],
        selection_split="valid",
        stop_reason=stop,
        candidates_evaluated=len(records) - 1,
        targets_met=targets_met(best, protocol),
        records=records,
        test_used_for_selection=False,
    )
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "selection.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Gemma: validation selection",
        "",
        f"Selected: `{best['adapter']}`",
        "",
        "Primary scores use raw outputs. No JSON repair. Test is excluded from selection.",
        "",
        "| Adapter | Mean field exact | Skill F1 | JSON | Schema | Selection score | Promoted |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| {Path(record['adapter']).name} | {record['mean_field_exact_accuracy']:.4f} "
            f"| {record['skill_micro_f1']:.4f} | {record['json_validity']:.4f} "
            f"| {record['schema_validity']:.4f} | {record['selection_score']:.4f} "
            f"| {record['promoted']} |"
        )
    lines += [
        "",
        f"Stopping rule: {stop or 'continue candidates under locked protocol'}.",
        "",
        "Silver source-field labels; validation has 72 variants from 25 jobs. "
        "These scores do not establish generalization to arbitrary ads or career advice.",
        "",
        "Per-run error_analysis.json records schema failures, exact field errors, "
        "variant slices and paired same-unit numeric MAE.",
    ]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k not in {"records", "protocol"}}, indent=2)
    )


if __name__ == "__main__":
    main()

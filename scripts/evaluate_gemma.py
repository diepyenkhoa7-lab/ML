"""Generate/score extraction predictions; inference only, never trains Gemma."""

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.prepare_gemma_sft import FIELDS, validate_label  # noqa: E402


def score(rows, predictions):
    if len(rows) != len(predictions):
        raise ValueError("Prediction count does not match frozen references")
    valid_json = valid_schema = tp = fp = fn = 0
    correct = dict.fromkeys(FIELDS, 0)
    for index, (row, prediction) in enumerate(zip(rows, predictions)):
        if (
            prediction["index"] != index
            or prediction["source_record_id"] != row["source_record_id"]
        ):
            raise ValueError("Prediction order/source mismatch")
        target = json.loads(row["messages"][-1]["content"])
        try:
            value = json.loads(prediction["output"].strip())
            if not isinstance(value, dict):
                raise ValueError("Expected JSON object")
            valid_json += 1
            try:
                validate_label(value)
                valid_schema += 1
            except (ValueError, TypeError):
                pass
        except (ValueError, TypeError):
            value = {}
        for key in FIELDS:
            if key not in value:
                continue
            expected, actual = target[key], value[key]
            if isinstance(expected, (int, float)) and not isinstance(actual, bool):
                equal = isinstance(actual, (int, float)) and math.isclose(
                    expected, actual, rel_tol=1e-6, abs_tol=1e-6
                )
            elif key == "skills" and isinstance(actual, list):
                equal = set(expected or []) == set(x for x in actual if isinstance(x, str))
            else:
                equal = type(actual) is type(expected) and actual == expected
            correct[key] += int(equal)
        expected_skills = {s.casefold().strip() for s in target["skills"] or []}
        actual = value.get("skills")
        actual_skills = (
            {s.casefold().strip() for s in actual if isinstance(s, str)}
            if isinstance(actual, list)
            else set()
        )
        tp += len(expected_skills & actual_skills)
        fp += len(actual_skills - expected_skills)
        fn += len(expected_skills - actual_skills)
    n = len(rows)
    return {
        "examples": n,
        "json_validity": valid_json / n,
        "schema_validity": valid_schema / n,
        "field_exact_accuracy": {k: v / n for k, v in correct.items()},
        "skill_micro_precision": tp / (tp + fp) if tp + fp else 0,
        "skill_micro_recall": tp / (tp + fn) if tp + fn else 0,
        "skill_micro_f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0,
        "limits": "Silver references; augmented cards are not independent jobs; not advice quality",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["valid", "test"], default="valid")
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--predictions", type=Path, help="Score an existing predictions JSONL")
    parser.add_argument("--generate", action="store_true", help="Run inference, without training")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.generate and not args.predictions:
        parser.error("Choose --generate or --predictions")
    source = ROOT / "data/finetune" / f"{args.split}.jsonl"
    manifest = json.loads((source.parent / "manifest.json").read_text())
    assert checksum(source) == manifest["splits"][args.split]["sha256"]
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    output = args.output
    if output.exists():
        raise SystemExit("Preserve existing evaluation; choose a new --output directory")
    output.mkdir(parents=True)
    if args.generate:
        import mlx.core as mx
        from mlx_lm import generate, load
        from mlx_lm.sample_utils import make_sampler

        mx.random.seed(42)
        model, tokenizer = load(
            str(ROOT / "models/gemma-mlx-4bit"),
            adapter_path=str(args.adapter) if args.adapter else None,
        )
        predictions = []
        for index, row in enumerate(rows):
            prompt = tokenizer.apply_chat_template(
                row["messages"][:-1],
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            result = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=256,
                sampler=make_sampler(temp=0.0),
                verbose=False,
            )
            predictions.append(
                dict(index=index, source_record_id=row["source_record_id"], output=result)
            )
            print(f"{index + 1}/{len(rows)}", flush=True)
            (output / "predictions.jsonl").write_text(
                "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in predictions)
            )
    else:
        predictions = [json.loads(line) for line in args.predictions.read_text().splitlines()]
    result = score(rows, predictions)
    result.update(
        split=args.split,
        dataset_sha256=checksum(source),
        adapter=str(args.adapter) if args.adapter else None,
        gemma_training_started_by_this_command=False,
    )
    (output / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

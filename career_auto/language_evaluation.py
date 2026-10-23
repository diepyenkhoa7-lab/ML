"""Extraction metrics against silver references, including individual field accuracy."""

from career_ai.language import extract


def evaluate_language(model, examples):
    correct = dict(role=0, experience_years=0)
    known_correct = dict(role=0, experience_years=0)
    known_total = dict(role=0, experience_years=0)
    valid = tp = fp = fn = 0
    errors = []
    for i, item in enumerate(examples):
        expected = item["answer"]
        for field in correct:
            known_total[field] += int(expected.get(field) is not None)
        try:
            actual = extract(model, item["prompt"])
            valid += 1
            for field in correct:
                equal = actual.get(field) == expected.get(field)
                correct[field] += int(equal)
                known_correct[field] += int(equal and expected.get(field) is not None)
            a = {s.casefold() for s in actual["skills"]}
            b = {s.casefold() for s in expected["skills"]}
            tp += len(a & b)
            fp += len(a - b)
            fn += len(b - a)
        except (ValueError, TypeError, KeyError) as exc:
            fn += len(set(expected.get("skills", [])))
            errors.append(dict(index=i, error=str(exc)[:240]))
    n = len(examples)
    return dict(
        samples=n,
        json_schema_rate=valid / n if n else None,
        field_accuracy=sum(correct.values()) / (2 * n) if n else None,
        field_accuracy_by_name={k: v / n if n else None for k, v in correct.items()},
        known_field_samples=known_total,
        known_field_accuracy={
            k: known_correct[k] / v if v else None for k, v in known_total.items()
        },
        skill_f1=(
            2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else (float(valid == n) if n else None)
        ),
        errors=errors,
        label_quality="source_derived_silver_not_human_gold",
    )

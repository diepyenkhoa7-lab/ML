"""Validation by default; the automatic goal authorizes test only for the final winner."""

import argparse
from pathlib import Path

from career_ai.data import ROOT, UNITS, load, load_language
from career_ai.evaluation import metrics

from .state import FOLDER, read, write


def evaluate(run, family="llm", split="valid", language=True):
    if split not in ["valid", "test"]:
        raise ValueError("Evaluation split must be valid or test")
    metadata = read(run / f"{family}.json")
    if metadata.get("limited_trial"):
        raise ValueError("Smoke trial is not eligible for full evaluation")
    if split == "test":
        state = read(FOLDER / "state.json")
        if not state.get("test_authorized") or (
            family == "llm" and (ROOT / state["selected_run"]).resolve() != run.resolve()
        ):
            raise ValueError("Test is reserved for the selected final checkpoint")
    from career_ai.models import loaded_llm, predict

    frame = load(split)
    predictions = predict(frame, run, family)
    result = metrics(frame, predictions)
    frame.assign(prediction=predictions, unit=frame.market.map(UNITS)).to_csv(
        run / f"{family}_{split}_predictions.csv", index=False
    )
    write(run / f"{family}_{split}_metrics.json", result)
    if family == "llm" and language:
        from career_ai.language import evaluate_language

        examples = load_language(split)
        if split == "valid":
            examples = examples[:32]
        write(run / f"language_{split}.json", evaluate_language(loaded_llm(run)[0], examples))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--model", choices=["baseline", "llm"], default="llm")
    parser.add_argument("--split", choices=["valid", "test"], default="valid")
    args = parser.parse_args()
    evaluate(args.run, args.model, args.split)

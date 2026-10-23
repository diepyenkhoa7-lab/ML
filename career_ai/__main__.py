import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .data import ROOT, UNITS, digest, load, load_language, prepare, validate_profile, write


def main():
    p = argparse.ArgumentParser(
        description="TensorFlow salary research; train and inference are separate commands"
    )
    p.add_argument(
        "command",
        choices=[
            "prepare",
            "train-baseline",
            "train-llm",
            "evaluate",
            "predict",
            "analyze",
            "advise",
        ],
    )
    p.add_argument("--run", type=Path)
    p.add_argument("--input", type=Path)
    p.add_argument("--model", choices=["baseline", "llm"], default="llm")
    p.add_argument("--epochs", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--language-eval", action="store_true")
    a = p.parse_args()
    if a.epochs is not None and a.epochs < 1:
        p.error("--epochs must be positive")
    if a.limit is not None and a.command != "train-llm":
        p.error("--limit is only supported by train-llm smoke trials")
    if a.command == "prepare":
        print(json.dumps(prepare(), ensure_ascii=False, indent=2))
        return
    if a.command.startswith("train-"):
        from .models import baseline_train, llm_train

        folder = a.run or ROOT / "outputs" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        folder.mkdir(parents=True, exist_ok=False)
        lineage = dict(
            status="running",
            started_at=datetime.now(UTC).isoformat(),
            command=a.command,
            epochs=a.epochs,
            limit=a.limit,
            dataset_manifest_sha256=digest(ROOT / "data/tensorflow_v1/manifest.json"),
            source_sha256={
                str(p.relative_to(ROOT)): digest(p) for p in (ROOT / "career_ai").glob("*.py")
            },
        )
        write(folder / "lineage.json", lineage)
        try:
            if a.command == "train-baseline":
                baseline_train(folder, a.epochs or 100)
            else:
                llm_train(folder, a.epochs or 2, a.limit)
        except BaseException as exc:
            lineage.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        else:
            lineage["status"] = "completed"
        finally:
            lineage["ended_at"] = datetime.now(UTC).isoformat()
            write(folder / "lineage.json", lineage)
        print(folder)
        return
    if not a.run:
        p.error("--run is required")
    from .models import predict

    if a.command == "evaluate":
        from .evaluation import metrics

        if a.model == "llm" and json.loads((a.run / "llm.json").read_text()).get("limited_trial"):
            p.error("Limited smoke trial cannot be reported as full test evaluation")
        frame = load("test")
        pred = predict(frame, a.run, a.model)
        result = metrics(frame, pred)
        evaluated = frame.assign(prediction=pred, unit=frame.market.map(UNITS))
        evaluated.to_csv(a.run / (a.model + "_test_predictions.csv"), index=False)
        write(a.run / (a.model + "_test_metrics.json"), result)
        if a.language_eval and a.model == "llm":
            from .language import evaluate_language
            from .models import loaded_llm

            examples = load_language("test")
            write(a.run / "language_test.json", evaluate_language(loaded_llm(a.run)[0], examples))
        print(json.dumps(result, indent=2))
        return
    if not a.input:
        p.error("--input is required")
    if a.input.suffix == ".json":
        frame = pd.read_json(a.input)
    elif a.input.suffix == ".xlsx":
        frame = pd.read_excel(a.input)
    else:
        frame = pd.read_csv(a.input)
    if a.command == "advise":
        from .language import advise
        from .models import loaded_llm

        lm, _ = loaded_llm(a.run)
        results = []
        for r in frame.to_dict("records"):
            try:
                profile = validate_profile(r)
                estimate = float(predict(pd.DataFrame([profile]), a.run, "llm")[0])
                results.append(
                    dict(
                        profile=profile,
                        salary=estimate,
                        unit=UNITS[profile["market"]],
                        **advise(lm, profile),
                    )
                )
            except (ValueError, TypeError, KeyError) as exc:
                results.append(dict(error=str(exc)))
        write(a.run / "advice.json", results)
        print(a.run / "advice.json")
        return
    results = []
    for i, row in enumerate(frame.to_dict("records")):
        try:
            row = dict(row)
            if (
                isinstance(row.get("description"), str)
                and row["description"]
                and any(not row.get(k) for k in ["role", "experience_years", "skills"])
            ):
                from .language import extract
                from .models import loaded_llm

                extraction = extract(loaded_llm(a.run)[0], str(row["description"]))
                for k, v in extraction.items():
                    if row.get(k) is None or row.get(k) == "":
                        row[k] = v
            profile = validate_profile(row)
            value = float(predict(pd.DataFrame([profile]), a.run, a.model)[0])
            results.append(
                dict(
                    source_row=i + 1,
                    **profile,
                    prediction=value,
                    model_version=f"{a.model}:{a.run.name}",
                    unit=UNITS[profile["market"]],
                    error=None,
                )
            )
        except (ValueError, TypeError, KeyError) as exc:
            results.append(dict(source_row=i + 1, prediction=None, error=str(exc)))
    frame = pd.DataFrame(results)
    destination = a.run / "predictions.csv"
    frame.to_csv(destination, index=False)
    write(a.run / "predictions.json", results)
    print(destination)
    if a.command == "analyze":
        from .charts import charts

        charts(frame[frame.error.isna()], a.run / "figures")


if __name__ == "__main__":
    main()

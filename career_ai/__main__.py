import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .data import ROOT, UNITS, digest, prepare, validate_profile, write
from .inputs import missing, read_profiles


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
    p.add_argument("--extractor-run", type=Path)
    p.add_argument("--model", choices=["baseline", "llm"], default="llm")
    p.add_argument("--epochs", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--language-eval", action="store_true")
    p.add_argument("--split", choices=["valid", "test"], default="valid")
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
        from career_auto.evaluation import evaluate
        print(json.dumps(evaluate(a.run, a.model, a.split, a.language_eval), indent=2))
        return
    if not a.input:
        p.error("--input is required")
    frame = read_profiles(a.input)
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
                and any(missing(row.get(k)) for k in ["role", "experience_years", "skills"])
            ):
                from .language import extract
                from .models import loaded_llm

                extractor_run = a.run if a.model == "llm" else a.extractor_run
                if extractor_run is None:
                    raise ValueError("Text extraction with baseline requires --extractor-run")
                extraction = extract(loaded_llm(extractor_run)[0], str(row["description"]))
                for k, v in extraction.items():
                    if missing(row.get(k)):
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
    frame = pd.DataFrame(
        results,
        columns=[
            "source_row",
            "market",
            "role",
            "location",
            "experience_years",
            "skills",
            "prediction",
            "model_version",
            "unit",
            "error",
        ],
    )
    destination = a.run / "predictions.csv"
    frame.to_csv(destination, index=False)
    write(a.run / "predictions.json", results)
    print(destination)
    if a.command == "analyze":
        from .charts import charts

        charts(frame[frame.error.isna()], a.run / "figures")


if __name__ == "__main__":
    main()

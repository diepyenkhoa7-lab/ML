"""Acceptance demo on train-derived profiles; never presented as a blind quality metric."""

import argparse
import json
import sys
from pathlib import Path

from career_ai.data import FEATURES, ROOT, UNITS, load

from .state import FOLDER, write


def text_demo(run, folder, profiles, main):
    """Exercise extraction plus regression; examples are synthetic, not quality labels."""
    import numpy as np

    records = []
    for market in ["vietnam", "international"]:
        profile = next(p for p in profiles if p["market"] == market)
        if market == "vietnam":
            description = (
                f"Tuyển {profile['role']}. Kinh nghiệm: {profile['experience_years']} năm. "
                f"Kỹ năng yêu cầu: {profile['skills']}."
            )
        else:
            description = (
                f"Hiring a {profile['role']}. Experience: {profile['experience_years']} years. "
                f"Required skills: {profile['skills']}."
            )
        records.append(dict(market=market, location=profile["location"], description=description))
    path = folder / "job_text.json"
    write(path, records)
    previous = {
        name: (run / name).read_bytes()
        for name in ["predictions.json", "predictions.csv"]
        if (run / name).exists()
    }
    sys.argv = ["career_ai", "predict", "--run", str(run), "--input", str(path)]
    main()
    predictions = json.loads((run / "predictions.json").read_text())
    if len(predictions) != 2:
        raise ValueError("Text demo did not return both markets")
    for record, prediction in zip(records, predictions, strict=True):
        if (
            prediction.get("error")
            or prediction.get("market") != record["market"]
            or prediction.get("unit") != UNITS[record["market"]]
            or not prediction.get("model_version")
            or not np.isfinite(prediction.get("prediction", float("nan")))
        ):
            raise ValueError("Text extraction-to-salary demo failed; inspect predictions.json")
    write(folder / "text_predictions.json", predictions)
    for name, content in previous.items():
        (run / name).write_bytes(content)
    return dict(
        passed=True,
        profiles=2,
        provenance="Synthetic job descriptions from train profile features; salary excluded",
        quality_metric=False,
    )


def demo(run):
    import numpy as np
    import pandas as pd

    from career_ai.__main__ import main

    folder = FOLDER / "demo"
    folder.mkdir(exist_ok=True)
    records = load("train").groupby("market").head(2)[FEATURES].to_dict("records")
    records.append(dict(records[0], market="invalid"))
    records.append(
        dict(records[0], role=None, experience_years=None, skills=None, description="job " * 4000)
    )
    frame = pd.DataFrame(records)
    frame.to_csv(folder / "profiles.csv", index=False)
    frame.to_excel(folder / "profiles.xlsx", index=False)
    write(folder / "profiles.json", records)
    reference = None
    for suffix in ["csv", "xlsx", "json"]:
        sys.argv = [
            "career_ai",
            "analyze",
            "--run",
            str(run),
            "--model",
            "llm",
            "--input",
            str(folder / f"profiles.{suffix}"),
        ]
        main()
        values = json.loads((run / "predictions.json").read_text())
        if len(values) != 6 or any(values[i].get("error") for i in range(4)):
            raise ValueError("Structured valid profiles failed inference")
        if not all(values[i].get("error") for i in [4, 5]):
            raise ValueError("Invalid or oversized rows were not rejected individually")
        for value in values[:4]:
            if value["unit"] != UNITS[value["market"]] or not np.isfinite(value["prediction"]):
                raise ValueError("Invalid unit or nonfinite prediction")
        numbers = [r["prediction"] for r in values[:4]]
        if reference is not None:
            np.testing.assert_allclose(numbers, reference, rtol=1e-5)
        reference = numbers
        write(folder / f"predictions_{suffix}.json", values)
    extraction = text_demo(run, folder, records[:4], main)
    write(folder / "advice_profiles.json", records[:4])
    sys.argv = [
        "career_ai",
        "advise",
        "--run",
        str(run),
        "--input",
        str(folder / "advice_profiles.json"),
    ]
    main()
    advice = json.loads((run / "advice.json").read_text())
    if any(r.get("error") for r in advice):
        raise ValueError("Career advice failed; inspect run advice.json")
    write(
        folder / "acceptance.json",
        dict(
            passed=True,
            model_run=str(run.relative_to(ROOT)),
            formats=["csv", "xlsx", "json"],
            valid_profiles=4,
            rejected_rows=2,
            advice=True,
            text_extraction=extraction,
            dataset="train-derived demonstration, not test metrics",
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    demo(parser.parse_args().run.resolve())

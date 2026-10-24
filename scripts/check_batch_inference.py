"""Exercise the actual CLI and saved baseline across all three input formats."""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def check():
    import numpy as np
    import pandas as pd

    from career_ai.__main__ import main
    from career_ai.data import FEATURES, load, write

    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    folder = args.run / "batch_checks"
    folder.mkdir(exist_ok=True)
    records = load("train").groupby("market").head(2)[FEATURES].to_dict("records")
    records.append(dict(records[0], market="invalid"))
    frame = pd.DataFrame(records)
    frame.to_csv(folder / "input.csv", index=False)
    frame.to_excel(folder / "input.xlsx", index=False)
    write(folder / "input.json", records)
    reference = None
    for suffix in ["csv", "xlsx", "json"]:
        sys.argv = [
            "career_ai",
            "analyze",
            "--run",
            str(args.run),
            "--model",
            "baseline",
            "--input",
            str(folder / f"input.{suffix}"),
        ]
        main()
        result = json.loads((args.run / "predictions.json").read_text())
        assert len(result) == 5 and result[-1]["error"]
        assert all(r["error"] is None for r in result[:-1])
        values = [r["prediction"] for r in result[:-1]]
        if reference is None:
            reference = values
        else:
            np.testing.assert_allclose(values, reference, rtol=1e-6)
        shutil.copyfile(args.run / "predictions.json", folder / f"output_{suffix}.json")
    write(
        folder / "result.json",
        dict(
            passed=True, formats=["csv", "xlsx", "json"], valid_rows=4, invalid_rows=1, charts=True
        ),
    )
    print("Actual model batch inference and charts passed", flush=True)


check()

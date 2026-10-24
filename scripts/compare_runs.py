"""Compare completed full experiments on the same frozen dataset and units."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--baseline", type=Path, required=True)
parser.add_argument("--llm", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
metadata = [
    json.loads((folder / f"{family}.json").read_text())
    for family, folder in [("baseline", args.baseline), ("llm", args.llm)]
]
if metadata[1].get("limited_trial"):
    raise ValueError("Cannot compare a limited LLM smoke trial with full test results")
if metadata[0]["dataset_manifest_sha256"] != metadata[1]["dataset_manifest_sha256"]:
    raise ValueError("Experiments used different frozen datasets")
rows = []
for family, folder in [("baseline", args.baseline), ("llm", args.llm)]:
    scores = json.loads((folder / f"{family}_test_metrics.json").read_text())
    rows.extend(
        dict(model=family, market=market, **values)
        for market, values in scores["by_market"].items()
    )
frame = pd.DataFrame(rows)
for market, part in frame.groupby("market"):
    if part.samples.nunique() != 1 or part.unit.nunique() != 1:
        raise ValueError(f"Sample or unit mismatch: {market}")
args.output.mkdir(parents=True, exist_ok=False)
frame.to_csv(args.output / "comparison.csv", index=False)
for market, part in frame.groupby("market"):
    ax = part.set_index("model")[["mae", "rmse"]].plot.bar(rot=0, figsize=(7, 4))
    ax.set_ylabel(part.unit.iloc[0])
    ax.set_title(market)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output / f"{market}_errors.png")
    plt.close(ax.figure)
print(frame.to_string(index=False))

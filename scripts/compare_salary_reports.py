"""Aggregate market sanity checks. Never train, calibrate or open a holdout."""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.salary import FEATURES, SalaryService, salary_service  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402


def main():
    current, old = salary_service(), SalaryService()
    frame = current.train.copy()
    folder = ROOT / f"outputs/metrics/salary_{current.experiment}/external_sanity"
    folder.mkdir(parents=True, exist_ok=True)
    reference = pd.read_csv(ROOT / "data/references/itviec_2025_2026.csv")
    rows = []
    for ref in reference.to_dict("records"):
        subset = frame[
            frame.role.eq(ref["role"])
            & frame.experience_years.between(ref["low_years"], ref["high_years"])
        ]
        if len(subset) < 5:
            rows.append(dict(**ref, train_profiles=len(subset), status="insufficient_5_profiles"))
            continue
        current_median = float(
            np.median(current.models[current.selected_model].predict(subset[FEATURES]))
        )
        old_median = float(np.median(old.models[old.selected_model].predict(subset[FEATURES])))
        rows.append(
            dict(
                **ref,
                train_profiles=len(subset),
                status="comparable_unit_different_population",
                current_prediction_median_vnd=current_median,
                old_prediction_median_vnd=old_median,
                gap_vnd=current_median - ref["median_vnd_month"],
                gap_pct=(current_median / ref["median_vnd_month"] - 1) * 100,
            )
        )
    comparison = pd.DataFrame(rows)
    comparison.to_csv(folder / "itviec_comparison.csv", index=False, lineterminator="\n")
    usable = comparison[comparison.train_profiles.ge(5)]
    if len(usable):
        plot = usable.assign(group=usable.role + " · " + usable.experience_band + "y")
        plot = plot.melt(
            id_vars=["group"],
            value_vars=[
                "median_vnd_month",
                "old_prediction_median_vnd",
                "current_prediction_median_vnd",
            ],
            var_name="series",
            value_name="vnd",
        )
        plot["million_vnd"] = plot.vnd / 1e6
        plot["series"] = plot.series.map(
            dict(
                median_vnd_month="ITviec aggregate",
                old_prediction_median_vnd="v1 RF predictions",
                current_prediction_median_vnd="v2 Ridge predictions",
            )
        )
        sns.set_theme(style="whitegrid")
        fig, ax = plt.subplots(figsize=(10, max(4, len(usable) * 0.65)), layout="constrained")
        sns.barplot(data=plot, y="group", x="million_vnd", hue="series", ax=ax, errorbar=None)
        ax.set(
            title="Market sanity check; different populations, not holdout error",
            xlabel="Million VND/month",
            ylabel="Role / experience band",
        )
        handles, labels = ax.get_legend_handles_labels()
        ax.get_legend().remove()
        fig.legend(handles, labels, loc="outside lower center", ncol=3, frameon=False)
        fig.savefig(folder / "itviec_comparison.png", dpi=150)
        plt.close(fig)
    topdev = pd.read_csv(ROOT / "data/references/topdev_2024_2025.csv")
    role_predictions = {}
    for role, subset in frame.groupby("role"):
        if len(subset) >= 5:
            role_predictions[role] = float(
                np.median(current.models[current.selected_model].predict(subset[FEATURES]))
            )
    base = role_predictions.get("Backend Developer")
    topdev["current_prediction_median_vnd"] = topdev.role.map(role_predictions)
    topdev["topdev_ratio_to_backend"] = topdev.median_usd_month_gross / 1340
    topdev["model_ratio_to_backend"] = (
        topdev.current_prediction_median_vnd / base if base else np.nan
    )
    topdev.to_csv(folder / "topdev_relative_comparison.csv", index=False, lineterminator="\n")
    summary = dict(
        status="completed",
        scope="aggregate sanity check only; no model/label/calibration changes",
        data_source="selected model training profiles only; no validation/test opened",
        itviec_available_groups=len(usable),
        itviec_insufficient_groups=len(comparison) - len(usable),
        median_absolute_gap_percent=float(usable.gap_pct.abs().median()) if len(usable) else None,
        caution=(
            "Survey actual income vs disclosed advertised ranges; experience/skills/employer "
            "populations and gross/net differ. Gap is NOT prediction MAE."
        ),
        topdev="USD kept native; compare relative role ratios only, no implicit FX",
        files={
            p.name: checksum(p)
            for p in folder.iterdir()
            if p.is_file() and p.name != "manifest.json"
        },
    )
    (folder / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

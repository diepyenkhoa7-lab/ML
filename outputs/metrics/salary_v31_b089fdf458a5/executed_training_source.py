"""Real strict-label ablation; validation selection precedes one fresh-source evaluation."""

import copy
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.salary import FEATURES, SalaryService  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402
from scripts.train_salary_v2 import metrics, preprocessing, write  # noqa: E402


def checked(item):
    path = ROOT / item["path"]
    assert checksum(path) == item["sha256"], "Frozen input checksum mismatch"
    frame = pd.read_csv(path)
    if "rows" in item:
        assert len(frame) == item["rows"]
    frame["experience_years"] = frame.experience_years.astype(float)
    for col in FEATURES[1:]:
        frame[col] = frame[col].astype(object).where(frame[col].notna(), np.nan)
    return frame


def market_panel(predictions, panel, refs):
    rows = []
    for ref in refs.to_dict("records"):
        mask = panel.role.eq(ref["role"]) & panel.experience_years.between(
            ref["low_years"], ref["high_years"]
        )
        row = dict(**ref, profiles=int(mask.sum()))
        if mask.sum() >= 5:
            for name, values in predictions.items():
                median = float(np.median(values[mask]))
                row[name + "_median_vnd"] = median
                row[name + "_gap_pct"] = (median / ref["median_vnd_month"] - 1) * 100
        rows.append(row)
    comparison = pd.DataFrame(rows)
    usable = comparison[comparison.profiles.ge(5)]
    gaps = {
        name: float(usable[name + "_gap_pct"].abs().median()) if len(usable) else None
        for name in predictions
    }
    return comparison, gaps


def run():
    protocol_path = ROOT / "configs/salary_v31_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    dataset_path = ROOT / f"data/splits/v{protocol['version']}/vn_developer/manifest.json"
    dataset = json.loads(dataset_path.read_text())
    assert checksum(protocol_path) == dataset["protocol_sha256"]
    assert checksum(ROOT / "scripts/prepare_salary_v31.py") == dataset["code_sha256"]
    assert checksum(ROOT / "scripts/salary_v31_labels.py") == dataset["labels_code_sha256"]
    assert checksum(ROOT / "scripts/salary_v3_labels.py") == dataset["inherited_labels_code_sha256"]
    experiment = "v31_" + checksum(dataset_path)[:12]
    output = ROOT / "outputs/metrics" / ("salary_" + experiment)
    output.mkdir(parents=True, exist_ok=False)
    write(output / "protocol.json", protocol)
    (output / "executed_training_source.py").write_bytes(Path(__file__).read_bytes())
    train, older, valid = [checked(dataset["files"][k]) for k in ["train", "older_train", "valid"]]
    assert set(valid.leakage_group_id).isdisjoint(
        set(train.leakage_group_id) | set(older.leakage_group_id)
    )
    assert all(d.label_quality.eq("direct_month_range_silver").all() for d in [train, older, valid])
    # The market panel and incumbent bytes are frozen before fitting; no panel targets used.
    panel = checked(dataset["market_panel"])
    incumbent = SalaryService("v2_042e3aa1a886")
    old_panel_predictions = incumbent.models[incumbent.selected_model].predict(panel[FEATURES])
    candidates, selected = [], {}
    for arm in protocol["candidates"]["arms"]:
        data = train if arm == "recent_strict" else pd.concat([train, older], ignore_index=True)
        weights = np.where(data.source_year.ge(2025), 1.0, protocol["candidates"]["older_weight"])
        prep = preprocessing()
        x, xv = prep.fit_transform(data[FEATURES]), None
        xv = prep.transform(valid[FEATURES])
        specs = [("ridge", dict(alpha=a)) for a in protocol["candidates"]["ridge_alphas"]]
        specs += [
            ("random_forest", dict(min_samples_leaf=n))
            for n in protocol["candidates"]["random_forest_min_leaf"]
        ]
        for family, params in specs:
            started = time.monotonic()
            estimator = (
                Ridge(**params)
                if family == "ridge"
                else RandomForestRegressor(
                    n_estimators=protocol["candidates"]["random_forest_trees"],
                    criterion=protocol["candidates"]["random_forest_criterion"],
                    random_state=31415,
                    n_jobs=4,
                    **params,
                )
            )
            estimator.fit(x, data.salary_monthly_vnd.to_numpy(), sample_weight=weights)
            score = metrics(valid.salary_monthly_vnd, estimator.predict(xv))
            candidate = dict(
                family=family,
                arm=arm,
                parameters=params,
                train_rows=len(data),
                weak_rows=0,
                valid=score,
                elapsed_seconds=time.monotonic() - started,
            )
            candidates.append(candidate)
            write(output / "validation_candidates.json", candidates)
            print(json.dumps(candidate), flush=True)
            previous = selected.get(family)
            if previous is None or (score["mae_vnd"], score["rmse_vnd"]) < (
                previous["candidate"]["valid"]["mae_vnd"],
                previous["candidate"]["valid"]["rmse_vnd"],
            ):
                selected[family] = dict(
                    candidate=candidate,
                    pipeline=Pipeline(
                        [
                            ("preprocess", copy.deepcopy(prep)),
                            ("model", estimator),
                        ]
                    ),
                )
    best = min(
        selected,
        key=lambda n: (
            selected[n]["candidate"]["valid"]["mae_vnd"],
            selected[n]["candidate"]["valid"]["rmse_vnd"],
        ),
    )
    model_dir = ROOT / "models/salary" / experiment
    model_dir.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for family, item in selected.items():
        path = model_dir / f"{family}.joblib"
        joblib.dump(item["pipeline"], path)
        artifacts[family] = dict(path=str(path.relative_to(ROOT)), sha256=checksum(path))
    selection = dict(
        experiment_id=experiment,
        selected_model=best,
        selected={k: v["candidate"] for k, v in selected.items()},
        artifacts=artifacts,
        test_opened=False,
        selected_at_utc=datetime.now(timezone.utc).isoformat(),
        data_manifest_sha256=checksum(dataset_path),
        code_sha256=checksum(Path(__file__)),
    )
    write(output / "selection.json", selection)
    comparison, gaps = market_panel(
        dict(v2=old_panel_predictions, v3=selected[best]["pipeline"].predict(panel[FEATURES])),
        panel,
        pd.read_csv(ROOT / "data/references/itviec_2025_2026.csv"),
    )
    comparison.to_csv(output / "market_panel_comparison.csv", index=False)
    # First access to fresh public holdout targets occurs only after model selection is locked.
    test = checked(dataset["files"]["test"])
    assert set(test.leakage_group_id).isdisjoint(
        set(train.leakage_group_id) | set(older.leakage_group_id) | set(valid.leakage_group_id)
    )
    predictions = {k: v["pipeline"].predict(test[FEATURES]) for k, v in selected.items()}
    predictions["v2_ridge"] = incumbent.models[incumbent.selected_model].predict(test[FEATURES])
    scores = {k: metrics(test.salary_monthly_vnd, p) for k, p in predictions.items()}
    new, old = scores[best], scores["v2_ridge"]
    rule = protocol["promotion"]
    gates = dict(
        enough_independent_rows=len(test) >= rule["min_test_rows"],
        enough_independent_companies=test.leakage_group_id.nunique() >= rule["min_test_companies"],
        mae_improves_5pct=new["mae_vnd"]
        <= old["mae_vnd"] * (1 - rule["min_mae_improvement_vs_v2"]),
        rmse_guard=new["rmse_vnd"] <= old["rmse_vnd"] * rule["rmse_ratio_max_vs_v2"],
        nonnegative_r2=new["r2"] is not None and new["r2"] >= rule["min_r2"],
        market_gap_not_worse=gaps["v3"] is not None and gaps["v3"] <= gaps["v2"],
        same_arm_for_serving=len({v["candidate"]["arm"] for v in selected.values()}) == 1,
    )
    rng, deltas = np.random.default_rng(31415), []
    groups = test.leakage_group_id.unique()
    difference = np.abs(test.salary_monthly_vnd.to_numpy() - predictions["v2_ridge"]) - np.abs(
        test.salary_monthly_vnd.to_numpy() - predictions[best]
    )
    for _ in range(2000):
        indices = np.concatenate(
            [
                np.flatnonzero(test.leakage_group_id.to_numpy() == g)
                for g in rng.choice(groups, len(groups), replace=True)
            ]
        )
        deltas.append(float(np.mean(difference[indices])))
    result = dict(
        experiment_id=experiment,
        selected_model=best,
        test=scores,
        promotion_gates=gates,
        promotion_eligible=all(gates.values()),
        market_panel_median_absolute_gap_pct=gaps,
        market_caution=(
            "Known aggregate objective; not independent individual income MAE. "
            "Same frozen panel and groups for both models; no report rows used in training."
        ),
        paired_mae_improvement_company_bootstrap_95_vnd=(
            np.percentile(deltas, [2.5, 97.5]).tolist() if len(groups) >= 10 else None
        ),
        bootstrap_caution="No confidence interval reported for fewer than 10 independent companies",
        test_opened_once_after_selection=True,
        old_holdouts_not_used=True,
        selection_sha256=checksum(output / "selection.json"),
    )
    write(output / "test_metrics.json", result)
    exported = test[
        ["record_id", "leakage_group_id", "role", "salary_monthly_vnd", "source_url"]
    ].copy()
    for name, values in predictions.items():
        exported[name] = values
    exported.to_csv(output / "test_predictions.csv", index=False)
    for family, item in selected.items():
        snapshot = (
            train if item["candidate"]["arm"] == "recent_strict" else pd.concat([train, older])
        )
        snapshot.to_csv(model_dir / f"{family}_training_snapshot.csv", index=False)
    write(
        model_dir / "manifest.json",
        dict(
            experiment_id=experiment,
            selected_model=best,
            artifacts=artifacts,
            dataset_manifest=dict(
                path=str(dataset_path.relative_to(ROOT)), sha256=checksum(dataset_path)
            ),
            evaluation=dict(
                path=str((output / "test_metrics.json").relative_to(ROOT)),
                sha256=checksum(output / "test_metrics.json"),
            ),
            selected_by="validation MAE, RMSE",
            weak_rows=0,
            promotion_eligible=all(gates.values()),
            serving_status="candidate; active config unchanged",
        ),
    )
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    run()

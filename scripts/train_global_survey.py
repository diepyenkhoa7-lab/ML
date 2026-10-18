"""Fit a versioned global compensation model, separate from Vietnam advertised salary."""

import json
import re
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.train_open_aijobs import digest, score, write  # noqa: E402


def main():
    protocol_path = ROOT / "configs/global_survey_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    source = protocol["source_csv"]
    assert digest(ROOT / source["path"]) == source["sha256"]
    experiment = "global_survey_v1_" + source["sha256"][:12]
    split_dir = ROOT / "data/splits" / experiment
    output = ROOT / "outputs/metrics" / experiment
    models = ROOT / "models/salary" / experiment
    if any(path.exists() for path in [split_dir, output, models]):
        raise ValueError("Immutable experiment already exists")
    for path in [split_dir, output, models]:
        path.mkdir(parents=True)
    started = time.monotonic()
    raw = pd.read_csv(ROOT / source["path"], low_memory=False)
    data = pd.DataFrame(
        dict(
            experience_years=pd.to_numeric(raw.WorkExp, errors="coerce"),
            role=raw.DevType.str.strip(),
            country=raw.Country.str.strip(),
            salary_annual_usd=pd.to_numeric(raw.ConvertedCompYearly, errors="coerce"),
        )
    )
    data["skills"] = (
        raw[protocol["skills_columns"]]
        .fillna("")
        .agg(";".join, axis=1)
        .map(
            lambda value: ";".join(
                sorted({s.strip().casefold() for s in value.split(";") if s.strip()})
            )
        )
    )
    data = data.dropna()
    data = data[
        data.salary_annual_usd.between(1000, 1000000) & data.experience_years.between(0, 80)
    ]
    data = data[data.role.ne("") & data.country.ne("")].drop_duplicates().reset_index(drop=True)
    features = protocol["features"]
    data["profile_group"] = pd.util.hash_pandas_object(data[features], index=False).map(str)
    train_valid, test_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=20261018).split(
            data, groups=data.profile_group
        )
    )
    develop, test = data.iloc[train_valid], data.iloc[test_idx]
    train_idx, valid_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.1875, random_state=20261018).split(
            develop, groups=develop.profile_group
        )
    )
    train, valid = develop.iloc[train_idx], develop.iloc[valid_idx]
    for a, b in [(train, valid), (train, test), (valid, test)]:
        assert set(a.profile_group).isdisjoint(b.profile_group)
    files = {}
    for name, frame in dict(train=train, valid=valid, test=test).items():
        path = split_dir / (name + ".csv")
        frame.to_csv(path, index=False)
        files[name] = dict(
            path=str(path.relative_to(ROOT)),
            rows=len(frame),
            groups=int(frame.profile_group.nunique()),
            sha256=digest(path),
        )
    write(
        split_dir / "manifest.json",
        dict(
            experiment=experiment,
            source=source,
            protocol_sha256=digest(protocol_path),
            raw_rows=len(raw),
            retained_rows=len(data),
            files=files,
            target="salary_annual_usd",
            unit="USD/year",
            limits=protocol["limits"],
        ),
    )
    candidates, fitted = [], {}
    for family, settings in [("ridge", [10, 100]), ("random_forest", [5, 15])]:
        for value in settings:
            regressor = (
                Ridge(alpha=value, solver="lsqr")
                if family == "ridge"
                else (
                    RandomForestRegressor(
                        n_estimators=120,
                        max_depth=14,
                        min_samples_leaf=value,
                        n_jobs=4,
                        random_state=20261018,
                    )
                )
            )
            preprocess = ColumnTransformer(
                [
                    ("experience", StandardScaler(), ["experience_years"]),
                    ("categories", OneHotEncoder(handle_unknown="ignore"), ["role", "country"]),
                    (
                        "skills",
                        Pipeline(
                            [
                                (
                                    "flatten",
                                    FunctionTransformer(np.ravel, feature_names_out="one-to-one"),
                                ),
                                (
                                    "vectorizer",
                                    CountVectorizer(
                                        binary=True,
                                        token_pattern=None,
                                        tokenizer=re.compile(r"[^;]+").findall,
                                        min_df=3,
                                    ),
                                ),
                            ]
                        ),
                        ["skills"],
                    ),
                ]
            )
            pipeline = Pipeline(
                [
                    ("preprocess", preprocess),
                    (
                        "model",
                        TransformedTargetRegressor(
                            regressor=regressor, func=np.log1p, inverse_func=np.expm1
                        ),
                    ),
                ]
            )
            print(f"FIT {family}={value}; train {len(train)} valid {len(valid)}", flush=True)
            pipeline.fit(train[features], train.salary_annual_usd)
            name = f"{family}_{value}"
            fitted[name] = pipeline
            candidates.append(
                dict(
                    name=name,
                    family=family,
                    parameter=value,
                    **score(valid.salary_annual_usd, pipeline.predict(valid[features])),
                )
            )
            write(output / "validation_candidates.json", candidates)
            print(json.dumps(candidates[-1]), flush=True)
    selection = {
        family: min(
            (c for c in candidates if c["family"] == family),
            key=lambda c: (c["mae_usd_year"], c["rmse_usd_year"]),
        )
        for family in ["ridge", "random_forest"]
    }
    selected = min(selection, key=lambda f: selection[f]["mae_usd_year"])
    write(
        output / "selection.json",
        dict(selected=selection, selected_family=selected, protocol_sha256=digest(protocol_path)),
    )
    metrics, artifacts = {}, {}
    predictions = test[["profile_group", "salary_annual_usd"]].copy()
    for family, choice in selection.items():
        pipeline = fitted[choice["name"]]
        path = models / (family + ".joblib")
        joblib.dump(pipeline, path, compress=3)
        artifacts[family] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        predictions[family] = pipeline.predict(test[features])
        metrics[family] = score(test.salary_annual_usd, predictions[family])
    metrics["median_baseline"] = score(
        test.salary_annual_usd, np.full(len(test), train.salary_annual_usd.median())
    )
    baseline, best = metrics["median_baseline"], metrics[selected]
    gates = dict(
        enough_rows=len(test) >= 200,
        enough_groups=test.profile_group.nunique() >= 200,
        mae=best["mae_usd_year"] <= 0.95 * baseline["mae_usd_year"],
        rmse=best["rmse_usd_year"] <= 1.05 * baseline["rmse_usd_year"],
    )
    result = dict(
        experiment=experiment,
        unit="USD/year",
        target="salary_annual_usd",
        selected_family=selected,
        test=metrics,
        samples=len(test),
        profile_serving_gates=gates,
        profile_serving_eligible=all(gates.values()),
        elapsed_seconds=round(time.monotonic() - started, 2),
        limits=protocol["limits"],
    )
    write(output / "test_metrics.json", result)
    predictions.to_csv(output / "test_predictions.csv", index=False)
    snapshot = models / "training_snapshot.csv"
    train.to_csv(snapshot, index=False)
    write(
        models / "manifest.json",
        dict(
            experiment_id=experiment,
            artifacts=artifacts,
            selected_model=selected,
            unit="USD/year",
            features=features,
            target="salary_annual_usd",
            profile_serving_eligible=all(gates.values()),
            promotion_eligible=False,
            serving_scope="international_survey_only",
            dataset_manifest=dict(
                path=str((split_dir / "manifest.json").relative_to(ROOT)),
                sha256=digest(split_dir / "manifest.json"),
            ),
            training_snapshot=dict(path=str(snapshot.relative_to(ROOT)), sha256=digest(snapshot)),
            evaluation=dict(
                path=str((output / "test_metrics.json").relative_to(ROOT)),
                sha256=digest(output / "test_metrics.json"),
            ),
        ),
    )
    print("COMPLETED " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()

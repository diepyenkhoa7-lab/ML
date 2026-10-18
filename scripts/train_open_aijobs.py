"""Train an isolated annual-USD benchmark; never replace the Vietnam serving model."""

import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def score(y, prediction):
    if not np.isfinite(prediction).all():
        raise ValueError("Nonfinite benchmark predictions")
    return dict(
        samples=len(y),
        mae_usd_year=float(mean_absolute_error(y, prediction)),
        rmse_usd_year=float(np.sqrt(mean_squared_error(y, prediction))),
        r2=float(r2_score(y, prediction)),
    )


def main():
    protocol_path = ROOT / "configs/open_aijobs_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    source = protocol["source_csv"]
    raw_path = ROOT / source["path"]
    if digest(raw_path) != source["sha256"]:
        raise ValueError("Raw source hash mismatch")
    experiment = "open_aijobs_v1_" + source["sha256"][:12]
    split_dir = ROOT / "data/splits" / experiment
    output = ROOT / "outputs/metrics" / experiment
    models = ROOT / "models/salary" / experiment
    if any(path.exists() for path in [split_dir, output, models]):
        raise ValueError("Immutable experiment exists; inspect its results instead of rerunning")
    for path in [split_dir, output, models]:
        path.mkdir(parents=True)
    started = time.monotonic()
    raw = pd.read_csv(raw_path)
    features = protocol["features"]
    numeric = ["work_year", "remote_ratio"]
    categories = [name for name in features if name not in numeric]
    data = raw[features + ["salary_in_usd"]].copy()
    for name in numeric + ["salary_in_usd"]:
        data[name] = pd.to_numeric(data[name], errors="coerce")
    for name in categories:
        data[name] = data[name].astype("string").str.strip()
    data = data.dropna()
    data = data[
        data.salary_in_usd.between(1000, 1000000)
        & data.work_year.between(2020, 2025)
        & data.remote_ratio.isin([0, 50, 100])
    ]
    data = data[~data[categories].eq("").any(axis=1)].drop_duplicates().reset_index(drop=True)
    group_fields = protocol["group_features"]
    data["profile_group"] = [
        hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()
        for values in data[group_fields].itertuples(index=False, name=None)
    ]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=20261018)
    develop_index, test_index = next(splitter.split(data, groups=data.profile_group))
    develop, test = data.iloc[develop_index], data.iloc[test_index]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.1875, random_state=20261018)
    train_index, valid_index = next(splitter.split(develop, groups=develop.profile_group))
    train, valid = develop.iloc[train_index], develop.iloc[valid_index]
    partitions = dict(train=train, valid=valid, test=test)
    for a, b in [(train, valid), (train, test), (valid, test)]:
        assert set(a.profile_group).isdisjoint(b.profile_group)
    files = {}
    for name, frame in partitions.items():
        path = split_dir / (name + ".csv")
        frame.to_csv(path, index=False)
        files[name] = dict(
            path=str(path.relative_to(ROOT)),
            rows=len(frame),
            groups=frame.profile_group.nunique(),
            sha256=digest(path),
        )
    manifest = dict(
        experiment=experiment,
        source=source,
        protocol_sha256=digest(protocol_path),
        raw_rows=len(raw),
        retained_unique_rows=len(data),
        files=files,
        target=protocol["target"],
        unit=protocol["unit"],
        limits=protocol["limits"],
    )
    write(split_dir / "manifest.json", manifest)
    candidates, fitted = [], {}
    for family, settings in [("ridge", [10, 100]), ("random_forest", [10, 30])]:
        for value in settings:
            estimator = (
                Ridge(alpha=value, solver="lsqr")
                if family == "ridge"
                else (
                    RandomForestRegressor(
                        n_estimators=100,
                        max_depth=12,
                        min_samples_leaf=value,
                        max_features=0.7,
                        n_jobs=4,
                        random_state=20261018,
                    )
                )
            )
            preprocess = ColumnTransformer(
                [
                    (
                        "numeric",
                        Pipeline(
                            [
                                ("impute", SimpleImputer(strategy="median")),
                                ("scale", StandardScaler()),
                            ]
                        ),
                        numeric,
                    ),
                    ("categories", OneHotEncoder(handle_unknown="ignore"), categories),
                ]
            )
            pipeline = Pipeline(
                [
                    ("preprocess", preprocess),
                    (
                        "regressor",
                        TransformedTargetRegressor(
                            regressor=estimator, func=np.log1p, inverse_func=np.expm1
                        ),
                    ),
                ]
            )
            print(
                f"FIT {family} parameter={value}, train={len(train)} valid={len(valid)}", flush=True
            )
            pipeline.fit(train[features], train.salary_in_usd)
            metrics = score(valid.salary_in_usd, pipeline.predict(valid[features]))
            name = f"{family}_{value}"
            fitted[name] = pipeline
            candidates.append(dict(name=name, family=family, parameter=value, **metrics))
            write(output / "validation_candidates.json", candidates)
            print(json.dumps(candidates[-1]), flush=True)
    selection = {}
    for family in ["ridge", "random_forest"]:
        selection[family] = min(
            (c for c in candidates if c["family"] == family),
            key=lambda c: (c["mae_usd_year"], c["rmse_usd_year"]),
        )
    selected_family = min(selection, key=lambda f: selection[f]["mae_usd_year"])
    write(
        output / "selection.json",
        dict(
            selected=selection,
            selected_family=selected_family,
            protocol_sha256=digest(protocol_path),
        ),
    )
    # Open the fixed test only after the per-family validation choices have been persisted.
    metrics, artifacts = {}, {}
    predictions = test[["profile_group", "salary_in_usd"]].copy()
    for family, choice in selection.items():
        model = fitted[choice["name"]]
        path = models / (family + ".joblib")
        joblib.dump(model, path, compress=3)
        artifacts[family] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        predictions[family] = model.predict(test[features])
        metrics[family] = score(test.salary_in_usd, predictions[family])
    baseline = np.full(len(test), train.salary_in_usd.median())
    metrics["median_baseline"] = score(test.salary_in_usd, baseline)
    predictions.to_csv(output / "test_predictions.csv", index=False)
    result = dict(
        experiment=experiment,
        target=protocol["target"],
        unit="USD/year",
        selected_family=selected_family,
        test=metrics,
        samples=len(test),
        elapsed_seconds=round(time.monotonic() - started, 2),
        dataset_manifest_sha256=digest(split_dir / "manifest.json"),
        protocol_sha256=digest(protocol_path),
        serving_model_changed=False,
        limits=protocol["limits"],
    )
    write(output / "test_metrics.json", result)
    write(
        models / "manifest.json",
        dict(
            experiment_id=experiment,
            artifacts=artifacts,
            selected_model=selected_family,
            promotion_eligible=False,
            serving_scope=(
                "research-only international annual USD; incompatible with VN offer contract"
            ),
            dataset_manifest=str((split_dir / "manifest.json").relative_to(ROOT)),
            evaluation=dict(
                path=str((output / "test_metrics.json").relative_to(ROOT)),
                sha256=digest(output / "test_metrics.json"),
            ),
        ),
    )
    print("COMPLETED " + json.dumps(result), flush=True)


if __name__ == "__main__":
    main()

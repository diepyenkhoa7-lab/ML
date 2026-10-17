"""Train a fixed validation-only grid; open the new explicit holdout once after selection."""

import copy
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.salary import FEATURES, SalaryService  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def preprocessing():
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                ["experience_years"],
            ),
            (
                "categories",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                ["role", "level", "location"],
            ),
            (
                "skills",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(strategy="constant", fill_value="__missing_skill__"),
                        ),
                        ("flatten", FunctionTransformer(np.ravel, feature_names_out="one-to-one")),
                        (
                            "vectorizer",
                            CountVectorizer(
                                binary=True,
                                token_pattern=None,
                                tokenizer=re.compile(r"[^;]+").findall,
                            ),
                        ),
                    ]
                ),
                ["skills"],
            ),
        ]
    )


def metrics(target, prediction):
    target, prediction = np.asarray(target), np.asarray(prediction)
    errors = np.abs(target - prediction)
    return dict(
        samples=len(target),
        mae_vnd=mean_absolute_error(target, prediction),
        rmse_vnd=float(np.sqrt(mean_squared_error(target, prediction))),
        r2=r2_score(target, prediction) if len(target) > 1 and np.var(target) else None,
        median_absolute_error_vnd=float(np.median(errors)),
        within_5m=float(np.mean(errors <= 5e6)),
    )


def checked_frame(item):
    path = ROOT / item["path"]
    if checksum(path) != item["sha256"]:
        raise ValueError("Frozen v2 data checksum mismatch")
    frame = pd.read_csv(path)
    assert len(frame) == item["rows"]
    frame["experience_years"] = frame.experience_years.astype(float)
    for col in FEATURES[1:]:
        frame[col] = frame[col].astype(object).where(frame[col].notna(), np.nan)
    return frame


def run():
    protocol_path = ROOT / "configs/salary_v2_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    data_manifest_path = ROOT / f"data/splits/v{protocol['version']}/vn_developer/manifest.json"
    manifest = json.loads(data_manifest_path.read_text())
    assert checksum(protocol_path) == manifest["protocol_sha256"]
    assert checksum(ROOT / "scripts/prepare_salary_v2.py") == manifest["code_sha256"]
    experiment = "v2_" + checksum(data_manifest_path)[:12]
    output = ROOT / "outputs/metrics" / ("salary_" + experiment)
    if output.exists():
        raise ValueError("Preserve completed/incomplete experiment; no automatic retrain on test")
    output.mkdir(parents=True)
    write(output / "protocol.json", protocol)
    train, weak, valid = [
        checked_frame(manifest["files"][s]) for s in ["train", "weak_train", "valid"]
    ]
    assert set(train.leakage_group_id).isdisjoint(valid.leakage_group_id)
    assert set(weak.leakage_group_id).isdisjoint(valid.leakage_group_id)
    selected = {}
    candidates = []
    for arm in protocol["candidates"]["arms"]:
        data = train if arm == "strict" else pd.concat([train, weak], ignore_index=True)
        weights = np.where(data.label_quality.eq("explicit_month"), 1.0, 0.3)
        prep = preprocessing()
        x = prep.fit_transform(data[FEATURES])
        xv = prep.transform(valid[FEATURES])
        for family, params in [
            ("ridge", dict(alpha=a)) for a in protocol["candidates"]["ridge_alphas"]
        ] + [
            ("random_forest", dict(min_samples_leaf=leaf))
            for leaf in protocol["candidates"]["random_forest_min_leaf"]
        ]:
            started = time.monotonic()
            model = (
                Ridge(**params)
                if family == "ridge"
                else RandomForestRegressor(
                    n_estimators=300,
                    criterion="absolute_error",
                    random_state=42,
                    n_jobs=4,
                    **params,
                )
            )
            model.fit(x, data.salary_monthly_vnd.to_numpy(), sample_weight=weights)
            score = metrics(valid.salary_monthly_vnd, model.predict(xv))
            candidate = dict(
                family=family,
                arm=arm,
                parameters=params,
                train_rows=len(data),
                valid=score,
                elapsed_seconds=time.monotonic() - started,
            )
            candidates.append(candidate)
            write(output / "validation_candidates.json", candidates)
            print(json.dumps(candidate), flush=True)
            old = selected.get(family)
            key = (score["mae_vnd"], score["rmse_vnd"])
            if old is None or key < (
                old["candidate"]["valid"]["mae_vnd"],
                old["candidate"]["valid"]["rmse_vnd"],
            ):
                selected[family] = dict(
                    candidate=candidate,
                    pipeline=Pipeline([("preprocess", copy.deepcopy(prep)), ("model", model)]),
                )
    best_family = min(
        selected,
        key=lambda name: (
            selected[name]["candidate"]["valid"]["mae_vnd"],
            selected[name]["candidate"]["valid"]["rmse_vnd"],
        ),
    )
    model_dir = ROOT / "models/salary" / experiment
    model_dir.mkdir(parents=True, exist_ok=False)
    artifacts = {}
    for family, item in selected.items():
        path = model_dir / (family + ".joblib")
        joblib.dump(item["pipeline"], path)
        artifacts[family] = dict(path=str(path.relative_to(ROOT)), sha256=checksum(path))
    selection = dict(
        experiment_id=experiment,
        selected_model=best_family,
        chosen_at_utc=datetime.now(timezone.utc).isoformat(),
        selected={name: item["candidate"] for name, item in selected.items()},
        test_opened=False,
        data_manifest_sha256=checksum(data_manifest_path),
        code_sha256=checksum(Path(__file__)),
    )
    write(output / "selection.json", selection)
    # Holdout is first loaded after all candidates/artifact identities are locked.
    test = checked_frame(manifest["files"]["test"])
    assert test.label_quality.eq("explicit_month").all()
    assert set(test.leakage_group_id).isdisjoint(
        set(train.leakage_group_id) | set(weak.leakage_group_id) | set(valid.leakage_group_id)
    )
    baseline = SalaryService()
    predictions = {
        name: item["pipeline"].predict(test[FEATURES]) for name, item in selected.items()
    }
    predictions["v1_random_forest"] = baseline.models["random_forest"].predict(test[FEATURES])
    dummy = DummyRegressor(strategy="median").fit(train[FEATURES], train.salary_monthly_vnd)
    predictions["median_baseline"] = dummy.predict(test[FEATURES])
    scores = {name: metrics(test.salary_monthly_vnd, value) for name, value in predictions.items()}
    old, new = scores["v1_random_forest"], scores[best_family]
    promotion = dict(
        enough_holdout=len(test) >= 20,
        mae_improves_10pct=new["mae_vnd"] <= old["mae_vnd"] * 0.9,
        rmse_guard=new["rmse_vnd"] <= old["rmse_vnd"] * 1.05,
        nonnegative_r2=new["r2"] is not None and new["r2"] >= 0,
    )
    accepted = all(promotion.values())
    # Paired company-cluster bootstrap describes uncertainty; not a tuning signal.
    rng = np.random.default_rng(42)
    groups = test.leakage_group_id.unique()
    errors_old = np.abs(test.salary_monthly_vnd.to_numpy() - predictions["v1_random_forest"])
    errors_new = np.abs(test.salary_monthly_vnd.to_numpy() - predictions[best_family])
    delta = []
    for _ in range(2000):
        sampled = rng.choice(groups, size=len(groups), replace=True)
        indices = np.concatenate(
            [np.flatnonzero(test.leakage_group_id.to_numpy() == g) for g in sampled]
        )
        delta.append(float(np.mean(errors_old[indices] - errors_new[indices])))
    result = dict(
        experiment_id=experiment,
        selected_model=best_family,
        test=scores,
        promotion_gates=promotion,
        promotion_eligible=accepted,
        paired_mae_improvement_company_bootstrap_95_vnd=np.percentile(delta, [2.5, 97.5]).tolist(),
        selection_sha256=checksum(output / "selection.json"),
        no_test_feedback_retraining=True,
    )
    write(output / "test_metrics.json", result)
    exported = test[
        ["record_id", "leakage_group_id", "role", "location", "label_quality", "salary_monthly_vnd"]
    ].copy()
    for name, value in predictions.items():
        exported[name] = value
    exported.to_csv(output / "test_predictions.csv", index=False)
    slices = {}
    for field in ["role", "location", "source_year"]:
        for value, group in test.groupby(field):
            slices[f"{field}={value}"] = metrics(
                group.salary_monthly_vnd,
                predictions[best_family][test.index.get_indexer(group.index)],
            )
    write(output / "test_slices.json", slices)
    serving_train = (
        train if selected[best_family]["candidate"]["arm"] == "strict" else pd.concat([train, weak])
    )
    serving_train.to_csv(model_dir / "training_snapshot.csv", index=False)
    model_manifest = dict(
        experiment_id=experiment,
        selected_model=best_family,
        artifacts=artifacts,
        features=FEATURES,
        target="salary_monthly_vnd",
        unit="VND/month",
        dataset_manifest=dict(
            path=str(data_manifest_path.relative_to(ROOT)), sha256=checksum(data_manifest_path)
        ),
        training_snapshot=dict(
            path=str((model_dir / "training_snapshot.csv").relative_to(ROOT)),
            sha256=checksum(model_dir / "training_snapshot.csv"),
        ),
        evaluation=dict(
            path=str((output / "test_metrics.json").relative_to(ROOT)),
            sha256=checksum(output / "test_metrics.json"),
        ),
        selection_sha256=checksum(output / "selection.json"),
        protocol_sha256=checksum(protocol_path),
        promotion_eligible=accepted,
        label_quality="silver explicit + optional weak-period TRAIN ONLY",
        sklearn=__import__("sklearn").__version__,
    )
    write(model_dir / "manifest.json", model_manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    run()

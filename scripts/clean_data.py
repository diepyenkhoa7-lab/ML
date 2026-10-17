"""Chạy pipeline làm sạch 4 nguồn; lưu audit, review, nhãn tách theo nguồn/tiền tệ."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.data_cleaning import DEFAULT_POLICY, clean_source  # noqa: E402

INPUTS = {
    "user_vietnam_it_jobs": "data/raw/user_vietnam_it_jobs/vietnam_it_job_posts.csv",
    "vietjobs_2025": "data/raw/vietjobs_2025/VietJobs.csv",
    "stackoverflow_2025": "data/raw/stackoverflow_2025/survey_results_public.csv",
    "dataforge_2026_08": "data/raw/dataforge_2026_08/extracted/data/jobs.csv",
}
FEATURES = [
    "role",
    "level",
    "country",
    "location",
    "is_remote",
    "experience_years",
    "experience_min",
    "experience_max",
    "experience_kind",
    "experience_missing",
    "skills",
    "skills_json",
    "skills_missing",
]
SO_COLUMNS = [
    "ResponseId",
    "DevType",
    "Country",
    "WorkExp",
    "ConvertedCompYearly",
    "MainBranch",
    "LanguageHaveWorkedWith",
    "DatabaseHaveWorkedWith",
    "PlatformHaveWorkedWith",
    "WebframeHaveWorkedWith",
]


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "rows": len(df),
        "sha256": checksum(path),
    }


def validate_partition(result, raw_rows):
    clean, review, audit = result["clean"], result["review"], result["audit"]
    assert len(audit) == raw_rows
    assert audit.source_row_index.is_unique
    assert len(clean) == int(audit.disposition.eq("kept").sum())
    assert len(review) == int(audit.disposition.isin(["review", "quarantined_provenance"]).sum())
    if len(clean):
        assert clean.record_id.is_unique
        assert clean.review_reasons.eq("").all()
        for col in [
            "salary_min",
            "salary_max",
            "salary_monthly_native",
            "salary_monthly_vnd",
            "compensation_annual_usd",
            "experience_years",
        ]:
            values = pd.to_numeric(clean[col], errors="coerce").dropna()
            assert values.ge(0).all() and values.lt(float("inf")).all(), col
        labeled = clean.salary_monthly_native.notna()
        assert clean.loc[labeled, "salary_status"].eq("valid").all()
        assert clean.loc[labeled, "salary_period"].isin(["month", "year"]).all()
        vnd = clean.salary_monthly_vnd.notna()
        assert clean.loc[vnd, "currency"].eq("VND").all()
        assert clean.loc[vnd, "target_definition"].eq("advertised_salary_midpoint").all()


def process(source, policy, destination):
    path = ROOT / INPUTS[source]
    before = checksum(path)
    df = pd.read_csv(
        path, low_memory=False, usecols=SO_COLUMNS if source == "stackoverflow_2025" else None
    )
    print(f"Cleaning {source}: {len(df):,} rows", flush=True)
    result = clean_source(source, df, policy)
    validate_partition(result, len(df))
    assert checksum(path) == before, "Raw data was changed"
    folder = destination / source
    previous_manifest = folder / "manifest.json"
    previous_labels = (
        json.loads(previous_manifest.read_text()).get("files", {}).get("labels", [])
        if previous_manifest.exists()
        else []
    )
    files = {
        name: write_csv(result[name], folder / f"{name}.csv")
        for name in ["clean", "review", "audit"]
    }
    clean = result["clean"]
    label_files = []
    if len(clean):
        if source == "stackoverflow_2025":
            eligible = clean.compensation_annual_usd.notna()
            # Chỉ dùng phản hồi của người khai lập trình là nghề nghiệp chính cho bộ nhãn này.
            profession = df.set_index("ResponseId").MainBranch.to_dict()
            professional = clean.record_id.map(
                lambda x: profession.get(int(x.rsplit(":", 1)[1]))
            ).eq("I am a developer by profession")
            eligible &= professional
            target, label_unit = "compensation_annual_usd", "USD_year_gross"
        else:
            eligible = clean.salary_monthly_native.notna()
            target, label_unit = "salary_monthly_native", None
        for (currency, basis), group in clean.loc[eligible].groupby(["currency", "salary_basis"]):
            unit = label_unit or f"{currency}_month_{basis}"
            meta = ["record_id", "group_id", "source_dataset", "source_row_index"]
            columns = meta + FEATURES + [target]
            exported = group[columns].copy()
            if source != "stackoverflow_2025" and currency == "VND":
                exported = exported.rename(columns={target: "salary_monthly_vnd"})
            label_files.append(write_csv(exported, folder / "labels" / f"{unit}.csv"))
    files["labels"] = label_files
    # Remove only obsolete exports tracked by the prior run, within this source's labels folder.
    current_paths = {(ROOT / item["path"]).resolve() for item in label_files}
    for item in previous_labels:
        old = (ROOT / item["path"]).resolve()
        if old.parent == (folder / "labels").resolve() and old not in current_paths:
            old.unlink(missing_ok=True)
    dispositions = {str(k): int(v) for k, v in result["audit"].disposition.value_counts().items()}
    reasons = (
        result["review"].review_reasons.str.split(";").explode()
        if len(result["review"])
        else pd.Series(dtype=str)
    )
    stats = {
        "source": source,
        "raw_rows": len(df),
        "raw_path": INPUTS[source],
        "raw_sha256": before,
        "dispositions": dispositions,
        "clean_rows": len(clean),
        "review_rows": len(result["review"]),
        "label_rows": sum(item["rows"] for item in label_files),
        "label_files": len(label_files),
        "files": files,
        "review_reason_counts": {str(k): int(v) for k, v in reasons.value_counts().items()},
        "salary_status_counts_clean": {
            str(k): int(v) for k, v in clean.salary_status.value_counts().items()
        }
        if len(clean)
        else {},
        "decimal_salary_corrections": int(clean.salary_text_corrected_numeric.sum())
        if len(clean)
        else 0,
        "missing_experience_clean": int(clean.experience_missing.sum()) if len(clean) else 0,
        "missing_skills_clean": int(clean.skills_missing.sum()) if len(clean) else 0,
        "input_metadata": str(Path(INPUTS[source]).parent / "manifest.json")
        if source != "dataforge_2026_08"
        else "data/raw/dataforge_2026_08/manifest.json",
    }
    (folder / "manifest.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(
        f"{source}: clean={len(clean):,}, review={len(result['review']):,}, "
        f"labels={stats['label_rows']:,}",
        flush=True,
    )
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=INPUTS)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/cleaned")
    parser.add_argument("--policy", type=Path, default=ROOT / "configs/cleaning.json")
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text()) if args.policy.exists() else DEFAULT_POLICY
    policy_hash = hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    sources = [args.source] if args.source else list(INPUTS)
    summaries = [process(source, policy, destination) for source in sources]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": policy,
        "policy_sha256": policy_hash,
        "code_sha256": {
            name: checksum(ROOT / "scripts" / name)
            for name in ["data_cleaning.py", "clean_data.py"]
        },
        "sources": summaries,
        "feature_columns": FEATURES,
        "raw_inputs_unchanged": True,
        "scope": (
            "Rule-based cleaning; no imputation, FX, learned outlier cutoffs, splits or training"
        ),
    }
    report_dir = ROOT / "outputs/data_quality/cleaning"
    report_dir.mkdir(parents=True, exist_ok=True)
    stem = args.source or "all_sources"
    (report_dir / f"{stem}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    summary = pd.DataFrame(
        [
            {
                k: s[k]
                for k in [
                    "source",
                    "raw_rows",
                    "clean_rows",
                    "review_rows",
                    "label_rows",
                    "decimal_salary_corrections",
                ]
            }
            for s in summaries
        ]
    )
    summary.to_csv(report_dir / f"{stem}.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

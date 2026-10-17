"""Rà soát nhãn nguồn, nhóm tin và đóng băng train/valid/test; chưa huấn luyện."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import FEATURES, checksum  # noqa: E402
from scripts.label_review import (  # noqa: E402
    assign_splits,
    digest,
    group_records,
    review_labels,
)

META = ["record_id", "group_id", "leakage_group_id", "source_dataset", "source_row_index"]


def save_csv(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return {"path": str(path.relative_to(ROOT)), "rows": len(frame), "sha256": checksum(path)}


def load_candidates(cleaning):
    all_rows, inputs = [], []
    for source in cleaning["sources"]:
        name = source["source"]
        item = source["files"]["clean"]
        path = ROOT / item["path"]
        if checksum(path) != item["sha256"]:
            raise ValueError(f"Clean input changed: {path}")
        inputs.append({"path": item["path"], "sha256": item["sha256"]})
        clean = pd.read_csv(path, low_memory=False).set_index("record_id", drop=False)
        for label in source["files"]["labels"]:
            path = ROOT / label["path"]
            if checksum(path) != label["sha256"]:
                raise ValueError(f"Label input changed: {path}")
            inputs.append({"path": label["path"], "sha256": label["sha256"]})
            labels = pd.read_csv(path)
            target = labels.columns[-1]
            rows = clean.loc[labels.record_id].copy().reset_index(drop=True)
            rows["target"] = labels[target].to_numpy()
            rows["target_name"] = target
            rows["cohort"] = (
                "vn_it"
                if name in {"user_vietnam_it_jobs", "vietjobs_2025"}
                else "so_survey"
                if name == "stackoverflow_2025"
                else "dataforge_" + path.stem
            )
            if not rows.salary_status.eq("valid").all():
                raise ValueError("Non-valid salary in label export")
            all_rows.append(rows)
        print(f"Loaded {name}: {source['label_rows']:,} label candidates", flush=True)
    result = pd.concat(all_rows, ignore_index=True)
    if not result.record_id.is_unique:
        raise ValueError("Repeated source record in label exports")
    raw = pd.read_csv(ROOT / "data/raw/user_vietnam_it_jobs/vietnam_it_job_posts.csv")
    result["platform"] = None
    mask = result.source_dataset.eq("user_vietnam_it_jobs")
    result.loc[mask, "platform"] = raw.source_platform.iloc[
        result.loc[mask, "source_row_index"].astype(int)
    ].to_numpy()
    # Check the survey contract against the downloaded native fields as well as the clean export.
    survey = pd.read_csv(
        ROOT / "data/raw/stackoverflow_2025/survey_results_public.csv",
        usecols=["ResponseId", "ConvertedCompYearly", "MainBranch"],
    ).set_index("ResponseId")
    mask = result.source_dataset.eq("stackoverflow_2025")
    ids = result.loc[mask, "record_id"].str.rsplit(":", n=1).str[-1].astype(int)
    native = survey.loc[ids]
    if not native.MainBranch.eq("I am a developer by profession").all():
        raise ValueError("Non-professional survey response in salary cohort")
    if not (native.ConvertedCompYearly.to_numpy() == result.loc[mask, "target"].to_numpy()).all():
        raise ValueError("Survey annual target changed")
    return result, inputs


def partition_validation(frame):
    if frame.groupby("leakage_group_id").split.nunique().max() != 1:
        raise ValueError("A leakage group appears in multiple partitions")
    if frame.groupby("record_id").split.nunique().max() != 1:
        raise ValueError("A record appears in multiple partitions")
    if not frame.target.gt(0).all():
        raise ValueError("Non-positive target")


def write_cohort(name, frame, policy, split_dir, parent=None):
    folder = split_dir / name
    target_name = frame.target_name.iloc[0]
    if frame.target_name.nunique() != 1 or frame.currency.nunique() != 1:
        raise ValueError("Mixed targets or currencies")
    count_groups = frame.leakage_group_id.nunique()
    counts = frame.split.value_counts().to_dict() if "split" in frame else {}
    eligible = count_groups >= policy["minimum_cohort_groups"] and all(
        counts.get(part, 0) >= policy["minimum_partition_rows"]
        for part in ["train", "valid", "test"]
    )
    files = {}
    previous = folder / "manifest.json"
    previous_files = json.loads(previous.read_text()).get("files", {}) if previous.exists() else {}
    if eligible:
        partition_validation(frame)
        for part in ["train", "valid", "test"]:
            selected = frame[frame.split.eq(part)].sort_values("record_id")
            exported = selected[META + FEATURES + ["target"]].rename(
                columns={"target": target_name}
            )
            files[part] = save_csv(exported, folder / f"{part}.csv")
    else:
        # A small currency cohort remains available for review, without a misleading tiny test set.
        exported = frame[META + FEATURES + ["target"]].rename(columns={"target": target_name})
        files["insufficient_data"] = save_csv(exported, folder / "insufficient_data.csv")
    current_paths = {item["path"] for item in files.values()}
    for item in previous_files.values():
        old = ROOT / item["path"]
        if old.parent == folder and item["path"] not in current_paths:
            old.unlink(missing_ok=True)
    metadata = {
        "cohort": name,
        "parent_cohort": parent,
        "rows": len(frame),
        "groups": int(count_groups),
        "currency": frame.currency.iloc[0],
        "target": target_name,
        "salary_basis": frame.salary_basis.iloc[0],
        "target_definition": frame.target_definition.iloc[0],
        "files": files,
        "split_prepared": bool(eligible),
        "label_validation_scope": "downloaded_fields_not_independent_ground_truth",
        "source_terms_note": "DataForge terms unresolved; see docs/DATA_SOURCES.md"
        if name.startswith("dataforge_")
        else "Source provenance limits remain; see docs/DATA_SOURCES.md",
        "features": FEATURES,
        "metadata_not_features": META,
        "missing_experience_rows": int(frame.experience_missing.sum()),
        "missing_skills_rows": int(frame.skills_missing.sum()),
        "source_counts": frame.source_dataset.value_counts().to_dict(),
        "role_counts": frame.role.value_counts().to_dict(),
        "partition_profiles": {
            part: {
                "rows": len(group),
                "groups": int(group.leakage_group_id.nunique()),
                "sources": group.source_dataset.value_counts().to_dict(),
                "roles": group.role.value_counts().to_dict(),
                "missing_experience": int(group.experience_missing.sum()),
                "missing_skills": int(group.skills_missing.sum()),
            }
            for part, group in frame.groupby("split")
        }
        if eligible
        else {},
    }
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "manifest.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=ROOT / "configs/label_review.json")
    parser.add_argument(
        "--freeze", action="store_true", help="Lock this version's input/code signature"
    )
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text())
    cleaning_path = ROOT / "outputs/data_quality/cleaning/all_sources.json"
    cleaning = json.loads(cleaning_path.read_text())
    inspections_path = ROOT / "configs/label_inspections.csv"
    inspections = pd.read_csv(inspections_path).to_dict("records")
    code_hashes = {
        name: checksum(ROOT / "scripts" / name)
        for name in ["label_review.py", "prepare_salary_splits.py"]
    }
    signature = digest(
        json.dumps(
            {
                "policy": policy,
                "code": code_hashes,
                "cleaning": checksum(cleaning_path),
                "inspections": checksum(inspections_path),
            },
            sort_keys=True,
        )
    )
    split_dir = ROOT / "data/splits" / ("v" + policy["version"])
    frozen_path = split_dir / "FROZEN.json"
    if frozen_path.exists() and json.loads(frozen_path.read_text())["signature"] != signature:
        raise ValueError("Frozen split version differs; bump policy.version for a new experiment")
    candidates, inputs = load_candidates(cleaning)
    unknown = {row["record_id"] for row in inspections} - set(candidates.record_id)
    if unknown:
        raise ValueError(f"Inspection IDs absent from candidates: {unknown}")
    print("Checking labels and grouping similar job posts...", flush=True)
    reviewed = review_labels(candidates, policy, inspections)
    reviewed, edges = group_records(reviewed, policy)
    accepted = reviewed[reviewed.review_status.eq("accepted")].copy()
    # Each family has its own target. DataForge currencies share group assignments across files.
    family = accepted.source_dataset.map(
        {
            "user_vietnam_it_jobs": "vn",
            "vietjobs_2025": "vn",
            "stackoverflow_2025": "survey",
            "dataforge_2026_08": "dataforge",
        }
    )
    assigned = pd.concat(
        [
            assign_splits(group, policy["seed"], policy["fractions"])
            for _, group in accepted.groupby(family)
        ],
        ignore_index=True,
    )
    partition_validation(assigned)
    review_dir = ROOT / "data/processed/reviewed" / ("v" + policy["version"])
    report_dir = ROOT / "outputs/label_review" / ("v" + policy["version"])
    for folder in [split_dir, review_dir, report_dir]:
        folder.mkdir(parents=True, exist_ok=True)
    cohorts = [
        write_cohort(name, group, policy, split_dir) for name, group in assigned.groupby("cohort")
    ]
    developers = assigned[
        assigned.cohort.eq("vn_it") & assigned.role.isin(policy["developer_roles"])
    ].copy()
    cohorts.append(write_cohort("vn_developer", developers, policy, split_dir, parent="vn_it"))
    files = {
        "reviewed_all": save_csv(reviewed, review_dir / "all_candidates.csv"),
        "quarantined": save_csv(
            reviewed[reviewed.review_status.eq("review")], review_dir / "quarantined.csv"
        ),
        "duplicates": save_csv(
            reviewed[reviewed.review_status.eq("duplicate")], review_dir / "duplicates.csv"
        ),
        "group_edges": save_csv(edges, report_dir / "group_edges.csv"),
        "assignments": save_csv(
            assigned[META + ["cohort", "split"]], split_dir / "assignments.csv"
        ),
    }
    # Material for spot-checks includes downloaded evidence; sampling does not claim gold labels.
    sample = pd.concat(
        [
            group.sample(min(12, len(group)), random_state=policy["seed"])
            for _, group in reviewed.groupby("source_dataset")
        ],
        ignore_index=True,
    )
    files["sample"] = save_csv(sample, report_dir / "sample_for_inspection.csv")
    stats = reviewed.groupby(["source_dataset", "review_status"]).size().unstack(fill_value=0)
    stats.to_csv(report_dir / "review_summary.csv")
    report = {
        "policy": policy,
        "policy_sha256": digest(json.dumps(policy, sort_keys=True)),
        "cleaning_report_sha256": checksum(cleaning_path),
        "input_files": inputs,
        "inspections_sha256": checksum(inspections_path),
        "code_sha256": code_hashes,
        "signature": signature,
        "candidate_rows": len(reviewed),
        "accepted_rows": len(accepted),
        "review_rows": int(reviewed.review_status.eq("review").sum()),
        "duplicate_rows": int(reviewed.review_status.eq("duplicate").sum()),
        "inspected_record_decisions": len(inspections),
        "scope": (
            "Rule-based full audit plus Codex source-field inspections; not human gold labels"
        ),
        "split_method": (
            "Seeded shuffled groups, independent of salary labels; not a temporal holdout"
        ),
        "predictor_feature_fitting_performed": False,
        "deduplication_representation": "TF-IDF on title/body for grouping only; never model input",
        "model_training_performed": False,
        "primary_cohort": "vn_developer",
        "cohorts": cohorts,
        "files": files,
        "group_edge_types": edges.kind.value_counts().to_dict(),
        "invariants": {
            "no_record_overlap": True,
            "no_group_overlap": True,
            "parent_child_assignments_identical": True,
            "features_whitelisted": True,
        },
    }
    manifest_path = report_dir / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.freeze:
        frozen_path.write_text(
            json.dumps(
                {
                    "signature": signature,
                    "manifest_sha256": checksum(manifest_path),
                    "manifest_path": str(manifest_path.relative_to(ROOT)),
                },
                indent=2,
            )
            + "\n"
        )
    print(stats.to_string())
    print(
        pd.DataFrame(
            [
                {
                    "cohort": c["cohort"],
                    "rows": c["rows"],
                    "groups": c["groups"],
                    "train": c["files"].get("train", {}).get("rows", 0),
                    "valid": c["files"].get("valid", {}).get("rows", 0),
                    "test": c["files"].get("test", {}).get("rows", 0),
                    "prepared": c["split_prepared"],
                }
                for c in cohorts
            ]
        ).to_string(index=False)
    )


if __name__ == "__main__":
    main()

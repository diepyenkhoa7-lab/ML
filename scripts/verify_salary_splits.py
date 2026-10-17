"""Verify frozen salary datasets, provenance and split leakage contracts."""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from scripts.clean_data import FEATURES, checksum  # noqa: E402
from scripts.label_review import assign_splits, digest  # noqa: E402
from scripts.prepare_salary_splits import META  # noqa: E402

policy = json.loads((root / "configs/label_review.json").read_text())
version = "v" + policy["version"]
directory = root / "outputs/label_review" / version
report = json.loads((directory / "manifest.json").read_text())
frozen = json.loads((root / "data/splits" / version / "FROZEN.json").read_text())
assert frozen["manifest_sha256"] == checksum(directory / "manifest.json"), "frozen manifest"
assert frozen["signature"] == report["signature"], "frozen signature"
for name, h in report["code_sha256"].items():
    assert checksum(root / "scripts" / name) == h, name
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--training-only", action="store_true", help="Verify published frozen CSVs only"
)
args = parser.parse_args()
if args.training_only:
    counts = {}
    for cohort in report["cohorts"]:
        registries = {key: {} for key in ("record_id", "leakage_group_id")}
        for part, item in cohort["files"].items():
            path = root / item["path"]
            assert checksum(path) == item["sha256"], str(path)
            data = pd.read_csv(path)
            assert len(data) == item["rows"]
            assert set(data) == set(META + FEATURES + [cohort["target"]])
            assert data.record_id.is_unique
            assert data[cohort["target"]].gt(0).all()
            assert np.isfinite(data[cohort["target"]]).all()
            for key, registry in registries.items():
                for value in data[key]:
                    assert value not in registry or registry[value] == part, "partition overlap"
                    registry[value] = part
        counts[cohort["cohort"]] = cohort["rows"]
    print(
        json.dumps(
            dict(
                status="passed",
                scope="frozen CSV integrity only; raw audit excluded",
                cohorts=counts,
            ),
            indent=2,
        )
    )
    raise SystemExit(0)
for item in report["input_files"]:
    assert checksum(root / item["path"]) == item["sha256"], item["path"]
for item in report["files"].values():
    assert checksum(root / item["path"]) == item["sha256"], item["path"]
assert checksum(root / "configs/label_inspections.csv") == report["inspections_sha256"]
assert digest(json.dumps(policy, sort_keys=True)) == report["policy_sha256"]
reviewed = pd.read_csv(root / report["files"]["reviewed_all"]["path"], low_memory=False)
assigned = pd.read_csv(root / report["files"]["assignments"]["path"])
accepted = reviewed[reviewed.review_status.eq("accepted")].set_index("record_id")
assert set(accepted.index) == set(assigned.record_id), "accepted membership"
assert assigned.record_id.is_unique
assert assigned.groupby("leakage_group_id").split.nunique().max() == 1, "group overlap"
assert (
    len(reviewed)
    == report["candidate_rows"]
    == report["accepted_rows"] + report["review_rows"] + report["duplicate_rows"]
)
assert accepted.group_id.is_unique, "hard duplicate remains"
edges = pd.read_csv(root / report["files"]["group_edges"]["path"])
lookup = reviewed.set_index("record_id").leakage_group_id.to_dict()
assert all(lookup[a] == lookup[b] for a, b in zip(edges.left, edges.right)), "edge mismatch"
family = accepted.source_dataset.map(
    {
        "user_vietnam_it_jobs": "vn",
        "vietjobs_2025": "vn",
        "stackoverflow_2025": "survey",
        "dataforge_2026_08": "dataforge",
    }
)
for _, group in accepted.reset_index().groupby(family.to_numpy()):
    again = assign_splits(group, policy["seed"], policy["fractions"])
    actual = assigned.set_index("record_id").loc[again.record_id, "split"].tolist()
    assert actual == again.split.tolist(), "split reproducibility"
cohort_rows = []
for cohort in report["cohorts"]:
    members = []
    for part, item in cohort["files"].items():
        path = root / item["path"]
        assert checksum(path) == item["sha256"], str(path)
        data = pd.read_csv(path)
        assert len(data) == item["rows"]
        assert set(data) == set(META + FEATURES + [cohort["target"]]), "feature whitelist"
        assert data.record_id.is_unique
        assert data[cohort["target"]].gt(0).all() and np.isfinite(data[cohort["target"]]).all()
        native = accepted.loc[data.record_id]
        assert np.allclose(
            native.target.to_numpy(), data[cohort["target"]].to_numpy(), rtol=1e-12
        ), "target changed"
        assert native.currency.eq(cohort["currency"]).all()
        assert native.salary_basis.eq(cohort["salary_basis"]).all()
        if cohort["cohort"].startswith("vn_"):
            assert native.country.eq("Vietnam").all(), "Vietnam country mismatch"
        if part in ["train", "valid", "test"]:
            assert assigned.set_index("record_id").loc[data.record_id, "split"].eq(part).all()
            assert len(data) >= policy["minimum_partition_rows"]
        members.extend(data.record_id)
    assert len(members) == cohort["rows"] and len(set(members)) == len(members)
    if cohort["cohort"] == "vn_developer":
        expected = set(
            accepted[
                accepted.cohort.eq("vn_it") & accepted.role.isin(policy["developer_roles"])
            ].index
        )
        assert set(members) == expected, "developer subset"
    cohort_rows.append(
        dict(
            cohort=cohort["cohort"],
            rows=cohort["rows"],
            groups=cohort["groups"],
            split_prepared=cohort["split_prepared"],
        )
    )
cleaning = json.loads((root / "outputs/data_quality/cleaning/all_sources.json").read_text())
for source in cleaning["sources"]:
    assert checksum(root / source["raw_path"]) == source["raw_sha256"]
result = dict(
    status="passed",
    manifest_sha256=checksum(directory / "manifest.json"),
    candidate_rows=len(reviewed),
    accepted_rows=len(accepted),
    quarantined_rows=report["review_rows"],
    duplicate_rows=report["duplicate_rows"],
    detected_groups_crossing_partitions=0,
    overlapping_record_ids=0,
    checks=[
        "Frozen manifest, policy, source and code hashes match",
        "All raw data unchanged",
        "Every candidate accepted, quarantined or duplicate",
        "All exported labels match candidate fields and units",
        "All Vietnam cohort rows have Vietnam country",
        "No detected group or record crosses partitions",
        "Independent split regeneration matches assignments",
        "Developer subset follows parent split exactly",
        "Feature whitelist enforced in every exported CSV",
        "Small cohorts not assigned misleading tiny holdouts",
        "This verifier does not fit predictors or train models; SFT is validated separately",
    ],
    scope="Integrity and defined rules; unknown duplicates and source label errors may remain",
    cohorts=cohort_rows,
)
(directory / "validation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "cohorts"}, indent=2, ensure_ascii=False))

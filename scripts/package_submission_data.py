"""Package the serving datasets and latest reviewed trial; never train or alter splits."""

import argparse
import ast
import csv
import hashlib
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/submission/datasets.zip"
SALARY = "models/salary/v2_042e3aa1a886/manifest.json"
ADAPTER = "adapters/gemma-jobs/20261017T105728Z/manifest.json"
CORPUS = "data/finetune_full/v1.0.0"
TRIAL = "data/finetune_reviewed/v2.2.0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads((ROOT / path).read_text())


def row_count(path, data):
    text = data.decode("utf-8-sig")
    if path.endswith(".csv"):
        return sum(1 for _ in csv.DictReader(io.StringIO(text)))
    if path.endswith(".jsonl"):
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        return len(rows)
    return None


def collect():
    files, entries = {}, {}

    def add(path, purpose, expected_hash=None, expected_rows=None):
        source = ROOT / path
        if source.is_symlink() or not source.is_file() or not source.is_relative_to(ROOT):
            raise ValueError(f"Invalid input: {path}")
        data = source.read_bytes()
        digest, rows = sha(data), row_count(path, data)
        if expected_hash and digest != expected_hash:
            raise ValueError(f"Frozen hash mismatch: {path}")
        if expected_rows is not None and rows != expected_rows:
            raise ValueError(f"Frozen row count mismatch: {path}")
        files[path] = data
        entries[path] = dict(path=path, purpose=purpose, bytes=len(data), sha256=digest, rows=rows)

    config = read_json("configs/application.json")
    model = read_json(SALARY)
    if config["salary_experiment"] != model["experiment_id"]:
        raise ValueError("Serving salary model changed; review package profile first")
    tree = ast.parse((ROOT / "backend/app/services/gemma.py").read_text())
    active = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "ADAPTER" for target in node.targets)
    )
    if active != str(Path(ADAPTER).parent):
        raise ValueError("Serving Gemma adapter changed; review package profile first")
    add(SALARY, "serving_salary_lineage")
    for key in ["dataset_manifest", "training_snapshot"]:
        item = model[key]
        add(item["path"], "serving_salary", item["sha256"])
    salary_data = read_json(model["dataset_manifest"]["path"])
    for split, item in salary_data["files"].items():
        add(item["path"], f"serving_salary_{split}", item["sha256"], item["rows"])
    add(ADAPTER, "serving_gemma_lineage")
    add(f"{CORPUS}/manifest.json", "serving_gemma", read_json(ADAPTER)["sft_manifest_sha256"])
    for directory, purpose in [(CORPUS, "serving_gemma"), (TRIAL, "failed_trial_not_serving")]:
        manifest = read_json(f"{directory}/manifest.json")
        add(f"{directory}/manifest.json", purpose)
        for split, item in manifest["splits"].items():
            add(
                f"{directory}/{split}.jsonl", f"{purpose}_{split}", item["sha256"], item["examples"]
            )
    # Include the clean source tables and legacy split inputs referenced by serving SFT.
    for item in read_json(f"{CORPUS}/manifest.json")["inputs"]:
        add(item["path"], "serving_gemma_source", item["sha256"], item["rows"])
    for source in ["user_vietnam_it_jobs", "vietjobs_2025"]:
        add(f"data/processed/cleaned/{source}/manifest.json", "cleaning_provenance")
        add(f"data/raw/{source}/manifest.json", "raw_source_metadata_only")
    for path in [
        "data/raw/tinixai_2026/manifest.json",
        "data/raw/tinixai_2026/README.md",
        "data/raw/vietjobs_2025/SOURCE_README.md",
        "data/raw/vietjobs_2025/REPOSITORY_LICENSE.txt",
        "data/DATA_CARD.md",
        "docs/DATA_SOURCES.md",
        "docs/DATASET_HANDOFF.md",
        "configs/application.json",
        "configs/salary_v2_protocol.json",
        "configs/gemma_corrected_protocol.json",
        "outputs/metrics/gemma_corrected_v22/selection.json",
        "data/annotation/gemma_v2.0.0/manifest.json",
        "data/annotation/gemma_v2.0.0/review.jsonl",
        f"{TRIAL}/label_decisions.jsonl",
        "data/references/README.md",
        "data/references/itviec_2025_2026.csv",
        "data/references/topdev_2024_2025.csv",
    ]:
        add(path, "reference_or_provenance_not_extra_training_rows")
    return files, [entries[path] for path in sorted(entries)]


def verify(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entries")
        manifest = json.loads(archive.read("MANIFEST.json"))
        expected = {item["path"] for item in manifest["files"]}
        if set(names) != expected | {"MANIFEST.json"}:
            raise ValueError("Archive contents differ from manifest")
        for item in manifest["files"]:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe archive path")
            data = archive.read(item["path"])
            if len(data) != item["bytes"] or sha(data) != item["sha256"]:
                raise ValueError(f"Archive hash mismatch: {item['path']}")
            if row_count(item["path"], data) != item["rows"]:
                raise ValueError(f"Archive row count mismatch: {item['path']}")
    return dict(files=len(expected), bytes=path.stat().st_size, sha256=sha(path.read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path, help="Verify an existing ZIP without rebuilding")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify), indent=2))
        return
    files, entries = collect()
    manifest = dict(
        schema_version="career.submission.datasets.v1",
        serving_salary=read_json(SALARY)["experiment_id"],
        serving_gemma=str(Path(ADAPTER).parent),
        latest_trial="completed_validation_failed_not_deployed",
        quality="silver; zero independently human-reviewed gold labels",
        scope="Frozen datasets for serving models and latest reviewed trial, not all raw downloads",
        documentation="docs/DATASET_HANDOFF.md",
        self_excluded_from_hashes=True,
        files=entries,
    )
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=OUTPUT.parent, suffix=".tmp")
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, data in sorted(files.items()):
                info = zipfile.ZipInfo(path, date_time=(2026, 10, 18, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        result = verify(Path(temporary))
        os.replace(temporary, OUTPUT)
    finally:
        Path(temporary).unlink(missing_ok=True)
    (OUTPUT.parent / "MANIFEST.json").write_bytes(files["MANIFEST.json"])
    result["path"] = str(OUTPUT.relative_to(ROOT))
    (OUTPUT.parent / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

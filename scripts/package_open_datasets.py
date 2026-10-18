"""Package frozen international training tables, public-source provenance and licenses."""

import json
import os
import tempfile
import zipfile
from pathlib import Path

from package_submission_data import ROOT, row_count, sha, verify

EXPERIMENTS = ["global_survey_v1_7f2c2dbf6989", "open_aijobs_v1_ceea75a58f85"]
OUTPUT = ROOT / "outputs/submission/open_datasets.zip"


def main():
    files, entries = {}, []

    def add(relative, purpose, digest=None, rows=None):
        path = ROOT / relative
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("Unsafe data path")
        data = path.read_bytes()
        actual_rows = row_count(relative, data)
        if digest and sha(data) != digest:
            raise ValueError("Frozen hash mismatch: " + relative)
        if rows is not None and actual_rows != rows:
            raise ValueError("Frozen row count mismatch: " + relative)
        files[relative] = data
        entries.append(
            dict(
                path=relative, purpose=purpose, bytes=len(data), sha256=sha(data), rows=actual_rows
            )
        )

    for experiment in EXPERIMENTS:
        path = f"data/splits/{experiment}/manifest.json"
        manifest = json.loads((ROOT / path).read_text())
        add(path, "frozen_split_lineage")
        for split, item in manifest["files"].items():
            add(item["path"], f"{experiment}_{split}", item["sha256"], item["rows"])
    for source in json.loads((ROOT / "configs/open_salary_sources_20261018.json").read_text())[
        "sources"
    ]:
        for item in source["files"]:
            if not item["path"].endswith(".csv"):
                add(item["path"], "upstream_attribution_and_license", item["sha256"])
        for filename in ["manifest.json", "USAGE.md"]:
            add(f"data/raw/{source['id']}/{filename}", "raw_download_provenance")
    for path in [
        "configs/open_salary_sources_20261018.json",
        "configs/global_survey_protocol.json",
        "configs/open_aijobs_protocol.json",
        "docs/INTERNATIONAL_DATA.md",
    ]:
        add(path, "reproduction_protocol")
    manifest = dict(
        schema_version="career.open.datasets.v1",
        unit="USD/year",
        scope="Frozen derived tables; full raw snapshots fetched by pinned URLs/checksums",
        attribution=(
            "Stack Overflow 2024: ODbL-1.0/DbCL-1.0; AIJobs: CC0-1.0; "
            "Level: metadata only, CC-BY-4.0 compilation"
        ),
        files=sorted(entries, key=lambda e: e["path"]),
    )
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=OUTPUT.parent, suffix=".tmp")
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for path, data in sorted(files.items()):
                info = zipfile.ZipInfo(path, date_time=(2026, 10, 18, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        result = verify(Path(temporary))
        os.replace(temporary, OUTPUT)
    finally:
        Path(temporary).unlink(missing_ok=True)
    (OUTPUT.parent / "OPEN_MANIFEST.json").write_bytes(files["MANIFEST.json"])
    result["path"] = str(OUTPUT.relative_to(ROOT))
    (OUTPUT.parent / "open_verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

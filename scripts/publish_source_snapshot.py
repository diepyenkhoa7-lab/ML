"""Build a bounded source snapshot; optionally create a separate Git publication branch.

Preserves checkout, normal index, original refs and all local datasets. Does not push.
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from clean_data import checksum

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "publish/salary-gemma-prep"
MANIFEST = ROOT / "outputs/source_publication/manifest.json"


def collect_files():
    # Publish reviewed/released runs only; do not capture another manual training job.
    reviewed_runs = set()
    if MANIFEST.exists():
        for item in json.loads(MANIFEST.read_text()).get("files", []):
            parts = Path(item["path"]).parts
            if parts[:2] == ("outputs", "training_logs") and len(parts) > 2:
                if parts[2].startswith("gemma_"):
                    reviewed_runs.add(parts[2].removeprefix("gemma_"))
            if parts[:2] == ("adapters", "gemma-jobs") and len(parts) > 2:
                reviewed_runs.add(parts[2])
    for metrics in (ROOT / "outputs/metrics").glob("gemma_*_adapter_valid/metrics.json"):
        reviewed_runs.add(Path(json.loads(metrics.read_text())["adapter"]).name)
    for reviewed_selection in (ROOT / "outputs/metrics").glob("gemma_*/selection.json"):
        selection = json.loads(reviewed_selection.read_text())
        if "candidate_sha256" not in selection:
            continue
        candidate = Path(selection["candidate"])
        assert candidate.parts[:2] == ("adapters", "gemma-jobs")
        assert checksum(ROOT / candidate / "adapters.safetensors") == selection["candidate_sha256"]
        reviewed_runs.add(candidate.name)
    files = set()
    for name in [
        "README.md",
        "CHANGELOG.md",
        "Makefile",
        ".gitignore",
        ".python-version",
        ".env.example",
        "pyproject.toml",
        "data/DATA_CARD.md",
    ]:
        files.add(ROOT / name)
    files.update(ROOT.glob("requirements*.txt"))
    for directory in [
        "scripts",
        "tests",
        "configs",
        "docs",
        "backend",
        "frontend",
        "reports",
        "notebooks",
        "data/examples",
        "data/references",
        "data/annotation/v3.1.0",
        "data/annotation/gemma_v2.0.0",
        "data/annotation/gemma_v2.1.0",
        "data/annotation/gemma_v2.1.1",
        "data/finetune_reviewed/v2.0.0",
        "data/finetune_reviewed/v2.2.0",
        "data/splits/v3.0.0",
        "data/splits/v3.1.0",
        "outputs/metrics/salary_v3_b5ae152b9dd5",
        "outputs/metrics/salary_v31_b089fdf458a5",
        "models/salary/v3_b5ae152b9dd5",
        "models/salary/v31_b089fdf458a5",
        "data/splits/v2.1.0",
        "outputs/research/2026-10-18",
        "outputs/metrics/salary_v2_042e3aa1a886",
        "models/salary/v2_042e3aa1a886",
        "data/finetune",
        "data/finetune_full",
        "data/splits/v1.0.1",
        "outputs/label_review/v1.0.1",
        "outputs/environment",
        "outputs/notebook_preparation",
        "outputs/app_verification",
        "outputs/architecture_audit",
        "outputs/eda/20261017T092843Z_e3747c",
        "outputs/metrics/salary_bd9af2fa002caae8",
        "outputs/metrics/gemma_20261017T094853Z_base_valid",
        "outputs/metrics/gemma_20261017T094853Z_adapter_valid",
        "outputs/metrics/gemma_20261017T094853Z_comparison",
        "outputs/training_logs",
        "outputs/gemma_preparation",
        "models/salary/bd9af2fa002caae8",
    ]:
        files.update(p for p in (ROOT / directory).rglob("*") if p.is_file())
    for source in ["user_vietnam_it_jobs", "vietjobs_2025"]:
        for name in ["clean.csv", "manifest.json"]:
            files.add(ROOT / "data/processed/cleaned" / source / name)
    # Raw predictions and validation-only selection evidence for later tuning runs.
    for directory in (ROOT / "outputs/metrics").glob("gemma_*"):
        if directory.is_dir():
            files.update(p for p in directory.rglob("*") if p.is_file())
    # Mutable manual one-prompt inference is not an evaluated model artifact.
    files.discard(ROOT / "outputs/environment/gemma_adapter.json")
    # Keep public collection provenance, not full scraped descriptions/HTML or large survey CSVs.
    for source in ["stackoverflow_2026", "public_jobs_20261018", "joboko_20261018"]:
        for pattern in ["manifest.json", "README.md", "*.robots.txt"]:
            files.update((ROOT / "data/raw" / source).glob(pattern))
    for pattern in ["*.json", "*.csv", "*.png", "*.log"]:
        files.update((ROOT / "outputs/research/v3").glob(pattern))
    for name in [
        "data/raw/tinixai_2026/manifest.json",
        "data/raw/tinixai_2026/README.md",
        "models/gemma-source/manifest.json",
        "models/gemma-mlx-4bit/manifest.json",
        "outputs/data_quality/cleaning/all_sources.json",
        "models/README.md",
        "adapters/README.md",
    ]:
        if (ROOT / name).is_file():
            files.add(ROOT / name)
    # Summarized completed runs only; intermediate checkpoints and base weights stay local.
    for manifest_path in (ROOT / "adapters/gemma-jobs").glob("*/manifest.json"):
        if manifest_path.parent.name not in reviewed_runs or not json.loads(
            manifest_path.read_text()
        ).get("training_completed"):
            continue
        for name in ["adapters.safetensors", "adapter_config.json", "manifest.json"]:
            files.add(manifest_path.parent / name)
    excluded = {".backups", ".ipynb_checkpoints", "__pycache__", "node_modules", "dist"}
    files = {
        p
        for p in files
        if not excluded.intersection(p.relative_to(ROOT).parts)
        and p.suffix not in {".pyc", ".pyo"}
        and p.name != ".DS_Store"
        and not (
            p.relative_to(ROOT).parts[:2] == ("outputs", "training_logs")
            and p.relative_to(ROOT).parts[2].startswith("gemma_")
            and p.relative_to(ROOT).parts[2].removeprefix("gemma_") not in reviewed_runs
        )
    }
    # Reject credential formats without echoing any matched content.
    secret = re.compile(
        rb"hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{30,}|"
        rb"github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"
    )
    for path in files:
        assert path.is_file() and not path.is_symlink(), str(path)
        assert path.stat().st_size < 20 * 1024 * 1024, f"Oversized publication file: {path}"
        assert not secret.search(path.read_bytes()), f"Potential credential in {path}"
    return sorted(files)


def git(*args, env=None, input=None):
    return subprocess.check_output(["git", *args], cwd=ROOT, env=env, input=input).decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--publish", action="store_true", help="Create/update local source branch only"
    )
    parser.add_argument("--message-file", type=Path, help="Commit message for this source snapshot")
    args = parser.parse_args()
    files = collect_files()
    items = [
        {"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": checksum(p)}
        for p in files
    ]
    record = {
        "branch": BRANCH,
        "mode": "separate_history_source_snapshot",
        "preserved_history_branch": "feat/salary-training-gemma-prep",
        "includes": (
            "source, executed notebooks, frozen splits, two VN clean CSVs, "
            "silver JSONL, salary pipelines, small final Gemma adapter and logs"
        ),
        "excludes": (
            "raw/bulky audit CSVs, old failed splits, Gemma base weights, "
            "intermediate adapter checkpoints, unreviewed Gemma runs, user upload/runtime, "
            "caches, credentials"
        ),
        "reproduction": "docs/TRAINING_RUNBOOK.md",
        "self_excluded_from_hashes": True,
        "files": items,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    record["generated_at_utc"] = (
        previous["generated_at_utc"]
        if previous.get("files") == items
        else datetime.now(timezone.utc).isoformat()
    )
    MANIFEST.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    files.append(MANIFEST)
    print(
        json.dumps(
            dict(
                files=len(files),
                total_bytes=sum(p.stat().st_size for p in files),
                max_file_bytes=max(p.stat().st_size for p in files),
                manifest=str(MANIFEST),
            ),
            indent=2,
        )
    )
    if not args.publish:
        print("Plan only; no Git refs modified, no push.")
        return
    ref = f"refs/heads/{BRANCH}"
    found = (
        subprocess.run(["git", "show-ref", "--verify", "--quiet", ref], cwd=ROOT).returncode == 0
    )
    parent = git("rev-parse", ref) if found else None
    with tempfile.TemporaryDirectory(prefix="ml-source-index-") as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "index"))
        git("read-tree", "--empty", env=env)
        listing = Path(temporary) / "files.nul"
        listing.write_bytes(b"".join(str(p.relative_to(ROOT)).encode() + b"\0" for p in files))
        git("add", "-f", "--pathspec-from-file=" + str(listing), "--pathspec-file-nul", env=env)
        tree = git("write-tree", env=env)
        if parent and git("rev-parse", parent + "^{tree}") == tree:
            commit = parent
        else:
            message = (
                "feat(ml): publish salary and Gemma experiment artifacts\n\n"
                "Run EDA and baseline/Ridge/Random Forest on frozen VN developer splits; "
                "select RF by validation MAE and report all test metrics.\n"
                "Prepare traceable silver extraction JSONL, verified Google/MLX weight "
                "manifests and plan-only Gemma training with explicit confirmation.\n"
                "Keep bulky data and old Git history local; publish bounded source snapshot "
                "without force-push. See CHANGELOG.md and TRAINING_RUNBOOK.md.\n"
                "Validation: unit tests, Ruff, full frozen-source audit, strict JSONL checks, "
                "executed salary notebooks and pipeline reload. "
                "Latest Gemma status and metrics are recorded in the run logs.\n"
            )
            if args.message_file:
                message = args.message_file.read_text()
            params = ["commit-tree", tree] + (["-p", parent] if parent else [])
            commit = git(*params, input=message.encode())
            git("update-ref", ref, commit, parent or "0" * 40)
    print(
        json.dumps(
            dict(branch=BRANCH, commit=commit, pushed=False, original_checkout_preserved=True)
        )
    )


if __name__ == "__main__":
    main()

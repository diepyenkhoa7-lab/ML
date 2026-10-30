import json
import os
import subprocess
import sys
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]


def test_cli_previews_real_source_as_json():
    result = subprocess.run(
        [sys.executable, "-m", "career_market", "preview", "jobs-2026", "--limit", "1"],
        cwd=APP_ROOT,
        env={**os.environ, "PYTHONPATH": str(APP_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    preview = json.loads(result.stdout)
    assert preview["row_count"] == 1550
    assert preview["source"]["source_id"] == "jobs-2026"
    assert preview["records"][0]["raw"]["title"] == "GẤP\nUnity Developer (2+ Yoe) – Game Mobile"


def test_cli_reports_input_error_without_traceback():
    result = subprocess.run(
        [sys.executable, "-m", "career_market", "preview", "unknown"],
        cwd=APP_ROOT,
        env={**os.environ, "PYTHONPATH": str(APP_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Nguồn không được duyệt: unknown" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""


def test_cli_lists_approved_source_catalog():
    result = subprocess.run(
        [sys.executable, "-m", "career_market", "sources"],
        cwd=APP_ROOT,
        env={**os.environ, "PYTHONPATH": str(APP_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert [source["source_id"] for source in json.loads(result.stdout)] == [
        "jobs-2023",
        "jobs-2026",
    ]

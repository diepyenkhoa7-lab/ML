"""CLI smoke through real service results; only HTTP responses are substituted."""

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from career_market import MarketService

APP_ROOT = Path(__file__).parents[1]
ARCHIVE = Path(__file__).parent / "fixtures/download/jobs-2026-v1.zip"


def test_cli_download_verifies_cached_revision_as_json(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    MarketService(raw_dir=tmp_path / "raw").download_source(
        "jobs-2026", cache_dir=tmp_path / "cache"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_market",
            "download",
            "jobs-2026",
            "--raw-dir",
            str(tmp_path / "raw"),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--check-only",
        ],
        cwd=APP_ROOT,
        env={**os.environ, "PYTHONPATH": str(APP_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "cached"
    assert output["source"]["source_id"] == "jobs-2026"
    assert output["source"]["revision"] == 1


@pytest.mark.parametrize(
    "source_id, message",
    [
        ("unknown", "Nguồn không được duyệt: unknown"),
        ("jobs-2026", "Chưa có cache"),
    ],
)
def test_cli_download_errors_are_actionable_without_tracebacks(tmp_path, source_id, message):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_market",
            "download",
            source_id,
            "--raw-dir",
            str(tmp_path / "raw"),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--check-only",
        ],
        cwd=APP_ROOT,
        env={**os.environ, "PYTHONPATH": str(APP_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert message in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""

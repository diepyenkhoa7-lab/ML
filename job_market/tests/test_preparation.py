"""Synthetic logic records only; never bundled as market/training observations."""

import csv
import io
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from career_market import MarketService
from career_market.service import RawRecord


def test_preparation_reconciles_rows_and_keeps_missing_salary_in_eda():
    raw = {
        "title": "Backend Developer",
        "company": "Fixture",
        "location": "HCM/HN/Remote",
        "salary": "20 - 30 triệu",
        "experience": "",
        "date_posted": "2026-01-01",
    }
    records = [
        RawRecord("fixture", None, "https://example.org/1?q=1", raw),
        RawRecord("fixture", None, "https://example.org/1?q=2", raw),
        RawRecord("fixture", None, "https://example.org/2", {**raw, "title": "Sales Executive"}),
    ]
    result = MarketService().prepare_records(records)
    assert result["summary"] == {
        "raw_rows": 3,
        "duplicates": 1,
        "invalid_identity": 0,
        "out_of_scope": 1,
        "role_review": 0,
        "eda_postings": 1,
        "salary_targets": 0,
    }
    assert len(result["rows"]) == 3
    assert result["eda"][0]["locations"] == ["HCM", "HN"]
    assert result["eda"][0]["work_modes"] == ["Remote"]
    assert result["eda"][0]["raw"] == raw
    assert result["duplicates"][0]["duplicate_of"] == result["eda"][0]["row_id"]
    assert result["eda"][0]["experience_min"] is None
    assert result["targets"] == []


def test_real_snapshot_is_reproducible_and_has_empty_salary_targets(tmp_path):
    service = MarketService()
    first = service.snapshot(output_dir=tmp_path / "first")
    second = service.snapshot(output_dir=tmp_path / "second")
    assert first["report"]["summary"]["raw_rows"] == 3606
    assert first["manifest"] == second["manifest"]
    assert first["manifest"]["summary"]["salary_targets"] == 0
    assert first["manifest"]["ml_state"] == "blocked_pending_salary_gate"
    assert len(first["manifest"]["sources"]) == 2
    assert list(csv.DictReader(io.StringIO(first["files"]["salary_targets.csv"].decode()))) == []
    assert "salary_target_vnd_month" in first["files"]["salary_targets.csv"].decode()
    assert json.loads((tmp_path / "first/manifest.json").read_text()) == first["manifest"]
    assert first["files"]["eda.csv"] == second["files"]["eda.csv"]


def test_quality_page_shows_real_reconciliation_and_blocked_ml():
    page = Path(__file__).parents[1] / "pages/7_Chat_luong.py"
    app = AppTest.from_file(str(page), default_timeout=30).run()
    assert not app.exception
    assert [m.value for m in app.metric] == ["3606", "322", "0", "0"]
    assert any("ML bị chặn" in item.value for item in app.info)
    assert app.get("download_button")[0].proto.url

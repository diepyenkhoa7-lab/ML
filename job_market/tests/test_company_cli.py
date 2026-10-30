"""Fresh process adapter proof with synthetic prepared rows."""

import json
import os
import subprocess
import sys

from career_market.company_service import CompanyMarketService as MarketService


def test_company_cli_exports_the_service_report_from_prepared_json(tmp_path):
    rows = [
        {"source_id": "fixture", "posting_id": "a", "company_raw": "Example"},
        {"source_id": "fixture", "posting_id": "b", "company_raw": "EXAMPLE"},
    ]
    input_path = tmp_path / "prepared.json"
    input_path.write_text(json.dumps({"rows": rows}))
    csv_path = tmp_path / "groups.csv"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "career_market.company_cli",
            "--input",
            str(input_path),
            "--output",
            str(csv_path),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    assert result.returncode == 0, result.stderr
    expected = MarketService().company_report(rows)
    assert json.loads(result.stdout) == expected
    assert csv_path.read_text() == expected["csv"]


def test_company_cli_invalid_input_is_an_actionable_error(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"rows": [42]}')
    result = subprocess.run(
        [sys.executable, "-m", "career_market.company_cli", "--input", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "prepared" in result.stderr.lower()

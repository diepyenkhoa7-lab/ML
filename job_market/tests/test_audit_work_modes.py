"""Work-mode evidence is separate from technical uses of the word remote."""

from career_market import MarketService
from career_market.service import RawRecord


def test_remote_sensing_is_not_a_remote_work_arrangement():
    record = RawRecord(
        "fixture",
        "1",
        "https://example.org/1",
        {
            "title": "AI Engineer - Remote Sensing",
            "location": "HN",
        },
    )
    row = MarketService().prepare_records([record])["eda"][0]
    assert row["work_modes"] == []
    assert row["work_mode_evidence"] == []


def test_remote_procedure_call_is_technology_not_work_mode():
    record = RawRecord(
        "fixture",
        "1",
        "https://example.org/1",
        {
            "title": "Backend Developer - Remote Procedure Call (RPC)",
            "location": "HN",
        },
    )
    row = MarketService().prepare_records([record])["eda"][0]
    assert row["work_modes"] == []


def test_location_report_remote_selection_agrees_with_prepared_raw_rows():
    service = MarketService()
    prepared = service.prepare(["jobs-2026"])
    expected = {row["posting_id"] for row in prepared["rows"] if "Remote" in row["work_modes"]}
    assert expected
    report = service.location_report("jobs-2026", work_mode="Remote")
    assert {row["posting_id"] for row in report["rows"]} == expected
    assert report["unique_posting_count"] == len(expected)

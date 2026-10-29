"""Synthetic posting identities exercise logic, never dataset observations."""

from career_market import MarketService
from career_market.service import RawRecord


def test_identity_query_separates_distinct_jobs_but_tracking_does_not():
    raw = {"title": "Backend Developer", "location": "HCM", "salary": "Thỏa thuận"}
    records = [
        RawRecord("fixture", "1", "https://example.org/job?id=1&utm_source=one", raw),
        RawRecord("fixture", "2", "https://example.org/job?id=2", raw),
        RawRecord("fixture", "1", "https://example.org/job?utm_source=two&id=1", raw),
    ]
    report = MarketService().prepare_records(records)
    assert (report["summary"]["eda_postings"], report["summary"]["duplicates"]) == (2, 1)
    assert len({row["posting_id"] for row in report["eda"]}) == 2


def test_topcv_tracking_changes_do_not_change_posting_identity():
    rows = [
        {"source_id": "jobs-2026", "job_url": url}
        for url in [
            "https://www.topcv.vn/viec-lam/backend/2005046.html?ta_source=search&u_sr_id=one",
            "https://www.topcv.vn/viec-lam/backend/2005046.html?ta_source=list&u_sr_id=two",
        ]
    ]
    assert len(MarketService().select_locations(rows)) == 1


def test_duplicate_evidence_survives_input_order_and_retains_raw_rows():
    raw = {"title": "Backend Developer", "company": "Fixture", "salary": "Thỏa thuận"}
    records = [
        RawRecord(
            "fixture",
            "1",
            "https://example.org/job/1",
            {
                **raw,
                "location": "HCM",
                "job_requirements": "Java",
            },
        ),
        RawRecord(
            "fixture",
            "1",
            "https://example.org/job/1",
            {
                **raw,
                "location": "HN",
                "job_requirements": "Python",
            },
        ),
    ]
    service = MarketService()
    group_ids = []
    for ordered in [records, list(reversed(records))]:
        report = service.prepare_records(ordered)
        assert (report["summary"]["eda_postings"], report["summary"]["duplicates"]) == (1, 1)
        assert report["eda"][0]["locations"] == ["HCM", "HN"]
        assert report["eda"][0]["skills"] == ["Java", "Python"]
        group_ids.append(report["eda"][0]["repost_group_id"])
        assert len(report["repost_groups"]) == 1
        assert len(report["repost_groups"][0]["row_ids"]) == 2
        assert [row["raw"] for row in report["rows"]] == [record.raw for record in ordered]
    assert group_ids[0] == group_ids[1]


def test_conflicting_duplicate_salary_is_reviewed_not_used_as_target():
    raw = {"title": "Backend Developer", "company": "Fixture", "location": "HCM"}
    records = [
        RawRecord(
            "fixture",
            "1",
            "https://example.org/job/1",
            {
                **raw,
                "salary": "20 triệu VND/tháng",
            },
        ),
        RawRecord(
            "fixture",
            "1",
            "https://example.org/job/1",
            {
                **raw,
                "salary": "30 triệu VND/tháng",
            },
        ),
    ]
    for ordered in [records, list(reversed(records))]:
        report = MarketService().prepare_records(ordered)
        assert report["targets"] == []
        assert report["eda"] == []
        assert report["summary"]["entity_review"] == 1
        assert "salary_raw" in report["review"][0]["entity_conflicts"]


def test_missing_duplicate_salary_uses_supplied_evidence_in_either_order():
    raw = {"title": "Backend Developer", "company": "Fixture", "location": "HCM"}
    records = [
        RawRecord("fixture", "1", "https://example.org/job/1", {**raw, "salary": ""}),
        RawRecord(
            "fixture",
            "1",
            "https://example.org/job/1",
            {
                **raw,
                "salary": "20–30 triệu VND/tháng",
            },
        ),
    ]
    for ordered in [records, list(reversed(records))]:
        report = MarketService().prepare_records(ordered)
        assert len(report["targets"]) == 1
        assert report["targets"][0]["salary_target_vnd_month"] == 25_000_000
        assert len(report["targets"][0]["evidence_row_ids"]) == 2

"""ML02 synthetic identities: service seam only; never training observations."""

from career_market.company_service import CompanyMarketService as MarketService


def row(posting, company, **extra):
    return {
        "source_id": "fixture",
        "posting_id": posting,
        "job_id": posting,
        "job_url": f"https://example.org/{posting}",
        "company_raw": company,
        **extra,
    }


def test_company_aliases_keep_only_case_whitespace_and_unicode_equivalents():
    report = MarketService().company_report(
        [
            row("1", "  CÔNG  TY Á ", locations=["HCM", "HN"], skills=["Java", "Python"]),
            row("2", "công ty A\u0301"),
            row("3", "Cong Ty A"),
            row("4", "CÔNG TY Á Subsidiary"),
            row("5", "Recruiter for CÔNG TY Á"),
        ]
    )
    assert report["summary"] == {
        "rows": 5,
        "entities": 5,
        "companies": 4,
        "groups": 4,
        "review_groups": 0,
    }
    assignments = {r["posting_id"]: r for r in report["rows"]}
    assert assignments["1"]["group_id"] == assignments["2"]["group_id"]
    assert assignments["1"]["company_canonical"] == "công ty á"
    assert len(report["aliases"]) == 5
    assert assignments["1"]["company_raw"] == "  CÔNG  TY Á "


def test_company_and_repost_links_form_transitive_indivisible_groups():
    rows = [
        row("1", "Alpha"),
        row("2", "ALPHA", repost_group_id="repost-a"),
        row("3", "Beta", repost_group_id="repost-a"),
        row("4", "Beta"),
        row("4", "Beta", locations=["HN", "HCM"]),
        row("5", "Gamma"),
    ]
    service = MarketService()
    report = service.company_report(rows)
    groups = {r["posting_id"]: r["group_id"] for r in report["rows"]}
    assert len({groups[p] for p in ("1", "2", "3", "4")}) == 1
    assert groups["5"] != groups["1"]
    assert report["summary"] == {
        "rows": 6,
        "entities": 5,
        "companies": 3,
        "groups": 2,
        "review_groups": 0,
    }
    assert report["groups"] == service.company_report(list(reversed(rows)))["groups"]
    assert any(link["kind"] == "repost_group_id" for link in report["links"])


def test_unresolved_and_conflicting_identities_quarantine_whole_connected_group():
    rows = [
        row("1", "Alpha"),
        row("1", "Beta"),
        row("2", "Alpha"),
        row("3", "", repost_group_id="r"),
        row("4", "Gamma", repost_group_id="r"),
        row(None, "Delta", job_id=None, job_url=""),
        row("5", "Agency", raw={"company_id": "employer-1"}),
        row("6", "Client", raw={"company_id": "employer-1"}),
        row("7", "Safe", entity_conflicts=["salary_raw"]),
    ]
    report = MarketService().company_report(rows)
    assignments = {r["posting_id"]: r for r in report["rows"]}
    assert all(g["status"] == "review" for g in report["groups"])
    assert "conflicting_posting_company" in assignments["2"]["review_reasons"]
    assert "missing_company" in assignments["4"]["review_reasons"]
    assert "missing_posting_identity" in assignments[None]["review_reasons"]
    assert "conflicting_source_company_id" in assignments["5"]["review_reasons"]
    assert "entity_conflict:salary_raw" in assignments["7"]["review_reasons"]
    assert assignments["5"]["company_canonical"] != assignments["6"]["company_canonical"]
    assert report["groups"] == MarketService().company_report(rows[::-1])["groups"]


def test_explicit_duplicate_links_and_source_posting_ids_are_constraints_not_company_aliases():
    rows = [
        row("a", "Alpha", row_id="r1", job_id="shared"),
        row("b", "Beta", row_id="r2", duplicate_of="r1"),
        row("c", "Gamma", row_id="r3", job_id="shared"),
        row("d", "Delta", row_id="r4", duplicate_of="not-present"),
        row("e", "Other", source_id="other", job_id="shared"),
    ]
    report = MarketService().company_report(rows)
    by_id = {r["posting_id"]: r for r in report["rows"]}
    assert len({by_id[p]["group_id"] for p in ["a", "b", "c"]}) == 1
    assert by_id["e"]["group_id"] != by_id["a"]["group_id"]
    assert "conflicting_posting_company" in by_id["a"]["review_reasons"]
    assert "unresolved_duplicate_link" in by_id["d"]["review_reasons"]
    assert by_id["a"]["company_canonical"] != by_id["b"]["company_canonical"]


def test_report_exports_aliases_groups_and_provenance_without_mutating_prepared_overlay():
    import copy
    import csv
    import io
    import json

    rows = [
        row("1", " Alpha ", row_id="fixture:1", salary_label_status="accepted"),
        row("2", "ALPHA", row_id="fixture:2", raw={"company_id": "A"}),
    ]
    before = copy.deepcopy(rows)
    report = MarketService().company_report(rows)
    exported = list(csv.DictReader(io.StringIO(report["csv"])))
    assert [r["group_id"] for r in exported] == [r["group_id"] for r in report["rows"]]
    assert {r["company_raw"] for r in exported} == {" Alpha ", "ALPHA"}
    assert {r["source_id"] for r in exported} == {"fixture"}
    assert json.loads(exported[0]["review_reasons"]) == []
    assert report["policy"]["split_ratios"] == [0.70, 0.15, 0.15]
    assert report["policy"]["split_performed"] is False
    assert report["aliases"][0]["posting_ids"]
    assert rows == before
    empty = MarketService().company_report([])
    assert empty["summary"]["groups"] == 0
    assert "company_canonical" in empty["csv"]


def test_missing_identity_groups_stay_stable_when_preparation_reassigns_row_numbers():
    from career_market.service import RawRecord

    records = [
        RawRecord("fixture", None, "", {"company": "Unknown", "title": "Backend Developer"}),
        RawRecord(
            "fixture",
            "1",
            "https://example.org/1",
            {"company": "Alpha", "title": "Backend Developer"},
        ),
    ]
    service = MarketService()
    forward = service.company_report(service.prepare_records(records)["rows"])
    reverse = service.company_report(service.prepare_records(records[::-1])["rows"])
    assert forward["groups"] == reverse["groups"]


def test_shared_posting_urls_link_across_sources_without_inventing_company_aliases():
    rows = [
        row(
            "source-a:1",
            "Agency",
            source_id="a",
            job_id="1",
            job_url="https://example.org/job/1?utm_source=a",
        ),
        row(
            "source-b:8",
            "Client",
            source_id="b",
            job_id="8",
            job_url="https://example.org/job/1?utm_source=b",
        ),
    ]
    report = MarketService().company_report(rows)
    assert report["summary"]["groups"] == 1
    assert report["summary"]["companies"] == 2
    assert report["groups"][0]["status"] == "review"
    assert "conflicting_posting_company" in report["groups"][0]["review_reasons"]


def test_conflicting_company_ids_are_reviewed_and_compensation_evidence_is_untouched():
    import copy

    rows = [
        row(
            "1",
            "Acme",
            company_source_id="employer-1",
            compensation_scope="advertised_monthly_income",
            salary_label_evidence={"currency": {"raw": "VND", "approved": True}},
        ),
        row("2", "ACME", company_source_id="employer-2"),
    ]
    before = copy.deepcopy(rows)
    report = MarketService().company_report(rows)
    assert report["groups"][0]["status"] == "review"
    assert "conflicting_company_source_ids" in report["groups"][0]["review_reasons"]
    first = next(r for r in report["rows"] if r["posting_id"] == "1")
    assert first["compensation_scope"] == "advertised_monthly_income"
    assert first["salary_label_evidence"] == {"currency": {"raw": "VND", "approved": True}}
    assert rows == before


def test_two_reviewed_labels_from_one_company_cannot_fill_three_company_partitions():
    rows = [
        row(
            "1",
            "YODY",
            salary_target_vnd_month=27_500_000,
            salary_basis="unknown",
            compensation_scope="advertised_monthly_income",
        ),
        row(
            "2",
            "YODY",
            salary_target_vnd_month=37_500_000,
            salary_basis="unknown",
            compensation_scope="advertised_monthly_income",
        ),
        row("3", "Unlabeled"),
        row("4", "Conflict", salary_target_vnd_month=10_000_000, entity_conflicts=["company_raw"]),
    ]
    report = MarketService().company_report(rows)
    readiness = report["split_readiness"]
    assert readiness["independent_groups"] == 3
    assert readiness["usable_labeled_groups"] == 1
    assert readiness["labeled_company_count"] == 1
    assert readiness["labeled_split_group_count"] == 1
    assert readiness["usable_labeled_companies"] == 1
    assert readiness["usable_labeled_entities"] == 2
    assert readiness["minimum_group_count_met"] is False
    assert readiness["training_ready"] is False
    assert "YODY" in readiness["reason"]
    assert "train/validation/test" in readiness["reason"]
    assert readiness["cohorts"][0]["usable_labeled_groups"] == 1

"""A09: downloaded demand artifacts retain the scope of approved new sources."""

import csv
import io
import json

import pytest
from PIL import Image

from career_market import MarketService


@pytest.fixture(scope="module")
def market():
    service = MarketService()
    return service, service.prepare()["eda"]


def test_skill_demand_csv_retains_source_revision_period_filters_and_units(market):
    service, rows = market
    report = service.skill_demand(
        rows, role="Backend", locations=["HCM", "HN"], source_ids=["jobs-2026"], limit=3
    )
    exported = list(csv.DictReader(io.StringIO(report["csv"].decode())))
    assert len(exported) == 3
    metadata = json.loads(exported[0]["export_metadata"])
    assert metadata["sources"][0]["source_id"] == "jobs-2026"
    assert metadata["sources"][0]["revision"] == 1
    assert metadata["sources"][0]["dataset_url"] == (
        "https://www.kaggle.com/datasets/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026"
    )
    assert metadata["observed_period"] == {
        "date_from": "2025-12-18",
        "date_to": "2026-01-15",
        "date_kind": "posting",
    }
    assert metadata["filters"] == {
        "role": "Backend",
        "locations": ["HCM", "HN"],
        "work_mode": None,
        "source_ids": ["jobs-2026"],
        "limit": 3,
    }
    assert metadata["sample_size"] == report["posting_count"]
    assert metadata["units"] == {
        "posting_count": "distinct postings mentioning skill",
        "share_percent": "percent of selected distinct postings",
    }
    assert all(json.loads(row["export_metadata"]) == metadata for row in exported)
    assert [row["skill"] for row in exported] == [row["skill"] for row in report["table"]]


def test_skill_demand_png_carries_its_visible_provenance_footnote(market):
    service, rows = market
    report = service.skill_demand(rows, role="Backend", source_ids=["jobs-2026"], limit=2)
    image = Image.open(io.BytesIO(report["png"]))
    footnote = image.info.get("Description", "")
    assert "jobs-2026 (revision 1)" in footnote
    assert "2025-12-18 – 2026-01-15" in footnote
    assert "Nghề: Backend" in footnote
    assert "Địa điểm: tất cả" in footnote
    assert "Hình thức: tất cả" in footnote
    assert "Lọc nguồn: jobs-2026" in footnote
    assert "Top: 2" in footnote
    assert f"n={report['posting_count']}" in footnote
    assert "Đơn vị: tin duy nhất; tỷ lệ % trên n" in footnote
    assert footnote == report["scope"]


def test_empty_demand_exports_retain_requested_source_and_scope(market):
    service, _ = market
    report = service.skill_demand(
        [],
        role="Backend",
        locations=["HCM"],
        work_mode="Remote",
        source_ids=["jobs-2023"],
        limit=1,
    )
    exported = list(csv.DictReader(io.StringIO(report["csv"].decode())))
    assert len(exported) == 1
    assert exported[0]["record_type"] == "metadata"
    assert exported[0]["skill"] == ""
    metadata = json.loads(exported[0]["export_metadata"])
    assert metadata["sources"][0]["source_id"] == "jobs-2023"
    assert metadata["sources"][0]["revision"] == 2
    assert metadata["sample_size"] == 0
    assert metadata["observed_period"]["date_from"] is None
    assert metadata["observed_period"]["date_to"] is None
    assert metadata["filters"]["work_mode"] == "Remote"
    assert report["table"] == []
    footnote = Image.open(io.BytesIO(report["png"])).info["Description"]
    assert "jobs-2023 (revision 2)" in footnote
    assert "chưa rõ ngày đăng" in footnote
    assert "n=0" in footnote


def test_mixed_source_exports_keep_each_sources_observed_period(market):
    service, rows = market
    report = service.skill_demand(rows, role="Backend", locations=["HCM", "HN"], limit=1)
    exported = next(csv.DictReader(io.StringIO(report["csv"].decode())))
    sources = {
        source["source_id"]: source for source in json.loads(exported["export_metadata"])["sources"]
    }
    assert sources["jobs-2023"]["revision"] == 2
    assert sources["jobs-2023"]["observed_period"] == {
        "date_from": "2023-02-16",
        "date_to": "2023-02-21",
        "date_kind": "posting",
    }
    assert sources["jobs-2026"]["observed_period"] == {
        "date_from": "2025-12-18",
        "date_to": "2026-01-15",
        "date_kind": "posting",
    }
    footnote = Image.open(io.BytesIO(report["png"])).info["Description"]
    assert "jobs-2023 (revision 2): 2023-02-16 – 2023-02-21" in footnote
    assert "jobs-2026 (revision 1): 2025-12-18 – 2026-01-15" in footnote


@pytest.mark.parametrize(
    ("posting_date", "date_kind"),
    [(None, "posting"), ("invalid", "posting"), ("2035-01-01", "deadline")],
)
def test_undated_exports_never_substitute_import_year_or_deadline(market, posting_date, date_kind):
    service, rows = market
    # Controlled copies of an approved new-source row; the dataset stays untouched.
    original = next(row for row in rows if row["source_id"] == "jobs-2026" and row["skills"])
    report = service.skill_demand(
        [{**original, "posting_date": posting_date, "date_kind": date_kind}]
    )
    exported = next(csv.DictReader(io.StringIO(report["csv"].decode())))
    metadata = json.loads(exported["export_metadata"])
    assert metadata["observed_period"] == {
        "date_from": None,
        "date_to": None,
        "date_kind": "posting",
    }
    assert metadata["missing_posting_dates"] == 1
    assert metadata["sample_size"] == 1
    footnote = Image.open(io.BytesIO(report["png"])).info["Description"]
    assert "chưa rõ ngày đăng" in footnote
    assert "Thiếu ngày đăng: 1" in footnote
    assert "2035" not in footnote


def test_postings_without_skills_still_export_their_nonzero_sample(market):
    service, rows = market
    original = next(row for row in rows if row["source_id"] == "jobs-2026")
    report = service.skill_demand([{**original, "skills": []}])
    exported = next(csv.DictReader(io.StringIO(report["csv"].decode())))
    assert exported["record_type"] == "metadata"
    assert exported["sample_size"] == "1"
    assert json.loads(exported["export_metadata"])["sample_size"] == 1
    assert report["table"] == []

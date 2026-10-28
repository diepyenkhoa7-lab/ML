from pathlib import Path

import pytest

from career_market import MarketError, MarketService


def test_preview_preserves_real_2023_record_and_provenance():
    preview = MarketService().preview("jobs-2023", limit=1)
    assert preview.row_count == 2056
    assert len(preview.records) == 1
    assert preview.records[0].raw["job_title"] == "Performance Marketing"
    assert preview.records[0].job_id == "35BB6CB4"
    assert preview.records[0].job_url == (
        "https://careerbuilder.vn/vi/tim-viec-lam/performance-marketing.35BB6CB4.html"
    )
    assert preview.records[0].source_id == "jobs-2023"
    assert preview.source.revision == 2
    assert preview.source.license == "CC0-1.0"
    assert preview.raw_sha256 == "8014c43996075240d309a137f11436c1e3af218afa7e823e83d67ac6f7c85a3c"
    assert len(preview.columns) == 20


def test_catalog_and_2026_preview_expose_source_limits_and_original_url():
    service = MarketService()
    assert [source.source_id for source in service.sources()] == ["jobs-2023", "jobs-2026"]
    preview = service.preview("jobs-2026", limit=1)
    assert preview.row_count == 1550
    assert preview.columns == (
        "title",
        "company",
        "location",
        "experience",
        "salary",
        "date_posted",
        "url",
    )
    assert preview.records[0].job_id is None
    assert preview.records[0].raw["title"] == "GẤP\nUnity Developer (2+ Yoe) – Game Mobile"
    assert "?ta_source=" in preview.records[0].job_url
    assert preview.source.license == "CC-BY-4.0"
    assert preview.source.revision == 1
    assert preview.source.publisher == "baocgb"
    assert preview.source.platform == "TopCV"
    assert preview.source.has_job_description is False
    assert preview.source.salary_period_confirmed is False
    assert preview.source.metadata_url.endswith("baocgb/vietnam-it-jobs-raw-data-from-topcv-2026")
    assert (
        preview.source.archive_sha256
        == "29651eb3e85d4d5b0fb8e45f968e01585c51de95f038cb850dc72607352f0426"
    )
    assert preview.raw_sha256 == "e78ff2b6ed521ad894a70271a3254fcf434813916fdade4f7d449bc4fdf34ef9"


def test_unknown_source_has_actionable_error():
    with pytest.raises(MarketError, match="Nguồn không được duyệt: unknown"):
        MarketService().preview("unknown")


def test_missing_raw_file_has_actionable_error(tmp_path):
    with pytest.raises(MarketError, match="Không đọc được raw.*vietnamese-job-posting.csv"):
        MarketService(raw_dir=tmp_path).preview("jobs-2023")


def test_changed_schema_reports_missing_column(tmp_path):
    original = Path(__file__).parents[1] / "datasets/raw/topcv_jobs.csv"
    content = original.read_bytes().replace(b"title,", b"changed_title,", 1)
    (tmp_path / original.name).write_bytes(content)
    with pytest.raises(MarketError, match="Schema.*title"):
        MarketService(raw_dir=tmp_path).preview("jobs-2026")


def test_changed_raw_content_is_rejected_without_overwriting_it(tmp_path):
    original = Path(__file__).parents[1] / "datasets/raw/topcv_jobs.csv"
    changed = original.read_bytes().replace(b"Unity Developer", b"Unity developer", 1)
    raw_file = tmp_path / original.name
    raw_file.write_bytes(changed)
    with pytest.raises(MarketError, match="SHA-256.*jobs-2026"):
        MarketService(raw_dir=tmp_path).preview("jobs-2026")
    assert raw_file.read_bytes() == changed


def test_truncated_source_reports_expected_and_actual_row_counts(tmp_path):
    original = Path(__file__).parents[1] / "datasets/raw/topcv_jobs.csv"
    (tmp_path / original.name).write_bytes(original.read_bytes().split(b"\n", 1)[0] + b"\n")
    with pytest.raises(MarketError, match="Số dòng.*1550.*0"):
        MarketService(raw_dir=tmp_path).preview("jobs-2026")


@pytest.mark.parametrize(
    "content",
    [b"\xff\xfe", b'title,company,location,experience,salary,date_posted,url\n"unfinished'],
)
def test_unreadable_csv_has_actionable_error(tmp_path, content):
    (tmp_path / "topcv_jobs.csv").write_bytes(content)
    with pytest.raises(MarketError, match="CSV.*jobs-2026"):
        MarketService(raw_dir=tmp_path).preview("jobs-2026")


def test_negative_preview_limit_is_rejected():
    with pytest.raises(MarketError, match="limit"):
        MarketService().preview("jobs-2023", limit=-1)


@pytest.mark.parametrize("limit", [None, 10000])
def test_callers_can_read_every_raw_record_without_modifying_the_source(limit):
    original = Path(__file__).parents[1] / "datasets/raw/topcv_jobs.csv"
    before = original.read_bytes()
    preview = MarketService().preview("jobs-2026", limit=limit)
    assert len(preview.records) == 1550
    assert preview.records[-1].raw["title"] == "Thực Tập Sinh Business Analyst"
    assert original.read_bytes() == before

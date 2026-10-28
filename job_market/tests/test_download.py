"""Public downloader behavior; HTTP fixture is the approved new Kaggle v1 ZIP."""

import io
import json
from http.client import IncompleteRead
from pathlib import Path

import pytest

from career_market import MarketError, MarketService

ARCHIVE = Path(__file__).parent / "fixtures/download/jobs-2026-v1.zip"


def test_downloads_pinned_revision_and_retains_manifest(tmp_path, monkeypatch):
    def fetch(request, *, timeout):
        assert request.full_url == (
            "https://www.kaggle.com/api/v1/datasets/download/"
            "baocgb/vietnam-it-jobs-raw-data-from-topcv-2026?datasetVersionNumber=1"
        )
        return io.BytesIO(ARCHIVE.read_bytes())

    monkeypatch.setattr("urllib.request.urlopen", fetch)
    service = MarketService(raw_dir=tmp_path / "raw")
    result = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    assert result["status"] == "downloaded"
    assert result["source"]["revision"] == 1
    assert result["source"]["license"] == "CC-BY-4.0"
    assert result["raw_sha256"] == (
        "e78ff2b6ed521ad894a70271a3254fcf434813916fdade4f7d449bc4fdf34ef9"
    )
    assert Path(result["manifest_path"]).is_file()
    assert result["downloaded_at"].endswith("+00:00")
    assert service.preview("jobs-2026", limit=1).row_count == 1550


def test_reuses_matching_cache_without_network_and_keeps_download_date(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    service = MarketService(raw_dir=tmp_path / "raw")
    first = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    manifest_before = Path(first["manifest_path"]).read_bytes()

    def offline(*args, **kwargs):
        raise AssertionError("Matching cache must not need HTTP")

    monkeypatch.setattr("urllib.request.urlopen", offline)
    result = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    assert result["status"] == "cached"
    assert result["downloaded_at"] == first["downloaded_at"]
    assert Path(result["manifest_path"]).read_bytes() == manifest_before
    manifest = json.loads(manifest_before)
    assert manifest["download_url"] == first["download_url"]
    assert manifest["source"]["time_fields"] == {"date_posted": "ngày đăng theo nguồn"}


def test_changed_raw_is_reported_without_fetching_or_overwriting(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw = raw_dir / "topcv_jobs.csv"
    raw.write_bytes(b"test-only changed raw, never market data\n")

    def offline(*args, **kwargs):
        raise AssertionError("Changed local source must fail before HTTP")

    monkeypatch.setattr("urllib.request.urlopen", offline)
    with pytest.raises(MarketError, match="SHA-256 raw.*đã thay đổi"):
        MarketService(raw_dir=raw_dir).download_source("jobs-2026", cache_dir=tmp_path / "cache")
    assert raw.read_bytes() == b"test-only changed raw, never market data\n"
    assert not (tmp_path / "cache").exists()


def test_changed_cache_manifest_is_rejected_and_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    service = MarketService(raw_dir=tmp_path / "raw")
    first = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    manifest_path = Path(first["manifest_path"])
    changed = json.loads(manifest_path.read_text())
    changed["source"]["revision"] = 2
    manifest_path.write_text(json.dumps(changed))
    before = manifest_path.read_bytes()
    with pytest.raises(MarketError, match="Manifest.*không khớp"):
        service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    assert manifest_path.read_bytes() == before


def test_changed_remote_archive_is_rejected_before_any_extraction(tmp_path, monkeypatch):
    # Synthetic bytes are only a corrupt HTTP test response, never a dataset.
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: io.BytesIO(b"test-only changed ZIP")
    )
    with pytest.raises(MarketError, match="SHA-256 ZIP.*nguồn đã thay đổi"):
        MarketService(raw_dir=tmp_path / "raw").download_source(
            "jobs-2026", cache_dir=tmp_path / "cache"
        )
    assert list(tmp_path.iterdir()) == []


def test_corrupt_cached_archive_fails_offline_without_replacing_it(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    service = MarketService(raw_dir=tmp_path / "raw")
    first = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    archive_path = Path(first["archive_path"])
    archive_path.write_bytes(b"test-only corrupt cache")
    raw_before = Path(first["raw_path"]).read_bytes()

    def offline(*args, **kwargs):
        raise AssertionError("Corrupt cache must be reported, not silently replaced")

    monkeypatch.setattr("urllib.request.urlopen", offline)
    with pytest.raises(MarketError, match="SHA-256 ZIP"):
        service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    assert archive_path.read_bytes() == b"test-only corrupt cache"
    assert Path(first["raw_path"]).read_bytes() == raw_before


def test_interrupted_http_has_actionable_error_and_publishes_nothing(tmp_path, monkeypatch):
    class InterruptedResponse(io.BytesIO):
        def read(self, *args):
            raise IncompleteRead(b"test-only interrupted HTTP body")

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: InterruptedResponse())
    with pytest.raises(MarketError, match="Không tải được jobs-2026"):
        MarketService(raw_dir=tmp_path / "raw").download_source(
            "jobs-2026", cache_dir=tmp_path / "cache"
        )
    assert list(tmp_path.iterdir()) == []


def test_cache_without_receipt_does_not_invent_a_download_date(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "jobs-2026-v1.zip").write_bytes(ARCHIVE.read_bytes())
    with pytest.raises(MarketError, match="Cache.*thiếu.*manifest"):
        MarketService(raw_dir=tmp_path / "raw").download_source("jobs-2026", cache_dir=cache_dir)
    assert not (cache_dir / "jobs-2026-v1.json").exists()
    assert not (tmp_path / "raw").exists()


def test_check_only_requires_a_complete_cache_and_never_fetches(tmp_path, monkeypatch):
    def offline(*args, **kwargs):
        raise AssertionError("Integrity check must never download")

    monkeypatch.setattr("urllib.request.urlopen", offline)
    with pytest.raises(MarketError, match="Chưa có cache"):
        MarketService(raw_dir=tmp_path / "raw").download_source(
            "jobs-2026", cache_dir=tmp_path / "cache", check_only=True
        )
    assert list(tmp_path.iterdir()) == []


def test_check_only_reports_missing_raw_without_extracting_it(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    service = MarketService(raw_dir=tmp_path / "raw")
    first = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    Path(first["raw_path"]).unlink()
    with pytest.raises(MarketError, match="Thiếu raw"):
        service.download_source("jobs-2026", cache_dir=tmp_path / "cache", check_only=True)
    assert not Path(first["raw_path"]).exists()


def test_cached_archive_restores_missing_raw_and_keeps_receipt_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: io.BytesIO(ARCHIVE.read_bytes()))
    service = MarketService(raw_dir=tmp_path / "raw")
    first = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    Path(first["raw_path"]).unlink()
    manifest_path = Path(first["manifest_path"])
    manifest_path.write_text(json.dumps(json.loads(manifest_path.read_text())))
    before = manifest_path.read_bytes()
    result = service.download_source("jobs-2026", cache_dir=tmp_path / "cache")
    assert result["status"] == "cached"
    assert service.preview("jobs-2026").row_count == 1550
    assert manifest_path.read_bytes() == before

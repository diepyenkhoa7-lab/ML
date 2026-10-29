"""Download approved immutable revisions; never replace existing source bytes."""

import hashlib
import io
import json
import os
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path

from .service import MarketError, Source


def download_source(
    source: Source, raw_dir: Path, cache_dir: Path, *, timeout: float, check_only: bool
) -> dict:
    url = source.dataset_url.replace("/datasets/", "/api/v1/datasets/download/", 1)
    url += f"?datasetVersionNumber={source.revision}"
    archive_path = cache_dir / f"{source.source_id}-v{source.revision}.zip"
    manifest_path = archive_path.with_suffix(".json")
    raw_path = raw_dir / source.filename
    try:
        if archive_path.exists() != manifest_path.exists():
            raise MarketError(
                f"Cache {source.source_id} thiếu ZIP hoặc manifest; giữ nguyên để kiểm tra."
            )
        receipt = None
        if manifest_path.exists():
            try:
                receipt = json.loads(manifest_path.read_text())
                expected_source = json.loads(json.dumps(asdict(source)))
                if receipt["source"] != expected_source or receipt["download_url"] != url:
                    raise ValueError("revision, URL hoặc xuất xứ khác catalog")
                timestamp = datetime.fromisoformat(receipt["downloaded_at"])
                if timestamp.tzinfo is None:
                    raise ValueError("thời gian tải thiếu múi giờ")
            except (ValueError, TypeError, KeyError) as error:
                raise MarketError(f"Manifest {source.source_id} không khớp: {error}") from error
        if (
            raw_path.exists()
            and hashlib.sha256(raw_path.read_bytes()).hexdigest() != source.raw_sha256
        ):
            raise MarketError(f"SHA-256 raw không khớp cho {source.source_id}; raw đã thay đổi.")
        cached = archive_path.exists()
        if check_only and not cached:
            raise MarketError(f"Chưa có cache cho {source.source_id}; hãy tải đúng revision trước.")
        if check_only and not raw_path.exists():
            raise MarketError(f"Thiếu raw {source.filename}; dùng lệnh tải để trích lại từ cache.")
        if cached:
            archive = archive_path.read_bytes()
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "career-market/0.1"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                archive = response.read()
        if hashlib.sha256(archive).hexdigest() != source.archive_sha256:
            raise MarketError(f"SHA-256 ZIP không khớp cho {source.source_id}; nguồn đã thay đổi.")
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            raw = zipped.read(source.filename)
        if hashlib.sha256(raw).hexdigest() != source.raw_sha256:
            raise MarketError(f"SHA-256 raw không khớp cho {source.source_id}; nguồn đã thay đổi.")
        downloaded_at = datetime.now(timezone.utc).isoformat()
        if receipt is None:
            receipt = {
                "source": asdict(source),
                "download_url": url,
                "downloaded_at": downloaded_at,
            }
        if not check_only:
            cache_dir.mkdir(parents=True, exist_ok=True)
            raw_dir.mkdir(parents=True, exist_ok=True)
            for target, content in (
                (raw_path, raw),
                (archive_path, archive),
                (manifest_path, json.dumps(receipt, ensure_ascii=False, indent=2).encode()),
            ):
                if target == manifest_path and cached:
                    continue
                if target.exists() and target.read_bytes() == content:
                    continue
                with tempfile.TemporaryDirectory(dir=target.parent, prefix=".download-") as staging:
                    staged = Path(staging) / target.name
                    staged.write_bytes(content)
                    os.link(staged, target)
    except (OSError, urllib.error.URLError, HTTPException, zipfile.BadZipFile, KeyError) as error:
        raise MarketError(f"Không tải được {source.source_id}: {error}") from error
    return {
        **receipt,
        "status": "cached" if cached else "downloaded",
        "archive_sha256": source.archive_sha256,
        "raw_sha256": source.raw_sha256,
        "raw_path": str(raw_path),
        "archive_path": str(archive_path),
        "manifest_path": str(manifest_path),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }

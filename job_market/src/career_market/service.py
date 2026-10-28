"""Read approved postings and expose shared, source-aware business methods."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

from .locations import location_report, normalize_locations


class MarketError(ValueError):
    """An input problem safe to show in CLI and dashboard."""


@dataclass(frozen=True)
class Source:
    source_id: str
    revision: int
    license: str
    filename: str
    publisher: str
    platform: str
    metadata_url: str
    dataset_url: str
    archive_sha256: str
    raw_sha256: str
    expected_rows: int
    columns: tuple[str, ...]
    id_column: str | None
    url_column: str
    has_job_description: bool
    salary_period_confirmed: bool
    attribution: str
    time_fields: dict[str, str]
    imported_on: str


@dataclass(frozen=True)
class RawRecord:
    source_id: str
    job_id: str | None
    job_url: str
    raw: dict[str, str]


@dataclass(frozen=True)
class RawPreview:
    source: Source
    row_count: int
    columns: tuple[str, ...]
    raw_sha256: str
    records: tuple[RawRecord, ...]


class MarketService:
    """Public application seam; adapters only render its results."""

    def __init__(self, raw_dir: Path | None = None):
        package_dir = Path(__file__).resolve().parent
        bundled_raw = package_dir / "datasets/raw"
        self.raw_dir = (
            raw_dir
            if raw_dir is not None
            else (bundled_raw if bundled_raw.is_dir() else package_dir.parents[1] / "datasets/raw")
        )

    # T05: location aliases; shared by CLI callers and the location page.
    def normalize_locations(self, raw: str | None) -> dict:
        """Normalize whole labels; see docs/tdd/T05.md for the dictionary contract."""
        return normalize_locations(raw)

    def location_report(
        self, source_id: str, *, location: str | None = None, status: str | None = None
    ) -> dict:
        """Raw–clean table, exact canonical/status filters, and matching CSV (T05)."""
        preview = self.preview(source_id, limit=None)
        return location_report(source_id, preview.records, location, status)

    def sources(self) -> tuple[Source, ...]:
        catalog = json.loads(Path(__file__).with_name("sources.json").read_text())
        return tuple(Source(**{**item, "columns": tuple(item["columns"])}) for item in catalog)

    def preview(self, source_id: str, limit: int | None = 5) -> RawPreview:
        """Verify the whole source; limit=None returns every unmodified record."""
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise MarketError("limit phải là số nguyên không âm hoặc None (tất cả).")
        source = next((source for source in self.sources() if source.source_id == source_id), None)
        if source is None:
            raise MarketError(f"Nguồn không được duyệt: {source_id}")
        try:
            raw = (self.raw_dir / source.filename).read_bytes()
        except OSError as error:
            raise MarketError(f"Không đọc được raw {source.filename}: {error.strerror}") from error
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
            if tuple(reader.fieldnames or ()) != source.columns:
                raise MarketError(f"Schema {source_id}: cần các cột {', '.join(source.columns)}")
            rows = list(reader)
        except (UnicodeError, csv.Error) as error:
            raise MarketError(f"CSV không hợp lệ cho {source_id}: {error}") from error
        if len(rows) != source.expected_rows:
            raise MarketError(f"Số dòng {source_id}: cần {source.expected_rows}, nhận {len(rows)}.")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != source.raw_sha256:
            raise MarketError(f"SHA-256 không khớp cho {source_id}; raw đã thay đổi.")
        return RawPreview(
            source,
            len(rows),
            tuple(reader.fieldnames),
            digest,
            tuple(
                RawRecord(source_id, row.get(source.id_column), row[source.url_column], row)
                for row in rows[:limit]
            ),
        )

    # Salary normalization (T09): only the explicit salary field supplies evidence.
    def normalize_salary(self, raw: str | None) -> dict:
        """Return source amounts, units, classification and optional VND/month target."""
        from .salary import normalize_salary

        return normalize_salary(raw)

    def salary_report(self, source_id: str | None = None) -> dict:
        """Normalize every verified raw row; counts describe rows, not unique IT jobs."""
        from collections import Counter

        source_ids = (
            [source.source_id for source in self.sources()] if source_id is None else [source_id]
        )
        rows = []
        for selected in source_ids:
            for number, record in enumerate(self.preview(selected, limit=None).records, start=1):
                raw = record.raw.get("salary", "")
                rows.append(
                    {
                        "source_id": record.source_id,
                        "source_row": number,
                        "job_id": record.job_id,
                        "job_url": record.job_url,
                        "raw_salary": raw,
                        **self.normalize_salary(raw),
                    }
                )
        return {
            "rows": rows,
            "row_count": len(rows),
            "target_n": sum(row["salary_target_vnd_month"] is not None for row in rows),
            "source_counts": dict(Counter(row["source_id"] for row in rows)),
            "reason_counts": dict(Counter(row["salary_reason"] for row in rows)),
            "status_counts": dict(Counter(row["salary_status"] for row in rows)),
        }

    def salary_exports(self, report: dict) -> dict[str, str]:
        """Return raw/normalized/status/review CSV strings from a salary_report result."""
        from .salary import salary_exports

        return salary_exports(report)

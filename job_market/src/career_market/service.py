"""Read approved raw postings without cleaning or deriving market measures."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path


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

    # T10: experience normalization; independent of other normalization methods.
    def normalize_experience(self, raw) -> dict:
        """Return year bounds, kind, status and reason; see T10 ticket notes."""
        from .experience import normalize_experience

        return normalize_experience(raw)

    def experience_report(
        self, source_id: str, status: str | None = None, kind: str | None = None
    ) -> dict:
        """Raw/clean rows and matching CSV from one approved source; T10 notes define keys."""
        preview = self.preview(source_id, limit=None)
        rows = []
        for record in preview.records:
            raw = record.raw.get("experience", record.raw.get("exp"))
            row = {
                "source_id": record.source_id,
                "job_id": record.job_id,
                "job_url": record.job_url,
                "experience_raw": raw,
                **self.normalize_experience(raw),
            }
            if status is not None and row["experience_status"] != status:
                continue
            if kind is not None and row["experience_kind"] != kind:
                continue
            rows.append(row)
        output = io.StringIO()
        columns = [
            "source_id",
            "job_id",
            "job_url",
            "experience_raw",
            "experience_min",
            "experience_max",
            "experience_kind",
            "experience_status",
            "experience_reason",
        ]
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return {
            "rows": rows,
            "total_count": preview.row_count,
            "filtered_count": len(rows),
            "csv": output.getvalue(),
        }

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

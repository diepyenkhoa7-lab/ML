"""Read approved raw postings without cleaning or deriving market measures."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

from career_market.roles import classify_role


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

    # T03: phân loại vai trò, dùng chung cho các adapter.
    def classify_role(self, title: str, description: str = "", requirements: str = "") -> dict:
        """Return role, role_status, role_evidence (field/text), and role_reason."""
        return classify_role(title, description, requirements)

    def __init__(self, raw_dir: Path | None = None):
        package_dir = Path(__file__).resolve().parent
        bundled_raw = package_dir / "datasets/raw"
        self.raw_dir = (
            raw_dir
            if raw_dir is not None
            else (bundled_raw if bundled_raw.is_dir() else package_dir.parents[1] / "datasets/raw")
        )

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

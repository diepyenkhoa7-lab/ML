"""Describe observed date coverage without assuming comparable sampling frames."""

from collections import Counter
from datetime import date

from .snapshots import csv_bytes


def time_coverage(rows, sources):
    coverage, periods = [], []
    for source_id in sorted({row["source_id"] for row in rows}):
        source_rows = [row for row in rows if row["source_id"] == source_id]
        unique = {
            row["posting_id"]: row
            for row in source_rows
            if row.get("posting_id") and row.get("partition") != "duplicates"
        }
        dated = []
        for row in unique.values():
            if row.get("date_kind") == "posting" and row.get("posting_date"):
                try:
                    dated.append((row, date.fromisoformat(row["posting_date"])))
                except ValueError:
                    pass
        dates = [day.isoformat() for _, day in dated]
        counts = Counter(day.isoformat()[:7] for _, day in dated)
        eda_counts = Counter(day.isoformat()[:7] for row, day in dated if row["partition"] == "eda")
        metadata = next((source for source in sources if source.source_id == source_id), None)
        coverage.append(
            {
                "source_id": source_id,
                "platform": metadata.platform if metadata else source_id,
                "raw_rows": len(source_rows),
                "unique_postings": len(unique),
                "eda_postings": sum(row["partition"] == "eda" for row in unique.values()),
                "date_from": min(dates) if dates else None,
                "date_to": max(dates) if dates else None,
                "years": sorted({day.year for _, day in dated}),
                "observed_months": sorted(counts),
                "missing_posting_dates": len(unique) - len(dated),
            }
        )
        for month, count in sorted(counts.items()):
            periods.append(
                {
                    "source_id": source_id,
                    "posting_month": month,
                    "unique_postings": count,
                    "eda_postings": eda_counts[month],
                }
            )
    reason = (
        "Chưa đủ cơ sở kết luận xu hướng nhiều năm: các nguồn là bản chụp khác nền tảng/phạm vi, "
        "chưa có thiết kế lấy mẫu và độ phủ các kỳ tương đương. Tháng không quan sát không đồng nghĩa nhu cầu bằng 0. "
        "Ngày tải, cập nhật và hạn nộp không được dùng thay ngày đăng."
    )
    return {
        "status": "insufficient_comparability",
        "reason": reason,
        "coverage": coverage,
        "periods": periods,
        "csv": csv_bytes(
            coverage,
            [
                "source_id",
                "platform",
                "raw_rows",
                "unique_postings",
                "eda_postings",
                "date_from",
                "date_to",
                "years",
                "observed_months",
                "missing_posting_dates",
            ],
        ),
        "periods_csv": csv_bytes(
            periods, ["source_id", "posting_month", "unique_postings", "eda_postings"]
        ),
    }

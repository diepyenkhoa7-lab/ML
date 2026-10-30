"""Observed demand: one vote per skill per distinct posting."""

import io
import json
from collections import Counter
from datetime import date
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .postings import select_locations
from .snapshots import csv_bytes


def skill_demand(rows, role=None, locations=None, work_mode=None, source_ids=None, limit=15):
    selected = [
        r
        for r in rows
        if (role is None or r["role"] == role)
        and (source_ids is None or r["source_id"] in source_ids)
    ]
    selected = select_locations(selected, locations, work_mode)
    count = len(selected)
    frequencies = Counter(skill for row in selected for skill in set(row["skills"]))
    table = [
        {
            "skill": skill,
            "posting_count": frequency,
            "share_percent": round(100 * frequency / count, 2),
            "sample_size": count,
        }
        for skill, frequency in sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))[
            :limit
        ]
    ]
    catalog = json.loads(Path(__file__).with_name("sources.json").read_text())
    sources = sorted(
        set(source_ids)
        if source_ids is not None
        else {r["source_id"] for r in rows} or {item["source_id"] for item in catalog}
    )
    dates = []
    source_dates = {source_id: [] for source_id in sources}
    for row in selected:
        if row.get("date_kind") == "posting" and row.get("posting_date"):
            try:
                observed = date.fromisoformat(row["posting_date"]).isoformat()
                dates.append(observed)
                source_dates[row["source_id"]].append(observed)
            except ValueError:
                pass
    metadata = {
        "sources": [
            {
                **next(
                    (item for item in catalog if item["source_id"] == source_id),
                    {"source_id": source_id, "revision": None},
                ),
                "observed_period": {
                    "date_kind": "posting",
                    "date_from": min(source_dates[source_id]) if source_dates[source_id] else None,
                    "date_to": max(source_dates[source_id]) if source_dates[source_id] else None,
                },
            }
            for source_id in sources
        ],
        "observed_period": {
            "date_kind": "posting",
            "date_from": min(dates) if dates else None,
            "date_to": max(dates) if dates else None,
        },
        "missing_posting_dates": count - len(dates),
        "filters": {
            "role": role,
            "locations": locations,
            "work_mode": work_mode,
            "source_ids": source_ids,
            "limit": limit,
        },
        "sample_size": count,
        "units": {
            "posting_count": "distinct postings mentioning skill",
            "share_percent": "percent of selected distinct postings",
        },
    }
    source_labels = ", ".join(
        f"{source['source_id']} (revision {source['revision'] if source['revision'] is not None else 'chưa rõ'}): "
        + (
            f"{source['observed_period']['date_from']} – {source['observed_period']['date_to']}"
            if source["observed_period"]["date_from"]
            else "chưa rõ ngày đăng"
        )
        for source in metadata["sources"]
    )
    period = f"{min(dates)} – {max(dates)}" if dates else "chưa rõ ngày đăng"
    scope = (
        f"Nguồn: {source_labels or 'không có tin'} | Kỳ quan sát (ngày đăng): {period}"
        f" | Thiếu ngày đăng: {count - len(dates)} | Nghề: {role or 'tất cả'}"
        f" | Địa điểm: {', '.join(locations or []) or 'tất cả'}"
        f" | Hình thức: {work_mode or 'tất cả'}"
        f" | Lọc nguồn: {', '.join(source_ids) if source_ids is not None else 'tất cả'}"
        f" | Top: {limit} | n={count} | Đơn vị: tin duy nhất; tỷ lệ % trên n"
    )
    footnote = fill(scope, 125)
    footnote_height = 0.18 * len(footnote.splitlines()) + 0.2
    fig, axis = plt.subplots(figsize=(11, max(3, len(table) * 0.35 + 2)))
    if table:
        sns.barplot(
            data=pd.DataFrame(table), x="posting_count", y="skill", color="#2563a6", ax=axis
        )
        axis.bar_label(axis.containers[0], padding=3)
        axis.set_xlim(0, max(row["posting_count"] for row in table) * 1.2)
    else:
        axis.text(
            0.5,
            0.5,
            "Không có bằng chứng kỹ năng trong bộ lọc",
            ha="center",
            transform=axis.transAxes,
        )
    axis.set(
        xlabel="Số tin duy nhất có nhắc kỹ năng",
        ylabel="",
        title=f"Nhu cầu kỹ năng quan sát được · n={count}",
    )
    fig.set_figheight(fig.get_figheight() + footnote_height)
    fig.text(0.01, 0.01, footnote, fontsize=8)
    fig.tight_layout(rect=(0, footnote_height / fig.get_figheight(), 1, 1))
    output = io.BytesIO()
    fig.savefig(output, format="png", dpi=160, metadata={"Description": scope})
    plt.close(fig)
    export_rows = [
        {**row, "record_type": "skill", "export_metadata": metadata} for row in table
    ] or [{"record_type": "metadata", "sample_size": count, "export_metadata": metadata}]
    return {
        "posting_count": count,
        "with_skill_count": sum(bool(r["skills"]) for r in selected),
        "table": table,
        "scope": scope,
        "png": output.getvalue(),
        "csv": csv_bytes(
            export_rows,
            [
                "skill",
                "posting_count",
                "share_percent",
                "sample_size",
                "record_type",
                "export_metadata",
            ],
        ),
    }

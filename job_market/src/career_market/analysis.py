"""Observed demand: one vote per skill per distinct posting."""

import io
from collections import Counter
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
    sources = sorted({r["source_id"] for r in selected})
    scope = f"Nguồn: {', '.join(sources) or 'không có tin'} | Nghề: {role or 'tất cả'} | Địa điểm: {', '.join(locations or []) or 'tất cả'} | Hình thức: {work_mode or 'tất cả'}"
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
    fig.text(0.01, 0.01, fill(scope, 125), fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    output = io.BytesIO()
    fig.savefig(output, format="png", dpi=160)
    plt.close(fig)
    return {
        "posting_count": count,
        "with_skill_count": sum(bool(r["skills"]) for r in selected),
        "table": table,
        "scope": scope,
        "png": output.getvalue(),
        "csv": csv_bytes(table, ["skill", "posting_count", "share_percent", "sample_size"]),
    }

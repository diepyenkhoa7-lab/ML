"""Conservative whole-label location aliases from the approved new sources."""

import csv
import io
import json
import re
from collections import Counter

ALIASES = {
    "hcm": "HCM",
    "tp.hcm": "HCM",
    "ho chi minh": "HCM",
    "hồ chí minh": "HCM",
    "hn": "HN",
    "ha noi": "HN",
    "hà nội": "HN",
}

# Exact province labels observed in the checked location fields, not JD/address text.
# jobs-2023 v2 and jobs-2026 v1; spelling and boundary suffixes remain source-specific.
SOURCE_PROVINCES = frozenset(
    """An Giang
Bà Rịa - Vũng Tàu
Bình Dương
Bình Phước
Bình Thuận
Bình Định
Bạc Liêu
Bắc Giang
Bắc Ninh
Bến Tre
Cà Mau
Cần Thơ
Dak Lak
Dak Nông
Gia Lai
Hà Giang
Hà Nam
Hà Tĩnh
Hòa Bình
Hưng Yên
Hải Dương
Hải Phòng
Hậu Giang
Khánh Hòa
Kiên Giang
Long An
Lào Cai
Lâm Đồng
Nam Định
Nghệ An
Ninh Bình
Ninh Thuận
Phú Thọ
Phú Yên
Quảng Bình
Quảng Nam
Quảng Ngãi
Quảng Ninh
Quảng Trị
Sóc Trăng
Sơn La
Thanh Hóa
Thái Bình
Thái Nguyên
Thừa Thiên- Huế
Tiền Giang
Trà Vinh
Tuyên Quang
Tây Ninh
Vĩnh Long
Vĩnh Phúc
Yên Bái
Điện Biên
Đà Nẵng
Đồng Nai
Đồng Tháp
An Giang (mới)
Bắc Ninh (mới)
Cà Mau (mới)
Cần Thơ (mới)
Gia Lai (mới)
Huế
Hưng Yên (mới)
Hải Phòng (mới)
Khánh Hòa (mới)
Lâm Đồng (mới)
Ninh Bình (mới)
Phú Thọ (mới)
Quảng Trị (mới)
Thái Nguyên (mới)
Tây Ninh (mới)
Vĩnh Long (mới)
Đà Nẵng (mới)
Đồng Nai (mới)""".splitlines()
)

SCOPE_NOTE = (
    "Giữ hậu tố (mới) trong bằng chứng nguồn; nhãn chuẩn không xác nhận "
    "cùng phạm vi địa giới qua năm."
)


def normalize_locations(raw: str | None) -> dict:
    if raw is None or not raw.strip():
        return {
            "locations": [],
            "location_status": "missing",
            "location_aliases": {},
            "location_unresolved": [],
            "work_modes": [],
            "location_reason": "Thiếu địa điểm trong nguồn.",
        }
    locations = []
    aliases = {}
    unresolved = []
    new_scope = False
    for part in re.split(r"[|&]", raw):
        token = part.strip()
        if not token:
            continue
        label = token.casefold()
        new_scope = new_scope or label.endswith(" (mới)")
        canonical = (
            token if token in SOURCE_PROVINCES else ALIASES.get(label.removesuffix(" (mới)"))
        )
        if canonical:
            aliases[token] = canonical
            if canonical not in locations:
                locations.append(canonical)
        else:
            unresolved.append(token)
    if not locations and not unresolved:
        unresolved.append(raw)
    return {
        "locations": locations,
        "location_status": "review" if unresolved else "normalized",
        "location_aliases": aliases,
        "location_unresolved": unresolved,
        "work_modes": [],
        "location_reason": (
            "Khớp toàn bộ nhãn địa điểm đã xác minh."
            if not unresolved
            else "Chưa đủ chứng cứ để chuẩn hóa địa điểm; cần review chuỗi gốc."
        )
        + (" " + SCOPE_NOTE if new_scope else ""),
    }


def location_report(source_id, records, location=None, status=None) -> dict:
    """CSV-ready raw–clean rows and raw-label frequencies; never unique-job counts."""
    rows = []
    options = set()
    alias_table = []
    counts = Counter(record.raw["location"] for record in records)
    for raw, count in counts.items():
        result = normalize_locations(raw)
        options.update(result["locations"])
        if location is not None and location not in result["locations"]:
            continue
        if status is not None and status != result["location_status"]:
            continue
        flat = {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
            for key, value in result.items()
        }
        alias_table.append({"location_raw": raw, **flat, "raw_rows": count})
    by_raw = {row["location_raw"]: row for row in alias_table}
    for record in records:
        alias = by_raw.get(record.raw["location"])
        if alias is not None:
            rows.append(
                {
                    "source_id": source_id,
                    "job_id": record.job_id or "",
                    "job_url": record.job_url,
                    **{key: value for key, value in alias.items() if key != "raw_rows"},
                }
            )
    fields = [
        "source_id",
        "job_id",
        "job_url",
        "location_raw",
        "locations",
        "location_status",
        "location_aliases",
        "location_unresolved",
        "work_modes",
        "location_reason",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return {
        "source_id": source_id,
        "raw_row_count": len(records),
        "location_options": sorted(options),
        "alias_table": alias_table,
        "rows": rows,
        "csv": output.getvalue(),
    }

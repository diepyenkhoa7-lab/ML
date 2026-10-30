"""Conservative whole-label location aliases from the approved new sources."""

import csv
import io
import json
import re

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
    work_modes = []
    for part in re.split(r"[|&/]", raw):
        token = part.strip()
        if not token:
            continue
        label = token.casefold()
        if label in {"remote", "làm việc từ xa", "lam viec tu xa"}:
            if "Remote" not in work_modes:
                work_modes.append("Remote")
            continue
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
    if not locations and not unresolved and not work_modes:
        unresolved.append(raw)
    return {
        "locations": locations,
        "location_status": "review" if unresolved else "normalized",
        "location_aliases": aliases,
        "location_unresolved": unresolved,
        "work_modes": work_modes,
        "location_reason": (
            "Khớp toàn bộ nhãn địa điểm đã xác minh."
            if not unresolved
            else "Chưa đủ chứng cứ để chuẩn hóa địa điểm; cần review chuỗi gốc."
        )
        + (" " + SCOPE_NOTE if new_scope else ""),
    }


def location_report(
    source_id, canonical_rows, location=None, status=None, locations=None, work_mode=None
) -> dict:
    """Use the same canonical work-mode evidence as preparation and demand."""
    rows = []
    options = set()
    aliases_by_raw = {}
    for row in canonical_rows:
        options.update(row["locations"])
        requested = list(locations or []) + ([location] if location else [])
        if requested and not set(requested).intersection(row["locations"]):
            continue
        if work_mode and work_mode not in row["work_modes"]:
            continue
        if status is not None and status != row["location_status"]:
            continue
        result = {
            key: row[key]
            for key in (
                "location_raw",
                "locations",
                "location_status",
                "location_aliases",
                "location_unresolved",
                "work_modes",
                "location_reason",
            )
        }
        flat = {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
            for key, value in result.items()
        }
        alias = aliases_by_raw.setdefault(row["location_raw"], {**flat, "raw_rows": 0})
        alias["raw_rows"] += 1
        alias["work_modes"] = json.dumps(
            sorted(set(json.loads(alias["work_modes"])) | set(row["work_modes"])),
            ensure_ascii=False,
        )
        rows.append(
            {
                "source_id": source_id,
                "job_id": row["job_id"] or "",
                "job_url": row["job_url"],
                "posting_id": row["posting_id"],
                **flat,
            }
        )
    alias_table = list(aliases_by_raw.values())
    fields = [
        "source_id",
        "job_id",
        "job_url",
        "posting_id",
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
        "raw_row_count": len(canonical_rows),
        "location_options": sorted(options),
        "alias_table": alias_table,
        "rows": rows,
        "unique_posting_count": len({row["posting_id"] for row in rows if row["posting_id"]}),
        "csv": output.getvalue(),
    }

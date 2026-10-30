"""Strict normalization of the salary field, without inferred units or conversion."""

import re
import unicodedata
from decimal import Decimal

SCALES = {
    "trieu": 1_000_000,
    "tr": 1_000_000,
    "million": 1_000_000,
    "m": 1_000_000,
    "k": 1_000,
    "nghin": 1_000,
    "ngan": 1_000,
}
AMOUNT = r"([0-9][0-9.,]*)\s*(trieu|tr|million|m|k|nghin|ngan)?"


def _number(value: str) -> Decimal:
    # A separator followed by three digits is grouping, never a guessed decimal.
    if re.fullmatch(r"\d+", value):
        return Decimal(value)
    for group, decimal in [(".", ","), (",", ".")]:
        if re.fullmatch(
            r"\d{1,3}(?:" + re.escape(group) + r"\d{3})+(?:" + re.escape(decimal) + r"\d{1,2})?",
            value,
        ):
            return Decimal(value.replace(group, "").replace(decimal, "."))
    if re.fullmatch(r"\d+[.,]\d{1,2}", value):
        return Decimal(value.replace(",", "."))
    raise ValueError("invalid_amount")


def _amount(value: str, scale: str | None, shared_scale: str | None, peer: str | None) -> Decimal:
    # A shared suffix applies to two large endpoints too (1.000–2.000 nghìn).
    # A full amount paired with a short scaled endpoint is already expanded
    # (20 triệu–30.000.000); grouping separators alone do not decide the scale.
    if not scale and (_number(value) < 1000 or (peer is not None and _number(peer) >= 1000)):
        scale = shared_scale
    return _number(value) * SCALES.get(scale, 1)


def normalize_salary(raw: str | None) -> dict:
    """Keep amounts in source units; only explicit VND/month gets a target."""
    result = dict.fromkeys(
        (
            "salary_lower",
            "salary_upper",
            "salary_midpoint",
            "salary_currency",
            "salary_period",
            "salary_target_vnd_month",
        )
    )
    result.update(
        salary_basis="unknown",
        salary_kind="unknown",
        salary_status="review",
        salary_reason="invalid_amount",
    )
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        result["salary_reason"] = "missing_salary"
        return result
    if not isinstance(raw, str):
        return result
    text = unicodedata.normalize("NFD", raw or "").casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("đ", "d").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^luong\s*:\s*", "", text)
    for phrase, kind in [("thoa thuan", "negotiable"), ("canh tranh", "competitive")]:
        if text == phrase:
            result.update(salary_kind=kind, salary_reason=kind, salary_status="excluded")
            return result
    bound = None
    prefix = re.match(r"^(up\s*to|toi|den|duoi|tren|tu)(?=\s|\d)\s*", text)
    if prefix:
        bound = "lower_bound" if prefix[1] in ("tren", "tu") else "upper_bound"
        text = text[prefix.end() :]
    for currency, pattern in [
        ("VND", r"\b(?:vnd|vndong|dong|d)\b|(?<=\d)d\b|₫"),
        ("USD", r"\busd\b|\$"),
        ("EUR", r"\beur\b|€"),
    ]:
        if re.search(pattern, text):
            if result["salary_currency"] is not None:
                result.update(salary_currency=None, salary_reason="conflicting_currency")
                return result
            result["salary_currency"] = currency
            text = re.sub(pattern, " ", text)
    for period, words in [
        ("MONTH", "thang|month"),
        ("YEAR", "nam|year"),
        ("HOUR", "gio|hour"),
        ("DAY", "ngay|day"),
    ]:
        pattern = rf"(?:/|per\b|moi\b|hang\b)\s*(?:{words})\b"
        if re.search(pattern, text):
            if result["salary_period"] is not None:
                result.update(salary_period=None, salary_reason="conflicting_period")
                return result
            result["salary_period"] = period
            text = re.sub(pattern, " ", text)
    text = re.sub(r"\(\s*(gross|net)\s*\)", r" \1 ", text)
    for basis in ("gross", "net"):
        if re.search(rf"\b{basis}\b", text):
            if result["salary_basis"] != "unknown":
                result.update(salary_basis="unknown", salary_reason="conflicting_basis")
                return result
            result["salary_basis"] = basis
            text = re.sub(rf"\b{basis}\b", " ", text)
    if re.search(r"^\s*-\s*\d|[-]\s*-\s*\d", text):
        result["salary_reason"] = "negative_amount"
        return result
    match = re.fullmatch(AMOUNT + r"(?:\s*(?:-|den|to)\s*" + AMOUNT + r")?", text.strip())
    if not match:
        return result
    first, scale1, second, scale2 = match.groups()
    try:
        lower = _amount(first, scale1, scale2, second)
        upper = _amount(second, scale2, scale1, first) if second else lower
    except ValueError:
        return result
    if lower <= 0 or upper <= 0 or max(lower, upper) > 1_000_000_000_000_000:
        return result
    if lower > upper:
        result.update(
            salary_lower=float(lower),
            salary_upper=float(upper),
            salary_kind="bounded",
            salary_reason="inverted_range",
        )
        return result
    midpoint = (lower + upper) / 2
    result.update(
        salary_lower=float(lower),
        salary_upper=float(upper),
        salary_midpoint=float(midpoint),
        salary_kind="bounded" if second else "fixed",
    )
    if bound == "lower_bound" and prefix[1] == "tu" and second:
        bound = None
    if bound:
        if second:
            result["salary_midpoint"] = None
            return result
        result.update(salary_kind=bound, salary_midpoint=None, salary_reason="single_bound")
        result["salary_lower" if bound == "upper_bound" else "salary_upper"] = None
        return result
    missing = [name for name in ("currency", "period") if result[f"salary_{name}"] is None]
    if missing:
        result["salary_reason"] = "missing_" + "_and_".join(missing)
        result["salary_midpoint"] = None
    else:
        result.update(salary_status="parsed", salary_reason="non_vnd_month")
    if result["salary_currency"] == "VND" and result["salary_period"] == "MONTH":
        result.update(
            salary_status="valid",
            salary_reason="eligible_vnd_month",
            salary_target_vnd_month=float(midpoint),
        )
    return result


def salary_exports(report: dict) -> dict[str, str]:
    """CSV text for every raw row, normalized row, reason count and non-target row."""
    import csv
    import io
    from collections import Counter

    identity = ["source_id", "source_row", "job_id", "job_url", "raw_salary"]
    normalized = identity + list(normalize_salary(None))
    counts = Counter(
        (row["source_id"], row["salary_status"], row["salary_reason"]) for row in report["rows"]
    )
    statuses = [
        {
            "source_id": source,
            "salary_status": status,
            "salary_reason": reason,
            "n": count,
            "target_n": count if status == "valid" else 0,
        }
        for (source, status, reason), count in sorted(counts.items())
    ]
    tables = {
        "raw.csv": (identity, report["rows"]),
        "normalized.csv": (normalized, report["rows"]),
        "status.csv": (["source_id", "salary_status", "salary_reason", "n", "target_n"], statuses),
        "review.csv": (
            normalized,
            [row for row in report["rows"] if row["salary_target_vnd_month"] is None],
        ),
    }
    exports = {}
    for name, (columns, rows) in tables.items():
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        exports[name] = buffer.getvalue()
    return exports

"""Normalize evidenced experience bounds in years without inventing a midpoint."""

import math
import re

NUMBER = r"-?\d+(?:[.,]\d+)?"


def _result(low=None, high=None, kind="missing", status="missing", reason="missing_experience"):
    if status == "ok":
        values = [value for value in (low, high) if value is not None]
        if any(value < 0 for value in values):
            reason = "negative_experience"
        elif any(value > 60 for value in values):
            reason = "experience_over_60_years"
        elif low is not None and high is not None and low > high:
            reason = "inverted_experience_range"
        if reason:
            low, high, status = None, None, "review"
    return {
        "experience_min": low,
        "experience_max": high,
        "experience_kind": kind,
        "experience_status": status,
        "experience_reason": reason,
    }


def normalize_experience(raw):
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _result()
    text = str(raw).casefold().strip()
    if text in {"", "n/a", "null", "none", "nan", "na"}:
        return _result()
    if text in {
        "không yêu cầu kinh nghiệm",
        "chưa có kinh nghiệm",
        "không yêu cầu",
        "không có kinh nghiệm",
    }:
        return _result(0.0, 0.0, "no_experience", "ok", None)
    divisor = 12 if text.endswith("tháng") else 1
    match = re.fullmatch(
        rf"(?:từ\s+)?({NUMBER})\s*(năm|tháng)?\s*(?:-|–|—|đến)\s*"
        rf"({NUMBER})\s*(năm|tháng)?",
        text,
    )
    if match:
        low_unit, high_unit = match[2] or match[4], match[4] or match[2]
        low = float(match[1].replace(",", ".")) / (12 if low_unit == "tháng" else 1)
        high = float(match[3].replace(",", ".")) / (12 if high_unit == "tháng" else 1)
        return _result(low, high, "range", "ok", None)
    match = re.fullmatch(r"(-?\d+(?:[.,]\d+)?)\s*(?:năm|tháng)?", text)
    if match:
        years = float(match[1].replace(",", ".")) / divisor
        return _result(years, years, "exact", "ok", None)
    match = re.fullmatch(r"(trên|dưới|từ|tối đa)\s+(-?\d+(?:[.,]\d+)?)\s*(?:năm|tháng)", text)
    if match:
        years = float(match[2].replace(",", ".")) / divisor
        kind = {"trên": "greater_than", "dưới": "less_than", "từ": "at_least", "tối đa": "at_most"}[
            match[1]
        ]
        if kind in {"greater_than", "at_least"}:
            return _result(years, None, kind, "ok", None)
        return _result(None, years, kind, "ok", None)
    match = re.fullmatch(r"(-?\d+(?:[.,]\d+)?)\+\s*(?:năm|tháng)", text)
    if match:
        return _result(float(match[1].replace(",", ".")) / divisor, None, "at_least", "ok", None)
    return _result(kind="unknown", status="review", reason="unrecognized_experience")

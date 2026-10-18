"""Conservative direct monthly-range labels; never certify header buckets by proximity."""

import re

from scripts.data_cleaning import fold, level, parse_salary

NUM = r"\d+(?:[.,]\d+)*"
UNIT = r"(?:trieu(?:\s+dong)?|million|tr\b|m\b|vnd|vnđ|dong|đ|₫)"
RANGE = re.compile(
    rf"(?<![\w.,]){NUM}\s*(?:{UNIT})?\s*(?:-|–|—|~|den|to)\s*"
    rf"{NUM}\s*{UNIT}(?:\s*(?:vnd|dong|gross|net))?",
    re.I,
)
MONTH_AFTER = re.compile(r"^\s*(?:\(\s*)?(?:/\s*|moi\s+|per\s+)(?:thang|month)\b")
MONTH_BEFORE = re.compile(r"(?:luong\s+thang|monthly\s+(?:salary|income))\s*[:=]?\s*$")
ANCHOR = re.compile(r"luong|thu nhap|salary|income|compensation")
CENSOR = re.compile(r"up\s*to|upto|toi da|len toi|\btren\b|\bhon\b|\btoi\b|\bover\b")
FOREIGN = re.compile(r"usd|eur|sgd|jpy|\$")
EXCLUDED_TITLE = re.compile(
    r"\b(?:plc|cnc|scada|cam|teacher|trainer|sales)\b|giao vien|giang vien|kinh doanh"
)


def parse_range(span):
    # M denotes millions only inside an anchored salary clause, never in arbitrary prose.
    normalized = re.sub(r"(?<=\d)\s*m\b", " trieu", span)
    normalized = normalized.replace("vnđ", "VND").replace("đ", " VND ")
    normalized = re.sub(r"\b(?:den|to)\b", "-", normalized)
    parsed = parse_salary(normalized + "/thang")
    low, high = parsed["salary_min"], parsed["salary_max"]
    if (
        parsed["currency"] != "VND"
        or not low
        or not high
        or high <= low
        or high / low > 3
        or not 2e6 <= (low + high) / 2 <= 200e6
    ):
        return None
    return low, high


def direct_label(raw):
    """Return evidence and bounds, or quarantine; no missing-period training labels."""
    title = fold(raw["job_title"])
    if EXCLUDED_TITLE.search(title) or CENSOR.search(title):
        return None, "censored_or_non_developer_title"
    candidates = []
    for field in ["salary", "benefits", "job_description"]:
        content = fold(raw.get(field))
        for match in RANGE.finditer(content):
            before = content[max(0, match.start() - 65) : match.start()]
            after = content[match.end() : match.end() + 35]
            if field != "salary" and not ANCHOR.search(before):
                continue
            if not MONTH_AFTER.search(after) and not MONTH_BEFORE.search(before):
                continue
            local = before + match.group() + after[:12]
            if CENSOR.search(before[-25:]) or FOREIGN.search(local) or re.search(r"\bnet\b", local):
                continue
            bounds = parse_range(match.group())
            if bounds:
                candidates.append(
                    dict(
                        low=bounds[0],
                        high=bounds[1],
                        field=field,
                        evidence=content[max(0, match.start() - 35) : match.end() + 20],
                    )
                )
    if not candidates:
        return None, "no_direct_bounded_monthly_vnd_range"
    bounds = {(c["low"], c["high"]) for c in candidates}
    if len(bounds) != 1:
        return None, "conflicting_direct_monthly_ranges"
    chosen = candidates[0]
    chosen["salary_monthly_vnd"] = (chosen["low"] + chosen["high"]) / 2
    chosen["label_quality"] = "direct_month_range_silver"
    header = parse_salary(raw.get("salary"))
    chosen["header_differs"] = (
        header.get("salary_min") != chosen["low"] or header.get("salary_max") != chosen["high"]
    )
    return chosen, None


def title_level(position, title):
    content = fold(title)
    explicit = [
        name
        for name, pattern in [
            ("Intern", r"\bintern\b|thuc tap"),
            ("Fresher", r"\bfresher\b"),
            ("Junior", r"\bjunior\b"),
            ("Middle", r"\bmiddle\b|\bmid\b"),
            ("Senior", r"\bsenior\b"),
            ("Lead", r"\blead\b|truong nhom"),
        ]
        if re.search(pattern, content)
    ]
    return (
        explicit[0]
        if len(explicit) == 1
        else "Unknown"
        if explicit
        else level(position, title) or "Unknown"
    )

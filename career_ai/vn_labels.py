"""Source-grounded month evidence; migrated pure parsing from previous version."""

import re

from .source_parsing import fold, parse_salary

NUMBER = r"\d+(?:[.,]\d+)*"
SCALE = r"(?:trieu|tr\b|million|vnd|dong|usd|₫|d\b)"
MONEY = rf"{NUMBER}\s*(?:{SCALE})?"
MONTH_CLAUSE = re.compile(
    rf"{MONEY}(?:\s*[-–—~]\s*{MONEY})?\s*(?:{SCALE})?\s*"
    r"(?:/\s*(?:thang|month)|moi\s+thang|per\s+month)",
    re.IGNORECASE,
)
CENSORED = re.compile(r"(?:up\s*to|upto|toi da|len toi|tren|hon)\s*\d")


def salary_label(raw):
    title = fold(raw["job_title"])
    if CENSORED.search(title) or re.search(r"\b(?:plc|cnc|scada|cam)\b", title):
        return None, "censored_or_industrial"
    if re.search(r"\b(?:nam|year|annual|gio|hour|ngay|day|tuan|week)\b", fold(raw["salary"])):
        return None, "non_month_or_ambiguous_period"
    salary = parse_salary(raw["salary"])
    low, high = salary.get("salary_min"), salary.get("salary_max")
    if salary.get("currency") != "VND" or not low or not high or high < low:
        return None, "nonvnd_missing_or_censored_amount"
    if high / low > 3 or not 2e6 <= (low + high) / 2 <= 200e6:
        return None, "out_of_scope_range"
    if salary.get("salary_period") == "month":
        return (salary["salary_monthly_vnd"], "explicit_month", raw["salary"]), None
    if salary.get("salary_period") is not None:
        return None, "non_month_period"
    censored_evidence = False
    for field in ["benefits", "job_description", "requirements"]:
        content = fold(raw.get(field))
        for match in MONTH_CLAUSE.finditer(content):
            if low == high and CENSORED.search(content[max(0, match.start() - 16) : match.end()]):
                censored_evidence = True
                continue
            span = re.sub(r"(?<=\d)\s*d\b", " VND", match.group())
            parsed = parse_salary(span)
            if parsed.get("salary_monthly_vnd") and all(
                abs(parsed[k] - salary[k]) <= max(1, salary[k] * 0.01)
                for k in ["salary_min", "salary_max"]
            ):
                return (
                    parsed["salary_monthly_vnd"],
                    "explicit_month",
                    field + ": " + match.group(),
                ), None
    if censored_evidence:
        return None, "censored_body_evidence"
    # No annual/hourly evidence is converted to monthly. Missing period is a marked weak label.
    return (
        (low + high) / 2,
        "assumed_month_train_only",
        "period missing; monthly assumption",
    ), None

"""Pure salary/experience/role normalization migrated from the previous source."""

import math
import re
import unicodedata
from functools import lru_cache

import pandas as pd


def text(value):
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def fold(value):
    value = unicodedata.normalize("NFKD", text(value)).casefold().replace("đ", "d")
    return "".join(c for c in value if not unicodedata.combining(c))


def numeric(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def number(token):
    token = token.replace(" ", "")
    if "," in token and "." in token:
        decimal = "," if token.rfind(",") > token.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        token = token.replace(thousands, "").replace(decimal, ".")
    elif "," in token or "." in token:
        separator = "," if "," in token else "."
        pieces = token.split(separator)
        if len(pieces) > 2 or len(pieces[-1]) == 3:
            token = "".join(pieces)
        else:
            token = token.replace(separator, ".")
    return float(token)


def salary_result(
    low=None, high=None, currency=None, period=None, status="missing", basis="unknown"
):
    monthly = None
    if status == "valid" and low is not None and high is not None:
        if period == "month":
            monthly = (low + high) / 2
        elif period == "year":
            monthly = (low + high) / 24
    return {
        "salary_min": low,
        "salary_max": high,
        "currency": currency,
        "salary_period": period,
        "salary_basis": basis,
        "status": status,
        "salary_monthly_native": monthly,
        "salary_monthly_vnd": monthly if currency == "VND" else None,
    }


def native_salary(low, high, currency, period, basis="unknown"):
    low, high = numeric(low), numeric(high)
    currency = text(currency).upper() or None
    period = {"annual": "year", "monthly": "month", "hourly": "hour"}.get(
        fold(period), fold(period)
    ) or None
    if low is None and high is None:
        status = "missing"
    elif (low is not None and low < 0) or (high is not None and high < 0):
        status = "invalid_amount"
    elif low == high == 0:
        status = "not_disclosed"
        low = high = None
    elif low is None or high is None:
        status = "upper_bound" if low is None else "lower_bound"
    elif low <= 0 or high <= 0 or high < low:
        status = "invalid_range"
    elif not currency or not re.fullmatch(r"[A-Z]{3}", currency):
        status = "currency_unknown"
    elif period not in {"month", "year", "hour", "day", "week"}:
        status = "period_unknown"
    else:
        status = "valid"
    return salary_result(low, high, currency, period, status, basis)


def parse_salary(value, default_period=None):
    raw = fold(value).replace("–", "-").replace("—", "-").replace("−", "-")
    if not raw or raw in {"nan", "none", "null", "khong hien thi"}:
        return salary_result()
    if re.search(r"thoa thuan|thuong luong|negotiable|competitive", raw):
        return salary_result(status="negotiable")
    if raw.startswith("-") or "--" in raw:
        return salary_result(status="invalid_amount")
    currencies = set(re.findall(r"\b(?:usd|vnd|eur|gbp|cad|aud|sgd|jpy)\b", raw))
    vnd_scale = bool(re.search(r"trieu|\btr\b|(?<=\d)tr\b|\bty\b|₫|\bdong\b", raw))
    if vnd_scale:
        currencies.add("vnd")
    ambiguous = len(currencies) > 1 or ("$" in raw and currencies != {"usd"})
    currency = next(iter(currencies)).upper() if len(currencies) == 1 else None
    periods = {
        period
        for period, pattern in {
            "month": r"\bthang\b|\bmonth(?:ly)?\b|/mo\b",
            "year": r"\bnam\b|\byear(?:ly)?\b|\bannual\b|\bannum\b",
            "hour": r"\bgio\b|\bhour(?:ly)?\b|/hr\b",
            "day": r"\bngay\b|\bday\b",
            "week": r"\btuan\b|\bweek\b",
        }.items()
        if re.search(pattern, raw)
    }
    period = next(iter(periods)) if len(periods) == 1 else default_period if not periods else None
    basis = (
        "gross"
        if re.search(r"gross|truoc thue", raw)
        else ("net" if re.search(r"\bnet\b|sau thue", raw) else "unknown")
    )
    matches = list(
        re.finditer(
            r"(\d+(?:[.,]\d+)*)(?:\s*(trieu|million|billion|nghin|ngan|tr\b|k\b|ty\b))?",
            raw,
        )
    )
    if not matches or len(matches) > 2:
        return salary_result(currency=currency, period=period, status="unparsed", basis=basis)
    scales = {
        "trieu": 1e6,
        "tr": 1e6,
        "million": 1e6,
        "billion": 1e9,
        "ty": 1e9,
        "k": 1e3,
        "nghin": 1e3,
        "ngan": 1e3,
    }
    present_scales = {scales[m.group(2)] for m in matches if m.group(2)}
    amounts = [
        number(m.group(1))
        * (
            scales[m.group(2)]
            if m.group(2)
            else next(iter(present_scales))
            if len(present_scales) == 1
            else 1
        )
        for m in matches
    ]
    low, high = (amounts[0], amounts[1]) if len(amounts) == 2 else (amounts[0], amounts[0])
    if len(amounts) == 1 and re.search(r"^(?:tu\b|tren\b|from\b|over\b|>=)", raw):
        high = None
    elif len(amounts) == 1 and re.search(r"^(?:toi\b|den\b|duoi\b|up to\b|under\b|<=)", raw):
        low = None
    result = native_salary(low, high, currency, period, basis)
    if ambiguous:
        result.update(
            status="ambiguous_currency",
            salary_monthly_native=None,
            salary_monthly_vnd=None,
        )
    return result


def parse_experience(value, maximum=80):
    raw = fold(value).replace("–", "-").replace("—", "-")
    result = {
        "experience_years": None,
        "experience_min": None,
        "experience_max": None,
        "experience_kind": "missing",
    }
    if not raw:
        return result
    if re.search(r"khong (?:yeu cau|can kinh nghiem)|no experience required", raw):
        result.update(
            experience_years=0.0,
            experience_min=0.0,
            experience_max=0.0,
            experience_kind="explicit_zero",
        )
        return result
    numbers = re.findall(r"\d+(?:[.,]\d+)?", raw)
    if not numbers:
        return result
    values = [number(n) / (12 if "thang" in raw or "month" in raw else 1) for n in numbers]
    if raw.startswith("-") or len(values) > 2 or any(v > maximum or v < 0 for v in values):
        result["experience_kind"] = "invalid"
        return result
    low, high = values[0], values[-1]
    if high < low:
        result["experience_kind"] = "invalid"
    elif re.search(r"duoi|under|less than|<", raw):
        result.update(experience_max=high, experience_kind="upper_bound")
    elif re.search(r"tren|hon|over|more than|\+|>", raw):
        result.update(experience_min=low, experience_years=low, experience_kind="lower_bound")
    else:
        result.update(
            experience_min=low,
            experience_max=high,
            experience_years=low,
            experience_kind="range_lower_bound" if len(values) == 2 else "stated_years",
        )
    return result


ROLE_RULES = [
    (role, re.compile(pattern))
    for role, pattern in [
        ("Full-stack Developer", r"full[ -]?stack"),
        (
            "ML Engineer",
            r"machine learning|\bai[ /-]?ml\b|\b(?:ai|ml) engineer|ky su ai\b",
        ),
        ("Data Scientist", r"data scien|khoa hoc du lieu|applied scientist"),
        (
            "Data Engineer",
            r"data engineer|ky su du lieu|data warehouse|big data|\betl\b",
        ),
        ("Data Analyst", r"data (?:or business )?analyst|phan tich du lieu"),
        ("DevOps Engineer", r"devops|\bsre\b|site reliability"),
        (
            "QA Engineer",
            r"\bqa\b|\bqc\b|tester|test engineer|kiem thu|quality assurance",
        ),
        (
            "Security Engineer",
            r"cybersecurity|infosec|security (?:engineer|analyst)|an ninh|bao mat",
        ),
        (
            "Cloud Engineer",
            r"cloud (?:infrastructure|engineer|architect)|dien toan dam may",
        ),
        (
            "Software Architect",
            r"architect.*(?:software|solution)|kien truc.*phan mem|solution architect",
        ),
        (
            "Engineering Manager",
            r"engineering manager|tech(?:nical)? lead|cto\b|truong.*(?:it|cntt)\b",
        ),
        (
            "Mobile Developer",
            r"mobile.*(?:developer|engineer)|developer.*mobile|android|\bios\b|"
            r"flutter|react native|ung dung di dong",
        ),
        ("Frontend Developer", r"front[ -]?end|\breact\b|\bangular\b|\bvue(?:js)?\b"),
        ("Backend Developer", r"back[ -]?end"),
        ("Embedded Engineer", r"embedded|firmware|nhung"),
        (
            "Database Administrator",
            r"\bdba\b|database administrator|database.*engineer|quan tri.*co so du lieu",
        ),
        (
            "System Administrator",
            r"system administrator|sysadmin|quan tri.*(?:he thong|mang)|ha tang it|"
            r"ky su he thong|infrastructure engineer",
        ),
        (
            "Software Developer",
            r"\bdeveloper\b|programmer|software engineer|software development|lap trinh|"
            r"phat trien phan mem|ky su phan mem|ky su (?:java|python|c#)|\brpa\b|"
            r"nha phat trien.*(?:\.net|blockchain|web|ung dung)",
        ),
        (
            "IT Support",
            r"it support|help[ -]?desk|support engineer|nhan vien it|it staff|ky thuat.*cntt",
        ),
        ("Business Analyst", r"business analyst|phan tich nghiep vu"),
        ("UX/UI Designer", r"\bux\b|\bui\b|giao dien.*nguoi dung"),
    ]
]

NON_IT = re.compile(
    r"\bsales\b|business develop|recruiter|talent acquisition|"
    r"(?:nhan vien|chuyen vien|truong phong) tuyen dung|kinh doanh|ban hang|ke toan|accountant|"
    r"human resources|\bmarketing\b|thu ngan|chef|barista|civil engineer|mechanical|"
    r"nurse|retail|financial analyst|thiet ke do hoa|graphic designer|\bstudent\b|\bretired\b"
)

EXPLICIT_NON_IT = re.compile(
    r"\bcnc\b|lap trinh cam\b|nganh go\b|thuc pham|food safety|"
    r"gioi thieu su kien|hoi thao|\bwebinar\b|pet groom|telesales|call center"
)

STRONG_TECH_ROLE = re.compile(
    r"software engineer|software developer|\bdata (?:analyst|engineer|scientist)\b|"
    r"\b(?:backend|frontend|fullstack|ios|android) developer\b"
)


@lru_cache(maxsize=150000)
def classify_role(title):
    value = fold(title)
    if EXPLICIT_NON_IT.search(value) or (
        NON_IT.search(value) and not STRONG_TECH_ROLE.search(value)
    ):
        return {"role": None, "scope": "non_it"}
    for role, pattern in ROLE_RULES:
        if pattern.search(value):
            return {"role": role, "scope": "it"}
    return {"role": None, "scope": "unknown"}

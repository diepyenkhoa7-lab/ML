"""Các phép biến đổi dữ liệu có quy tắc rõ ràng, không học tham số từ toàn bộ dataset."""

import ast
import hashlib
import json
import math
import re
import unicodedata
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd

DEFAULT_POLICY = {
    "version": "1.0.0",
    "as_of": "2026-10-17T23:59:59+07:00",
    "user_history_before_year": 2026,
    "experience_max_years": 80,
    "annual_minimum_native_review": 1000,
    "salary_review_limits": {
        "VND_month": [1_000_000, 500_000_000],
        "USD_month": [100, 100_000],
        "USD_year": [1_000, 1_000_000],
    },
}


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
            r"(\d+(?:[.,]\d+)*)(?:\s*(trieu|million|billion|nghin|ngan|tr\b|k\b|ty\b))?", raw
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
            status="ambiguous_currency", salary_monthly_native=None, salary_monthly_vnd=None
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


SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java": "Java",
    "python": "Python",
    "sql": "SQL",
    "c++": "C++",
    "c#": "C#",
    "c": "C",
    "typescript": "TypeScript",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "vue": "Vue",
    "angularjs": "AngularJS",
    "angular": "Angular",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mssql": "SQL Server",
    "mssql server": "SQL Server",
    "sql server": "SQL Server",
    "mongodb": "MongoDB",
    ".net": ".NET",
    "dotnet": ".NET",
    "asp.net": "ASP.NET",
    "php": "PHP",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "git": "Git",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "linux": "Linux",
    "react-native": "React Native",
    "react native": "React Native",
    "power bi": "Power BI",
    "excel": "Excel",
    "spring boot": "Spring Boot",
}


def normalize_skills(value, separator=None):
    raw = text(value)
    if not raw:
        return {"skills": [], "valid": True, "missing": True}
    if separator:
        values = raw.split(separator)
    else:
        try:
            values = json.loads(raw)
        except (ValueError, TypeError):
            try:
                values = ast.literal_eval(raw)
            except (ValueError, SyntaxError):
                return {"skills": [], "valid": False, "missing": True}
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        return {"skills": [], "valid": False, "missing": True}
    unique = {}
    for item in values:
        item = text(item)
        if item:
            unique[fold(item)] = SKILL_ALIASES.get(fold(item), item)
    normalized = sorted(set(unique.values()), key=str.casefold)
    return {"skills": normalized, "valid": True, "missing": not normalized}


ROLE_RULES = [
    (role, re.compile(pattern))
    for role, pattern in [
        ("Full-stack Developer", r"full[ -]?stack"),
        (
            "ML Engineer",
            r"machine learning|\bai[ /-]?ml\b|\b(?:ai|ml) engineer|ky su ai\b",
        ),
        ("Data Scientist", r"data scien|khoa hoc du lieu|applied scientist"),
        ("Data Engineer", r"data engineer|ky su du lieu|data warehouse|big data|\betl\b"),
        ("Data Analyst", r"data (?:or business )?analyst|phan tich du lieu"),
        ("DevOps Engineer", r"devops|\bsre\b|site reliability"),
        ("QA Engineer", r"\bqa\b|\bqc\b|tester|test engineer|kiem thu|quality assurance"),
        (
            "Security Engineer",
            r"cybersecurity|infosec|security (?:engineer|analyst)|an ninh|bao mat",
        ),
        ("Cloud Engineer", r"cloud (?:infrastructure|engineer|architect)|dien toan dam may"),
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
POSITION_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"front[ -]?end",
        r"back[ -]?end",
        r"full[ -]?stack",
        r"business analyst|phan tich nghiep vu",
        r"\bqa engineer\b|\btester\b|kiem thu",
        r"software engineer|lap trinh vien",
        r"data engineer",
        r"data scientist",
        r"\bai engineer\b|machine learning engineer",
        r"\bux\b|\bui\b",
    ]
]


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


def normalize_location(value):
    raw = text(value)
    value = fold(raw)
    locations = []
    for name, pattern in [
        ("Hà Nội", r"ha[ -]?noi|hanoi"),
        ("TP.HCM", r"ho chi minh|hcm|sai gon|saigon"),
        ("Đà Nẵng", r"da nang|danang"),
    ]:
        if re.search(pattern, value):
            locations.append(name)
    remote = bool(re.search(r"remote|tu xa|work from home", value))
    if not locations and raw:
        if remote:
            locations = ["Remote"]
        else:
            locations = [re.sub(r"\s*\(mới\)", "", raw, flags=re.I).strip()]
    return {
        "locations": sorted(set(locations)),
        "is_remote": remote,
        "location": " / ".join(sorted(set(locations))) or None,
    }


def normalized_url(value):
    value = text(value)
    if not value:
        return ""
    parts = urlsplit(value)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), "")
    )


def level(value, title):
    raw = fold(value)
    source = raw or fold(title)
    for name, pattern in [
        ("Intern", r"intern|thuc tap|sinh vien"),
        ("Fresher", r"fresher|moi tot nghiep"),
        ("Junior", r"junior"),
        ("Senior", r"senior"),
        ("Lead", r"lead|truong nhom"),
        ("Manager", r"manager|truong phong|quan ly"),
        ("Executive", r"giam doc|c-suite|\bcto\b"),
        ("Employee", r"nhan vien"),
    ]:
        if re.search(pattern, source):
            return name
    return text(value) or None


@lru_cache(maxsize=150000)
def iso_date(value):
    if not text(value):
        return None
    parsed = pd.to_datetime(value, utc=True, errors="coerce", format="mixed")
    return parsed.isoformat() if not pd.isna(parsed) else None


def source_fields(source, row):
    if source == "user_vietnam_it_jobs":
        return dict(
            title=row.get("title"),
            company=row.get("company"),
            location=row.get("location"),
            country=None,
            experience=row.get("experience"),
            skills=row.get("skills"),
            separator=None,
            url=row.get("source_url"),
            posted=row.get("posted_at"),
            captured=row.get("crawl_time"),
            level=row.get("level"),
            description=row.get("requirements"),
            salary_raw=row.get("salary"),
            salary=parse_salary(row.get("salary")),
            ident=row.get("id"),
        )
    if source == "vietjobs_2025":
        return dict(
            title=row.get("job_title"),
            company=None,
            location=row.get("location"),
            country=row.get("country"),
            experience=row.get("experience_required"),
            skills=row.get("technical_skills"),
            separator=None,
            url=None,
            posted=None,
            captured=None,
            level=None,
            description="\n".join(text(row.get(k)) for k in ["description", "requirements_text"]),
            salary_raw=row.get("salary"),
            salary=parse_salary(row.get("salary"), "month"),
            ident=row["_row_index"],
        )
    if source == "dataforge_2026_08":
        return dict(
            title=row.get("title"),
            company=row.get("company_name"),
            location=row.get("location_raw"),
            country=row.get("country"),
            experience=None,
            skills=row.get("skills"),
            separator="|",
            url=row.get("url"),
            posted=row.get("posted_at"),
            captured=row.get("scraped_at"),
            level=None,
            description=None,
            salary_raw=json.dumps([numeric(row.get("salary_min")), numeric(row.get("salary_max"))]),
            salary=native_salary(
                row.get("salary_min"),
                row.get("salary_max"),
                row.get("salary_currency"),
                row.get("salary_period"),
            ),
            ident=row["_row_index"],
        )
    return dict(
        title=row.get("DevType"),
        company=None,
        location=row.get("Country"),
        country=row.get("Country"),
        experience=row.get("WorkExp"),
        skills=";".join(
            text(row.get(k))
            for k in [
                "LanguageHaveWorkedWith",
                "DatabaseHaveWorkedWith",
                "PlatformHaveWorkedWith",
                "WebframeHaveWorkedWith",
            ]
        ),
        separator=";",
        url=None,
        posted=None,
        captured=None,
        level=None,
        description=None,
        salary_raw=row.get("ConvertedCompYearly"),
        salary=native_salary(
            row.get("ConvertedCompYearly"), row.get("ConvertedCompYearly"), "USD", "year", "gross"
        ),
        ident=row.get("ResponseId"),
    )


def canonical_row(source, row, policy, role):
    f = source_fields(source, row)
    salary = f["salary"]
    experience = parse_experience(f["experience"], policy["experience_max_years"])
    skills = normalize_skills(f["skills"], f["separator"])
    loc = normalize_location(f["location"])
    country = text(f["country"]) or None
    if fold(country) in {"viet nam", "vietnam"}:
        country = "Vietnam"
    if not country and source == "user_vietnam_it_jobs":
        if not re.search(r"quoc te|nuoc ngoai|international|overseas", fold(f["location"])):
            country = "Vietnam"
    reason = []
    if role["scope"] == "unknown":
        reason.append("role_unclassified")
    title = fold(f["title"])
    if (
        source != "stackoverflow_2025"
        and "/" in title
        and sum(bool(pattern.search(title)) for pattern in POSITION_PATTERNS) > 1
    ):
        reason.append("multiple_roles_one_salary")
    # QA/support/management titles can refer to non-software industries in this general corpus.
    if source == "dataforge_2026_08" and role["role"] in {
        "QA Engineer",
        "IT Support",
        "Engineering Manager",
        "Business Analyst",
        "UX/UI Designer",
    }:
        evidence = fold(" ".join(text(row.get(k)) for k in ["title", "skills", "department"]))
        if not re.search(
            r"software|digital|\bit\b|\bict\b|python|javascript|typescript|\bjava\b|"
            r"selenium|playwright|cypress|\bsql\b|cloud|devops|automation test|web|mobile|app\b",
            evidence,
        ):
            reason.append("role_context_unverified")
    if not skills["valid"]:
        reason.append("invalid_skills")
    if experience["experience_kind"] == "invalid":
        reason.append("invalid_experience")
    benign = {"valid", "missing", "negotiable", "not_disclosed", "lower_bound", "upper_bound"}
    if salary["status"] not in benign:
        reason.append("salary_" + salary["status"])
    limits = policy["salary_review_limits"].get(f"{salary['currency']}_{salary['salary_period']}")
    if not limits and salary["salary_period"] == "year":
        monthly_limits = policy["salary_review_limits"].get(f"{salary['currency']}_month")
        if monthly_limits:
            limits = [value * 12 for value in monthly_limits]
    if limits and salary["status"] == "valid":
        if salary["salary_min"] < limits[0] or salary["salary_max"] > limits[1]:
            reason.append("salary_outside_review_limits")
    if (
        salary["status"] == "valid"
        and salary["salary_period"] == "year"
        and salary["salary_min"] < policy["annual_minimum_native_review"]
    ):
        reason.append("annual_salary_scale_review")
    posted, captured = iso_date(f["posted"]), iso_date(f["captured"])
    for name, raw, parsed in [
        ("posted", f["posted"], posted),
        ("captured", f["captured"], captured),
    ]:
        if text(raw) and parsed is None:
            reason.append("invalid_" + name + "_date")
        if parsed and pd.Timestamp(parsed) > pd.Timestamp(policy["as_of"]):
            reason.append("future_" + name + "_date")
    url = normalized_url(f["url"])
    body = text(f["description"])
    identity = url or (
        "|".join([fold(f["title"]), fold(f["location"]), fold(body)])
        if body
        else f"{source}:{f['ident']}"
    )
    target_definition = (
        "self_reported_total_compensation"
        if source == "stackoverflow_2025"
        else "advertised_salary_midpoint"
    )
    output = dict(
        record_id=f"{source}:{f['ident']}",
        group_id=hashlib.sha256(identity.encode()).hexdigest(),
        source_dataset=source,
        source_row_index=int(row["_row_index"]),
        title=text(f["title"]),
        role=role["role"],
        level=level(f["level"], f["title"]),
        company=text(f["company"]) or None,
        country=country,
        location=loc["location"],
        locations=json.dumps(loc["locations"], ensure_ascii=False),
        is_remote=loc["is_remote"]
        or (source == "dataforge_2026_08" and fold(row.get("is_remote")) in {"true", "1", "yes"}),
        skills=";".join(skills["skills"]),
        skills_json=json.dumps(skills["skills"], ensure_ascii=False),
        skills_missing=skills["missing"],
        experience_raw=text(f["experience"]) or None,
        experience_missing=experience["experience_years"] is None,
        salary_raw=text(f["salary_raw"]) or None,
        salary_min=salary["salary_min"],
        salary_max=salary["salary_max"],
        currency=salary["currency"],
        salary_period=salary["salary_period"],
        salary_basis=salary["salary_basis"],
        salary_status=salary["status"],
        salary_monthly_native=salary["salary_monthly_native"],
        salary_monthly_vnd=salary["salary_monthly_vnd"],
        compensation_annual_usd=(
            salary["salary_min"]
            if source == "stackoverflow_2025" and salary["status"] == "valid"
            else None
        ),
        target_definition=target_definition,
        posted_at=posted,
        captured_at=captured,
        source_url=url or None,
        description=body or None,
        skills_raw=text(f["skills"]) or None,
        location_raw=text(f["location"]) or None,
        salary_min_source_raw=numeric(row.get("salary_min")),
        salary_max_source_raw=numeric(row.get("salary_max")),
        review_reasons=";".join(reason),
        salary_text_corrected_numeric=False,
    )
    if source == "vietjobs_2025" and salary["status"] == "valid":
        original = [numeric(row.get("salary_min")), numeric(row.get("salary_max"))]
        parsed = [salary["salary_min"], salary["salary_max"]]
        output["salary_text_corrected_numeric"] = any(
            raw is not None and abs(raw * 1e6 - new) > 0.01 for raw, new in zip(original, parsed)
        )
    output.update(experience)
    return output


def clean_source(source, raw_df, policy):
    df = raw_df.copy(deep=True)
    df["_row_index"] = range(len(df))
    title_col = {"vietjobs_2025": "job_title", "stackoverflow_2025": "DevType"}.get(source, "title")
    url_col = {"user_vietnam_it_jobs": "source_url", "dataforge_2026_08": "url"}.get(source)
    if source == "vietjobs_2025":
        duplicate = raw_df.duplicated(keep="first")
    elif source == "stackoverflow_2025":
        duplicate = df.duplicated("ResponseId", keep="first")
    else:
        identity = df[url_col].map(normalized_url)
        time_col = (
            "updated_at"
            if "updated_at" in df
            else ("crawl_time" if "crawl_time" in df else "scraped_at")
        )
        ordering = pd.to_datetime(
            df.get(time_col, pd.Series(None, index=df.index)),
            errors="coerce",
            utc=True,
            format="mixed",
        )
        positions = pd.DataFrame({"identity": identity, "time": ordering, "position": df.index})
        positions = positions.sort_values(["time", "position"], na_position="first", kind="stable")
        duplicated_indices = positions.loc[
            positions.identity.ne("") & positions.duplicated("identity", keep="last"), "position"
        ]
        duplicate = df.index.isin(duplicated_indices)
        duplicate = pd.Series(duplicate, index=df.index)
    titles = df[title_col].fillna("").map(text)
    roles = titles.map(classify_role)
    scope = roles.map(lambda value: value["scope"])
    if source == "vietjobs_2025":
        category_it = df.category.map(fold).str.contains(r"thong_tin|cntt|information.technology")
        scope.loc[~category_it] = "non_it"
    clean, reviews, audit = [], [], []
    for row in df.to_dict("records"):
        i = row["_row_index"]
        disposition, reason = "kept", ""
        if duplicate.iloc[i]:
            disposition, reason = "duplicate", "duplicate_exact_or_source_identity"
        elif source == "user_vietnam_it_jobs" and (
            (captured := iso_date(row.get("crawl_time")))
            and pd.Timestamp(captured).year < policy["user_history_before_year"]
        ):
            disposition, reason = "quarantined_provenance", "user_historical_block_unverified"
        elif scope.iloc[i] == "non_it":
            disposition, reason = "non_it", "out_of_it_role_scope"
        output = None
        if disposition in {"kept", "quarantined_provenance"}:
            output = canonical_row(source, row, policy, roles.iloc[i])
            if disposition == "quarantined_provenance":
                output["review_reasons"] = ";".join(
                    filter(None, [output["review_reasons"], reason])
                )
            elif output["review_reasons"]:
                disposition, reason = "review", output["review_reasons"]
            if disposition == "kept":
                clean.append(output)
            else:
                reviews.append(output)
        audit.append(
            dict(
                source_dataset=source,
                source_row_index=i,
                record_id=(output["record_id"] if output else None),
                title=titles.iloc[i],
                disposition=disposition,
                reason=reason,
                group_id=output["group_id"] if output else None,
                source_url=text(row.get(url_col)) if url_col else None,
            )
        )
    return {
        "clean": pd.DataFrame(clean),
        "review": pd.DataFrame(reviews),
        "audit": pd.DataFrame(audit),
    }

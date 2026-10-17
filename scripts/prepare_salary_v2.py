"""Versioned recent VN salary data: explicit-month holdouts, weak-period train only."""

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.charts import TECHNOLOGIES  # noqa: E402
from backend.app.services.contracts import digest  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402
from scripts.data_cleaning import (  # noqa: E402
    SKILL_ALIASES,
    classify_role,
    fold,
    level,
    normalize_location,
    normalize_skills,
    parse_experience,
    parse_salary,
    text,
)

ROLES = {
    "Software Developer",
    "Backend Developer",
    "Frontend Developer",
    "Full-stack Developer",
    "Mobile Developer",
    "Embedded Engineer",
    "ML Engineer",
    "Data Engineer",
}
NUMBER = r"\d+(?:[.,]\d+)*"
SCALE = r"(?:trieu|tr\b|million|vnd|dong|usd|₫|d\b)"
MONEY = rf"{NUMBER}\s*(?:{SCALE})?"
MONTH_CLAUSE = re.compile(
    rf"{MONEY}(?:\s*[-–—~]\s*{MONEY})?\s*(?:{SCALE})?\s*"
    r"(?:/\s*(?:thang|month)|moi\s+thang|per\s+month)",
    re.I,
)
CENSORED = re.compile(r"(?:up\s*to|upto|toi da|len toi|tren|hon)\s*\d")
SKILLS = {
    name: re.compile(r"(?<![\w])" + re.escape(name) + r"(?![\w])", re.I)
    for name in sorted(TECHNOLOGIES | set(SKILL_ALIASES))
    if len(name) > 1
}


def extract_skills(requirements):
    content = text(requirements)
    found = [name for name, pattern in SKILLS.items() if pattern.search(content)]
    return normalize_skills(json.dumps(found))["skills"]


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


def prepare():
    protocol_path = ROOT / "configs/salary_v2_protocol.json"
    protocol = json.loads(protocol_path.read_text())
    source = ROOT / "data/raw/tinixai_2026"
    origin = json.loads((source / "manifest.json").read_text())
    assert origin["revision"] == protocol["input_source"].split("@")[1]
    assert checksum(source / "data.parquet") == origin["files"]["data.parquet"]["sha256"]
    frame = pd.read_parquet(source / "data.parquet")
    all_rows = len(frame)
    frame = frame[frame.year.isin(protocol["source_years"])]
    # Match titles directly, rather than relying on noisy industry labels.
    candidate = frame.job_title.fillna("").str.contains(
        r"develop|software|lập trình|lap trinh|backend|back.end|frontend|front.end|"
        r"full.stack|embedded|data engineer|kỹ sư phần mềm|ky su phan mem",
        case=False,
        regex=True,
    )
    old_ids = set()
    for split in ["valid", "test"]:
        old_ids.update(pd.read_csv(ROOT / f"data/splits/v1.0.1/vn_developer/{split}.csv").record_id)
    old = pd.read_csv(
        ROOT / "data/processed/reviewed/v1.0.1/all_candidates.csv",
        usecols=["record_id", "company"],
        low_memory=False,
    )
    old_companies = {
        re.sub(r"\W+", " ", fold(value)).strip()
        for value in old[old.record_id.isin(old_ids)].company
        if text(value)
    }
    counts = Counter(input=all_rows, recent=len(frame), title_candidates=int(candidate.sum()))
    records = []
    for raw in frame[candidate].to_dict("records"):
        role = classify_role(raw["job_title"])["role"]
        exp = parse_experience(raw["experience_level"])["experience_years"]
        company = re.sub(r"\W+", " ", fold(raw["company_name"])).strip()
        if role not in ROLES or exp is None or not company:
            counts["unsupported_role_experience_or_company"] += 1
            continue
        if company in old_companies:
            counts["old_holdout_company_excluded"] += 1
            continue
        label, reason = salary_label(raw)
        if label is None:
            counts[reason] += 1
            continue
        target, quality, evidence = label
        counts[quality] += 1
        records.append(
            dict(
                record_id=f"tinixai:{raw['id']}",
                company=raw["company_name"],
                leakage_group_id=hashlib.sha256(company.encode()).hexdigest(),
                title=raw["job_title"],
                role=role,
                level=level(raw["job_position"], raw["job_title"]) or "Unknown",
                experience_years=exp,
                location=normalize_location(raw["location"])["location"],
                skills=";".join(extract_skills(raw["requirements"])),
                salary_monthly_vnd=target,
                salary_raw=raw["salary"],
                label_quality=quality,
                period_evidence=evidence,
                source_year=int(raw["year"]),
                content_hash=digest([fold(raw["job_title"]), company, fold(raw["requirements"])]),
            )
        )
    data = pd.DataFrame(records)
    # Same text with conflicting prices is ambiguous, not independent observations.
    conflict = data.groupby("content_hash").salary_monthly_vnd.nunique()
    bad = set(conflict[conflict.gt(1)].index)
    counts["conflicting_content_rows"] = int(data.content_hash.isin(bad).sum())
    data = data[~data.content_hash.isin(bad)]
    data = data.sort_values(["label_quality", "source_year"], ascending=[False, False])
    # Explicit labels outrank weak ones when the same ad was reposted.
    data["strict_priority"] = data.label_quality.eq("explicit_month")
    data = data.sort_values(["strict_priority", "source_year"], ascending=False)
    before = len(data)
    data = (
        data.drop_duplicates("content_hash").drop(columns="strict_priority").reset_index(drop=True)
    )
    counts["duplicate_content_rows"] = before - len(data)
    strict = data[data.label_quality.eq("explicit_month")]
    if len(strict) < 75 or strict.leakage_group_id.nunique() < 40:
        raise ValueError("Not enough independent explicit-month labels for the locked protocol")
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    dev_idx, test_idx = next(splitter.split(strict, groups=strict.leakage_group_id))
    dev, test = strict.iloc[dev_idx], strict.iloc[test_idx]
    train_idx, valid_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42).split(
            dev,
            groups=dev.leakage_group_id,
        )
    )
    train, valid = dev.iloc[train_idx], dev.iloc[valid_idx]
    held = set(valid.leakage_group_id) | set(test.leakage_group_id)
    weak = data[data.label_quality.ne("explicit_month") & ~data.leakage_group_id.isin(held)]
    partitions = dict(train=train, weak_train=weak, valid=valid, test=test)
    assert not set(train.leakage_group_id) & held
    assert not set(valid.leakage_group_id) & set(test.leakage_group_id)
    assert not set(weak.leakage_group_id) & held
    folder = ROOT / f"data/splits/v{protocol['version']}/vn_developer"
    if (folder / "manifest.json").exists():
        raise ValueError("Preserve frozen v2; choose a new protocol/version instead of overwriting")
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, part in partitions.items():
        path = folder / f"{name}.csv"
        part.sort_values("record_id").to_csv(path, index=False, lineterminator="\n")
        files[name] = dict(
            path=str(path.relative_to(ROOT)),
            rows=len(part),
            groups=part.leakage_group_id.nunique(),
            sha256=checksum(path),
        )
    manifest = dict(
        schema_version="career.salary.dataset.v2",
        protocol_sha256=checksum(protocol_path),
        source=origin,
        counts=dict(counts),
        files=files,
        code_sha256=checksum(Path(__file__)),
        quality="silver explicit + weak train only",
        old_holdout_companies_sha256=digest(sorted(old_companies)),
    )
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(counts=counts, files=files), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    prepare()

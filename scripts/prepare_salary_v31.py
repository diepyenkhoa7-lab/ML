"""Freeze evidence-only development labels and independent current-source holdout."""

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.contracts import digest  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402
from scripts.data_cleaning import (  # noqa: E402
    classify_role,
    fold,
    normalize_location,
    parse_experience,
    text,
)
from scripts.prepare_salary_v2 import ROLES, extract_skills  # noqa: E402
from scripts.salary_v3_labels import CENSOR, EXCLUDED_TITLE, title_level  # noqa: E402
from scripts.salary_v31_labels import direct_label  # noqa: E402


def company_key(value):
    return re.sub(r"\W+", " ", fold(value)).strip()


def public_record(raw):
    item = raw["job_posting"]
    title = item.get("title", "")
    role = classify_role(title)["role"]
    if role not in ROLES or EXCLUDED_TITLE.search(fold(title)) or CENSOR.search(fold(title)):
        return None, "unsupported_public_role"
    if str(item.get("datePosted", ""))[:4] != "2026":
        return None, "public_not_2026_post"
    salary = item.get("baseSalary") or {}
    value = salary.get("value") or {}
    if salary.get("currency") != "VND" or value.get("unitText", "").upper() != "MONTH":
        return None, "public_currency_or_period"
    try:
        low, high = float(value["minValue"]), float(value["maxValue"])
    except (KeyError, TypeError, ValueError):
        return None, "public_not_two_numeric_bounds"
    if not 2e6 <= low <= high <= 200e6 or high / low > 3:
        return None, "public_invalid_range"
    company = (item.get("hiringOrganization") or {}).get("name")
    if not company_key(company):
        return None, "missing_company"
    body = BeautifulSoup(item.get("description") or "", "html.parser").get_text(" ", strip=True)
    content = fold(body)
    # Clear numeric experience mentions only; conflicting minimums are not silently resolved.
    experience_spans = list(
        re.finditer(
            r"(?<!\d)(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s*(?:nam\s+kinh\s+nghiem|years?\s+(?:of\s+)?experience)",
            content,
        )
    )
    years = {float(m.group(1)) for m in experience_spans}
    metadata = (item.get("experienceRequirements") or {}).get("monthsOfExperience")
    try:
        exp = float(metadata) / 12
    except (ValueError, TypeError):
        exp = next(iter(years)) if len(years) == 1 else None
    if exp is None or not 0 <= exp <= 40 or (years and any(abs(y - exp) > 0.1 for y in years)):
        return None, "missing_or_conflicting_experience"
    locations = item.get("jobLocation") or []
    if isinstance(locations, dict):
        locations = [locations]
    location = locations[0].get("address", {}).get("addressRegion") if locations else None
    if not location:
        return None, "missing_location"
    return dict(
        record_id="public:" + hashlib.sha256(raw["url"].encode()).hexdigest()[:20],
        company=company,
        leakage_group_id=digest(company_key(company)),
        title=title,
        role=role,
        level=title_level("", title),
        experience_years=exp,
        location=normalize_location(location)["location"],
        skills=";".join(extract_skills(item.get("skills") or body)),
        salary_monthly_vnd=(low + high) / 2,
        salary_min=low,
        salary_max=high,
        salary_raw=json.dumps(salary, ensure_ascii=False),
        source_url=raw["url"],
        source_year=int(str(item["datePosted"])[:4]),
        label_quality="public_jsonld_month_silver",
        period_evidence="baseSalary.currency=VND; value.unitText=MONTH; numeric minValue/maxValue",
        experience_evidence="metadata monthsOfExperience=" + str(metadata),
        content_hash=digest([fold(title), company_key(company), content]),
    ), None


def prepare():
    protocol = ROOT / "configs/salary_v31_protocol.json"
    config = json.loads(protocol.read_text())
    folder = ROOT / f"data/splits/v{config['version']}/vn_developer"
    if folder.exists():
        raise ValueError("Preserve frozen dataset; use a new version")
    old_all, old_held = set(), set()
    old = pd.read_csv(ROOT / "data/processed/reviewed/v1.0.1/all_candidates.csv", low_memory=False)
    for name in ["train", "valid", "test"]:
        ids = set(pd.read_csv(ROOT / f"data/splits/v1.0.1/vn_developer/{name}.csv").record_id)
        companies = {company_key(v) for v in old[old.record_id.isin(ids)].company if text(v)}
        old_all.update(companies)
        if name != "train":
            old_held.update(companies)
    for name in ["train", "weak_train", "valid", "test"]:
        part = pd.read_csv(ROOT / f"data/splits/v2.1.0/vn_developer/{name}.csv")
        companies = set(part.company.map(company_key))
        old_all.update(companies)
        if name in {"valid", "test"}:
            old_held.update(companies)
    source = ROOT / "data/raw/tinixai_2026"
    origin = json.loads((source / "manifest.json").read_text())
    assert checksum(source / "data.parquet") == origin["files"]["data.parquet"]["sha256"]
    frame = pd.read_parquet(source / "data.parquet")
    from scripts.collect_salary_v3 import DEVELOPER

    counts, records = Counter(), []
    for raw in frame.to_dict("records"):
        if not DEVELOPER.search(fold(raw["job_title"])):
            continue
        role = classify_role(raw["job_title"])["role"]
        exp = parse_experience(raw["experience_level"])["experience_years"]
        company = company_key(raw["company_name"])
        if role not in ROLES or exp is None or not company or company in old_held:
            counts["role_experience_company_or_old_holdout_excluded"] += 1
            continue
        label, reason = direct_label(raw)
        if label is None:
            counts[reason] += 1
            continue
        counts["direct_labels"] += 1
        counts["header_differs"] += int(label["header_differs"])
        records.append(
            dict(
                record_id=f"tinixai:{raw['id']}",
                company=raw["company_name"],
                leakage_group_id=digest(company),
                title=raw["job_title"],
                role=role,
                level=title_level(raw["job_position"], raw["job_title"]),
                experience_years=exp,
                location=normalize_location(raw["location"])["location"],
                skills=";".join(extract_skills(raw["requirements"])),
                salary_monthly_vnd=label["salary_monthly_vnd"],
                salary_min=label["low"],
                salary_max=label["high"],
                salary_raw=raw["salary"],
                label_quality=label["label_quality"],
                source_year=int(raw["year"]),
                period_evidence=label["field"] + ": " + label["evidence"],
                content_hash=digest([fold(raw["job_title"]), company, fold(raw["requirements"])]),
            )
        )
    data = pd.DataFrame(records)
    conflict = data.groupby("content_hash").salary_monthly_vnd.nunique()
    data = data[~data.content_hash.isin(conflict[conflict.gt(1)].index)]
    data = data.sort_values("source_year", ascending=False).drop_duplicates("content_hash")
    recent = data[data.source_year.ge(2025)]
    train_ix, valid_ix = next(
        GroupShuffleSplit(test_size=0.25, random_state=31415).split(
            recent,
            groups=recent.leakage_group_id,
        )
    )
    train, valid = recent.iloc[train_ix], recent.iloc[valid_ix]
    older = data[data.source_year.lt(2025) & ~data.leakage_group_id.isin(valid.leakage_group_id)]
    public_folder = ROOT / "data/raw/joboko_20261018"
    public_manifest = json.loads((public_folder / "manifest.json").read_text())
    raw_path = ROOT / public_manifest["file"]["path"]
    assert checksum(raw_path) == public_manifest["file"]["sha256"]
    seen_companies = old_all | set(data.company.map(company_key))
    for name in ["train", "older_train", "valid", "test"]:
        seen_companies.update(
            pd.read_csv(ROOT / f"data/splits/v3.0.0/vn_developer/{name}.csv").company.map(
                company_key
            )
        )
    test_records = []
    for line in raw_path.read_text().splitlines():
        record, reason = public_record(json.loads(line))
        if record is None:
            counts[reason] += 1
            continue
        if company_key(record["company"]) in seen_companies:
            counts["public_previously_seen_company_excluded"] += 1
            continue
        test_records.append(record)
    test = pd.DataFrame(test_records)
    if len(test):
        conflict = test.groupby("content_hash").salary_monthly_vnd.nunique()
        test = test[~test.content_hash.isin(conflict[conflict.gt(1)].index)]
        test = test.drop_duplicates("content_hash")
    else:
        raise ValueError("No independent public labels; cannot claim holdout")
    folder.mkdir(parents=True)
    files = {}
    for name, part in dict(train=train, older_train=older, valid=valid, test=test).items():
        path = folder / f"{name}.csv"
        part.sort_values("record_id").to_csv(path, index=False, lineterminator="\n")
        files[name] = dict(
            path=str(path.relative_to(ROOT)),
            sha256=checksum(path),
            rows=len(part),
            groups=part.leakage_group_id.nunique(),
        )
    panel = ROOT / "models/salary/v2_042e3aa1a886/training_snapshot.csv"
    manifest = dict(
        schema_version="career.salary.dataset.v3",
        protocol_sha256=checksum(protocol),
        code_sha256=checksum(Path(__file__)),
        labels_code_sha256=checksum(ROOT / "scripts/salary_v31_labels.py"),
        inherited_labels_code_sha256=checksum(ROOT / "scripts/salary_v3_labels.py"),
        sources=dict(tinixai=origin, public_jobs=public_manifest),
        counts=dict(counts),
        files=files,
        excluded_old_holdout_company_keys_sha256=digest(sorted(old_held)),
        public_excluded_all_seen_company_keys_sha256=digest(sorted(seen_companies)),
        market_panel=dict(path=str(panel.relative_to(ROOT)), sha256=checksum(panel)),
        quality="Evidence-only silver; zero assumed-period labels; not human verified gold",
    )
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(counts=counts, files=files), indent=2))


if __name__ == "__main__":
    prepare()

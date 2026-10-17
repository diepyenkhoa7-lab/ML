"""Lập hồ sơ nguồn và xuất các tập ứng viên; chưa chuẩn hóa nhãn/huấn luyện model."""

import ast
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/source_views"
REPORT = ROOT / "outputs/data_quality"


def fold(value):
    text = unicodedata.normalize("NFKD", str(value)).casefold().replace("đ", "d")
    return "".join(char for char in text if not unicodedata.combining(char))


def counts(series):
    return {str(key): int(value) for key, value in series.value_counts(dropna=False).items()}


def dates(series):
    parsed = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    return {
        "valid": int(parsed.notna().sum()),
        "missing_or_invalid": int(parsed.isna().sum()),
        "min": str(parsed.min()),
        "max": str(parsed.max()),
        "year_counts": counts(parsed.dt.year.astype("Int64")),
        "after_retrieval_day": int((parsed > pd.Timestamp("2026-10-17T23:59:59+07:00")).sum()),
    }


def skill_count(value):
    if pd.isna(value) or not str(value).strip():
        return 0
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return -1
    return len(parsed) if isinstance(parsed, list) else -1


def basic(df, path):
    return {
        "file": str(path.relative_to(ROOT)),
        "rows": len(df),
        "column_count": len(df.columns),
        "columns": df.columns.tolist(),
        "missing_by_column": df.isna().sum().astype(int).to_dict(),
        "exact_duplicate_rows": int(df.duplicated().sum()),
    }


def save_view(df, name):
    path = OUT / name
    df.to_csv(path, index=False)
    return {"path": str(path.relative_to(ROOT)), "rows": len(df)}


def profile_user():
    path = ROOT / "data/raw/user_vietnam_it_jobs/vietnam_it_job_posts.csv"
    if not path.exists():
        return {"status": "not_downloaded"}
    df = pd.read_csv(path, low_memory=False)
    report = basic(df, path)
    salary = df.salary.fillna("").map(fold)
    negotiable = salary.str.contains(r"thoa thuan|thuong luong|negotiable|competitive", regex=True)
    numeric = salary.str.contains(r"\d", regex=True) & ~negotiable
    mixed_unit = salary.str.contains(r"\$|usd", regex=True) & salary.str.contains(
        r"trieu|\d\s*tr\b|vnd|₫", regex=True
    )
    skills = df.skills.map(skill_count)
    posted = pd.to_datetime(df.posted_at, errors="coerce", utc=True, format="mixed")
    crawled = pd.to_datetime(df.crawl_time, errors="coerce", utc=True, format="mixed")
    history = crawled.dt.year.lt(2026)
    report.update(
        {
            "source_platforms": counts(df.source_platform),
            "posted_at": dates(df.posted_at),
            "crawl_time": dates(df.crawl_time),
            "salary_nonempty": int(df.salary.notna().sum()),
            "salary_negotiable": int(negotiable.sum()),
            "salary_contains_numbers": int(numeric.sum()),
            "salary_mixed_currency_scale_flags": int(mixed_unit.sum()),
            "rows_with_skills": int((skills > 0).sum()),
            "invalid_skill_lists": int((skills < 0).sum()),
            "duplicate_source_urls": int(df.duplicated("source_url").sum()),
            "duplicate_job_hashes": int(df.duplicated("job_hash").sum()),
            "requirements_missing": int(df.requirements.isna().sum()),
            "origin_and_license": "unknown; user has no original dataset download URL",
            "timestamp_verification": "CSV timestamps; crawl history not independently verified",
            "historical_block_needs_provenance_review": int(history.sum()),
            "historical_year_platform_counts": pd.crosstab(
                crawled.loc[history].dt.year, df.loc[history, "source_platform"]
            ).to_dict(),
            "history_note": (
                "100 rows/platform/year in 2018–2025; hist-style URLs. Origin unverified."
            ),
        }
    )
    candidates = df.loc[posted.dt.year.eq(2026)].copy()
    candidates["source_dataset"] = "user_vietnam_it_jobs"
    candidates["record_id"] = "user-vn:" + candidates.id.astype(str)
    candidates["salary_status"] = "missing"
    candidates.loc[negotiable.reindex(candidates.index), "salary_status"] = "negotiable"
    candidates.loc[numeric.reindex(candidates.index), "salary_status"] = (
        "numeric_text_needs_parsing"
    )
    candidates["salary_mixed_unit_flag"] = mixed_unit.reindex(candidates.index)
    report["view_2026"] = save_view(candidates, "user_vietnam_it_jobs_2026.csv")
    report["view_history_for_review"] = save_view(
        df.loc[history], "user_vietnam_it_jobs_history_provenance_review.csv"
    )
    return report


def profile_vietjobs():
    path = ROOT / "data/raw/vietjobs_2025/VietJobs.csv"
    if not path.exists():
        return {"status": "not_downloaded"}
    df = pd.read_csv(path, low_memory=False)
    report = basic(df, path)
    categories = df.category.fillna("").map(fold)
    mask = categories.str.contains(r"thong_tin|cntt|information.technology|digital.engineering")
    subset = df.loc[mask].copy()
    if subset.empty:
        raise ValueError(f"Chưa nhận diện được category IT: {df.category.unique().tolist()}")
    positive = pd.to_numeric(subset.salary_min, errors="coerce").gt(0) & pd.to_numeric(
        subset.salary_max, errors="coerce"
    ).gt(0)
    mismatch = 0
    for row in df.itertuples():
        match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*triệu\s*", str(row.salary)
        )
        if match and pd.notna(row.salary_min) and pd.notna(row.salary_max):
            low, high = map(float, match.groups())
            mismatch += int(
                abs(low - float(row.salary_min)) > 0.001
                or abs(high - float(row.salary_max)) > 0.001
            )
    report.update(
        {
            "categories": counts(df.category),
            "it_categories_selected": counts(subset.category),
            "it_rows": len(subset),
            "it_positive_two_bound_salary_rows": int(positive.sum()),
            "salary_units": "million VND/month per paper; source numeric columns can lose decimals",
            "numeric_vs_text_range_mismatch_rows": mismatch,
            "rows_with_skills_it": int((subset.technical_skills.map(skill_count) > 0).sum()),
            "per_record_posted_dates": False,
            "per_record_source_urls": False,
            "period_note": "README: July–October 2025; paper: July 2025; unresolved discrepancy",
            "annotation_note": "GPT-4o/Gemini-assisted extraction; labels require review",
        }
    )
    subset.insert(0, "source_row_index", subset.index)
    subset.insert(0, "source_dataset", "vietjobs_2025")
    report["view_it"] = save_view(subset, "vietjobs_it_candidates.csv")
    return report


def profile_so():
    path = ROOT / "data/raw/stackoverflow_2025/survey_results_public.csv"
    if not path.exists():
        return {"status": "not_downloaded"}
    df = pd.read_csv(path, low_memory=False)
    report = basic(df, path)
    salary = pd.to_numeric(df.ConvertedCompYearly, errors="coerce")
    paid = salary.gt(0) & salary.lt(float("inf"))
    vn = df.Country.fillna("").map(fold).isin(["viet nam", "vietnam"])
    columns = [
        "ResponseId",
        "MainBranch",
        "Country",
        "DevType",
        "WorkExp",
        "YearsCode",
        "EdLevel",
        "Employment",
        "RemoteWork",
        "OrgSize",
        "ICorPM",
        "Industry",
        "LanguageHaveWorkedWith",
        "DatabaseHaveWorkedWith",
        "PlatformHaveWorkedWith",
        "WebframeHaveWorkedWith",
        "Currency",
        "CompTotal",
        "ConvertedCompYearly",
    ]
    report.update(
        {
            "salary_positive_rows": int(paid.sum()),
            "vietnam_rows": int(vn.sum()),
            "vietnam_salary_positive_rows": int((vn & paid).sum()),
            "positive_salary_with_workexp_rows": int((paid & df.WorkExp.notna()).sum()),
            "salary_units": "ConvertedCompYearly: USD/year, self-reported total compensation",
            "salary_max_usd_year": float(salary.max()),
            "not_job_demand": True,
            "post_dates_available": False,
            "outlier_handling": "Not removed here; assess on training data before fitting",
        }
    )
    subset = df.loc[paid, columns].copy()
    subset.insert(0, "source_dataset", "stackoverflow_2025")
    report["view_salary"] = save_view(subset, "stackoverflow_2025_salary_candidates.csv")
    return report


def profile_dataforge():
    path = ROOT / "data/raw/dataforge_2026_08/extracted/data/jobs.csv"
    if not path.exists():
        return {"status": "not_downloaded"}
    df = pd.read_csv(path, low_memory=False)
    report = basic(df, path)
    low = pd.to_numeric(df.salary_min, errors="coerce")
    high = pd.to_numeric(df.salary_max, errors="coerce")
    positive = low.gt(0) & high.gt(0) & high.ge(low)
    software = df.title.fillna("").str.contains(
        r"software|developer|programmer|devops|front[ -]?end|back[ -]?end|full[ -]?stack|"
        r"data engineer|data scientist|machine learning|\bml engineer\b|\bsre\b|site reliability|"
        r"\bqa\b|quality assurance engineer|cloud engineer|security engineer|\bcybersecurity\b|"
        r"\bdba\b|database (?:administrator|engineer)|mobile engineer|platform engineer|firmware",
        case=False,
        regex=True,
    )
    report.update(
        {
            "salary_positive_ordered_ranges": int(positive.sum()),
            "software_title_candidates": int(software.sum()),
            "software_salary_candidates": int((software & positive).sum()),
            "salary_currency_counts": counts(df.salary_currency),
            "salary_period_counts": counts(df.salary_period),
            "country_counts": counts(df.country),
            "posted_at": dates(df.posted_at),
            "scraped_at": dates(df.scraped_at),
            "duplicate_urls": int(df.duplicated("url").sum()),
            "salary_inverted_ranges": int((low.notna() & high.notna() & high.lt(low)).sum()),
            "full_description_in_free_package": False,
            "numeric_experience_column": False,
            "selection_note": "Title regex; review needed; some non-software roles may remain",
            "license_discrepancy": (
                "HF/site: CC BY-NC 4.0; bundled LICENSE.md: Tier 1 Internal Analytics. "
                "Model-training/redistribution terms need clarification."
            ),
        }
    )
    subset = df.loc[software & positive].copy()
    subset.insert(0, "source_dataset", "dataforge_2026_08")
    report["view_software_salary"] = save_view(
        subset, "dataforge_2026_08_software_salary_candidates.csv"
    )
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    result = {
        "profiled_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Source inventory and candidate subsets; not final clean training data",
        "sources": {
            "user_vietnam_it_jobs": profile_user(),
            "vietjobs_2025": profile_vietjobs(),
            "stackoverflow_2025": profile_so(),
            "dataforge_2026_08": profile_dataforge(),
        },
    }
    (REPORT / "source_inventory.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    views = {
        "user_vietnam_it_jobs": ("view_2026", "posted_at year 2026; salary may be missing"),
        "vietjobs_2025": ("view_it", "IT category; salary may be missing or need repair"),
        "stackoverflow_2025": ("view_salary", "positive ConvertedCompYearly, USD/year"),
        "dataforge_2026_08": (
            "view_software_salary",
            "software title regex + positive salary range",
        ),
    }
    summary = []
    for source, info in result["sources"].items():
        view_key, selection = views[source]
        view = info.get(view_key, {})
        summary.append(
            {
                "source_id": source,
                "raw_file": info.get("file"),
                "raw_rows": info.get("rows"),
                "candidate_file": view.get("path"),
                "candidate_rows": view.get("rows"),
                "selection": selection,
            }
        )
    pd.DataFrame(summary).to_csv(REPORT / "source_summary.csv", index=False)
    for name, info in result["sources"].items():
        print(
            name,
            {
                key: value
                for key, value in info.items()
                if key
                in {
                    "rows",
                    "status",
                    "it_rows",
                    "salary_positive_rows",
                    "vietnam_salary_positive_rows",
                    "software_salary_candidates",
                }
            },
        )


if __name__ == "__main__":
    main()

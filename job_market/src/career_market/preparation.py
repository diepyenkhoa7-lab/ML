"""Prepare traceable EDA records; salary eligibility never initiates training."""

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

from .postings import posting_key

RULES_VERSION = "eda-v1"


def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def posting_date(raw):
    text = raw.get("announcement_date", raw.get("date_posted", ""))
    for format in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return text, datetime.strptime(text, format).date().isoformat()
        except ValueError:
            pass
    return text, None


def prepare_records(service, records):
    rows, seen, groups = [], {}, defaultdict(list)
    for record in records:
        raw = record.raw
        title = raw.get("job_title", raw.get("title", ""))
        company = raw.get("company_title", raw.get("company", ""))
        description, requirements = raw.get("job_description", ""), raw.get("job_requirements", "")
        date_raw, date = posting_date(raw)
        row = {
            "row_id": f"{record.source_id}:{len(rows) + 1}",
            "source_id": record.source_id,
            "job_id": record.job_id,
            "job_url": record.job_url,
            "title_raw": title,
            "company_raw": company,
            "location_raw": raw.get("location", ""),
            "salary_raw": raw.get("salary", ""),
            "experience_raw": raw.get("exp", raw.get("experience", "")),
            "date_raw": date_raw,
            "posting_date": date,
            "date_kind": "posting",
            "has_job_description": bool(description or requirements),
            "raw": dict(raw),
            **service.classify_role(title, description, requirements),
            **service.normalize_locations(raw.get("location", "")),
            **service.normalize_salary(raw.get("salary", "")),
            **service.normalize_experience(raw.get("exp", raw.get("experience", ""))),
            **service.extract_skills(title, description, requirements),
            "duplicate_of": None,
        }
        row["work_mode_evidence"] = []
        if "Remote" in row["work_modes"]:
            row["work_mode_evidence"].append({"field": "location", "text": row["location_raw"]})
        if re.search(r"\bremote\b", title, re.I) and not re.search(
            r"\b(?:no|not) remote\b", title, re.I
        ):
            if "Remote" not in row["work_modes"]:
                row["work_modes"].append("Remote")
            row["work_mode_evidence"].append({"field": "title", "text": title})
        try:
            row["posting_id"] = posting_key(record.source_id, record.job_url, record.job_id)
        except ValueError:
            row["posting_id"] = None
        group_fields = [
            company.casefold().strip(),
            title.casefold().strip(),
            sorted(row["locations"]),
            description.strip(),
            requirements.strip(),
            row["experience_raw"],
            row["salary_raw"],
        ]
        row["repost_group_id"] = digest(group_fields)
        groups[row["repost_group_id"]].append(row)
        if row["posting_id"] is None:
            row["partition"] = "invalid_identity"
        elif row["posting_id"] in seen:
            row["partition"] = "duplicates"
            row["duplicate_of"] = seen[row["posting_id"]]
        else:
            seen[row["posting_id"]] = row["row_id"]
            row["partition"] = {"matched": "eda", "review": "role_review"}.get(
                row["role_status"], "out_of_scope"
            )
        reasons = []
        if row["partition"] != "eda":
            reasons.append(row["partition"])
        for domain, valid in (
            ("location", "normalized"),
            ("experience", "ok"),
            ("salary", "valid"),
        ):
            if row[f"{domain}_status"] != valid:
                reasons.append(f"{domain}: {row[f'{domain}_reason']}")
        if not date:
            reasons.append("date: chưa có ngày đăng hợp lệ")
        row["review_reasons"] = reasons
        rows.append(row)
    counts = Counter(row["partition"] for row in rows)
    eda = [row for row in rows if row["partition"] == "eda"]
    targets = [row for row in eda if row["salary_target_vnd_month"] is not None]
    return {
        "rules_version": RULES_VERSION,
        "summary": {
            "raw_rows": len(rows),
            "duplicates": counts["duplicates"],
            "invalid_identity": counts["invalid_identity"],
            "out_of_scope": counts["out_of_scope"],
            "role_review": counts["role_review"],
            "eda_postings": len(eda),
            "salary_targets": len(targets),
        },
        "rows": rows,
        "eda": eda,
        "targets": targets,
        "review": [row for row in rows if row["review_reasons"]],
        "duplicates": [row for row in rows if row["partition"] == "duplicates"],
        "repost_groups": [
            {
                "group_id": key,
                "evidence": "same_observed_fields",
                "row_ids": [r["row_id"] for r in members],
                "posting_ids": sorted({r["posting_id"] for r in members if r["posting_id"]}),
            }
            for key, members in groups.items()
            if len(members) > 1
        ],
        "ml_state": "blocked_pending_salary_gate",
    }

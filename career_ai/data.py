import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["market", "role", "location", "experience_years", "skills"]
SCALES = {"international": 1000.0, "vietnam": 1000000.0}
SKILLS_PATTERN = (
    r"\b(?:python|java|javascript|typescript|sql|react|angular|docker|kubernetes|"
    r"aws|azure|golang|rust|php|linux|git|node\.js)\b"
)
UNITS = {"international": "USD/year", "vietnam": "VND/month"}


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def prompt(row):
    return "Estimate compensation from this profile:\n" + json.dumps(
        {k: row[k] for k in FEATURES}, ensure_ascii=False, sort_keys=True
    )


def company_groups(records):
    """Keep company and identical substantive job bodies in one connected group."""
    parent = {}
    signatures = {}

    def find(key):
        parent.setdefault(key, key)
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    for row in records:
        company = "company:" + str(row["company_name"]).strip().casefold()
        find(company)
        body = re.sub(r"\s+", " ", str(row["requirements"])).strip().casefold()
        if len(body) < 100:
            continue
        key = hashlib.sha256((str(row["job_title"]).casefold() + body).encode()).hexdigest()
        if key in signatures:
            a, b = find(company), find(signatures[key])
            parent[max(a, b)] = min(a, b)
        signatures[key] = company
    return {company: find(company) for company in parent}


def prepare():
    out = ROOT / "data/tensorflow_v1"
    if out.exists():
        raise ValueError("Frozen dataset exists; do not overwrite")
    raw = ROOT / "data/raw/stackoverflow_2024/survey_results_public.csv"
    f = pd.read_csv(raw, low_memory=False)
    technologies = [
        "LanguageHaveWorkedWith",
        "DatabaseHaveWorkedWith",
        "PlatformHaveWorkedWith",
        "WebframeHaveWorkedWith",
        "MiscTechHaveWorkedWith",
    ]
    skills = (
        f[technologies]
        .fillna("")
        .agg(";".join, axis=1)
        .map(lambda s: ";".join(sorted(set(x.strip().lower() for x in s.split(";") if x.strip()))))
    )
    global_data = pd.DataFrame(
        dict(
            market="international",
            role=f.DevType,
            location=f.Country,
            experience_years=pd.to_numeric(f.WorkExp, errors="coerce"),
            skills=skills,
            salary=pd.to_numeric(f.ConvertedCompYearly, errors="coerce"),
        )
    )
    reasons = pd.Series("accepted", index=global_data.index)
    reasons.loc[global_data.isna().any(axis=1)] = "missing_required_field"
    reasons.loc[~global_data.salary.between(1000, 1000000)] = "salary_outside_study_domain"
    reasons.loc[~global_data.experience_years.between(0, 80)] = "invalid_experience"
    eligible = reasons.eq("accepted")
    duplicates = global_data.loc[eligible].duplicated()
    reasons.loc[duplicates[duplicates].index] = "duplicate_profile_and_target"
    global_audit = pd.DataFrame(dict(source_index=reasons.index, reason=reasons.values))
    global_data = global_data.loc[reasons.eq("accepted")].copy()
    global_data["group"] = pd.util.hash_pandas_object(global_data[FEATURES], index=False).astype(
        str
    )
    global_data["source_id"] = global_data.index.astype(str)
    global_data["source_dataset"] = "stackoverflow_2024"
    global_data["experience_kind"] = "self_reported_work_experience"
    # Reaudit original strings: never promote the legacy assumed-month labels.
    vnraw = ROOT / "data/raw/tinixai_2026/data.parquet"
    vn = pd.read_parquet(vnraw)
    from .source_parsing import classify_role, parse_experience
    from .vn_labels import salary_label

    candidates = vn[
        vn.job_title.fillna("").str.contains(
            "developer|software|frontend|backend|full.?stack|lập trình|"
            "data engineer|machine learning",
            case=False,
            regex=True,
        )
    ]
    group_map = company_groups(candidates.to_dict("records"))
    rows = []
    audit = []
    for i, r in candidates.iterrows():
        label, reason = salary_label(r.to_dict())
        experience_info = parse_experience(r.experience_level)
        experience = experience_info.get("experience_years")
        role = classify_role(r.job_title)["role"]
        keep = (
            label is not None
            and label[1] == "explicit_month"
            and experience is not None
            and role is not None
            and pd.notna(r.location)
        )
        audit.append(
            dict(
                source_index=int(i),
                source_id=str(r.id),
                accepted=keep,
                reason=(
                    "accepted_explicit_month"
                    if keep
                    else reason or "missing_role_experience_location_or_explicit_period"
                ),
                experience_kind=experience_info["experience_kind"],
            )
        )
        if not keep:
            continue
        text = str(r.requirements).lower()
        found = sorted(
            set(
                re.findall(
                    SKILLS_PATTERN,
                    text,
                )
            )
        )
        rows.append(
            dict(
                market="vietnam",
                role=str(role),
                location=str(r.location),
                experience_years=float(experience),
                skills=";".join(found),
                salary=label[0],
                source_id=str(r.id),
                source_dataset="tinixai_2026",
                experience_kind=experience_info["experience_kind"],
                group=group_map["company:" + str(r.company_name).strip().casefold()],
            )
        )
    vietnam = pd.DataFrame(rows).drop_duplicates(subset=[*FEATURES, "salary", "group"])
    if len(vietnam) < 30 or vietnam.group.nunique() < 10:
        raise ValueError(
            f"Insufficient strict VN labels: {len(vietnam)} rows; audit needed before training"
        )
    language_rows = candidates.to_dict("records")
    partitions = {s: [] for s in ["train", "valid", "test"]}
    for frame in [global_data, vietnam]:
        dev, test = next(
            GroupShuffleSplit(test_size=0.2, random_state=42).split(frame, groups=frame.group)
        )
        a = frame.iloc[dev]
        train, valid = next(
            GroupShuffleSplit(test_size=0.1875, random_state=42).split(a, groups=a.group)
        )
        for name, part in [
            ("train", a.iloc[train]),
            ("valid", a.iloc[valid]),
            ("test", frame.iloc[test]),
        ]:
            partitions[name].append(part)
    out.mkdir()
    files = {}
    for name, parts in partitions.items():
        frame = pd.concat(parts, ignore_index=True)
        frame.to_csv(out / f"{name}.csv", index=False)
        files[name] = dict(
            sha256=digest(out / f"{name}.csv"),
            rows=len(frame),
            markets=frame.market.value_counts().to_dict(),
        )
    for split, parts in partitions.items():
        groups = set(pd.concat(parts).group)
        examples = []
        for r in language_rows:
            group = group_map["company:" + str(r["company_name"]).strip().casefold()]
            if group not in groups:
                continue
            role = classify_role(r["job_title"])["role"]
            if not role:
                continue
            body = str(r["requirements"])
            skills = sorted(
                set(
                    re.findall(
                        SKILLS_PATTERN,
                        body.lower(),
                    )
                )
            )
            examples.append(
                dict(
                    prompt="Extract JSON role, experience_years, skills from this job. "
                    "Missing values are null.\n"
                    + str(r["job_title"])
                    + "\n"
                    + str(r["experience_level"])
                    + "\n"
                    + body,
                    answer=dict(
                        role=role,
                        experience_years=parse_experience(r["experience_level"]).get(
                            "experience_years"
                        ),
                        skills=skills,
                    ),
                    group=group,
                    source_id=str(r["id"]),
                    label_quality="source_derived_silver",
                )
            )
        examples = list(
            {
                json.dumps({k: e[k] for k in ["prompt", "answer", "group"]}, sort_keys=True): e
                for e in examples
            }.values()
        )
        (out / (split + ".jsonl")).write_text(
            "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in examples)
        )
    global_audit.to_csv(out / "international_audit.csv", index=False)
    artifacts = {p.name: digest(p) for p in out.glob("*.jsonl")}
    artifacts["international_audit.csv"] = digest(out / "international_audit.csv")
    pd.DataFrame(audit).to_csv(out / "vn_audit.csv", index=False)
    artifacts["vn_audit.csv"] = digest(out / "vn_audit.csv")
    write(
        out / "manifest.json",
        dict(
            files=files,
            artifacts=artifacts,
            raw={str(p.relative_to(ROOT)): digest(p) for p in [raw, vnraw]},
            units=UNITS,
            experience_policy="VN interval/lower-bound experience uses stated minimum; "
            "see experience_kind.",
            note="Previously studied sources; new split is not a newly collected "
            "blind benchmark. VN labels are source-derived silver.",
        ),
    )
    return files


def load(split):
    folder = ROOT / "data/tensorflow_v1"
    manifest = json.loads((folder / "manifest.json").read_text())
    path = folder / f"{split}.csv"
    if digest(path) != manifest["files"][split]["sha256"]:
        raise ValueError("Dataset checksum mismatch")
    return pd.read_csv(path).fillna({"skills": ""})


def load_language(split):
    folder = ROOT / "data/tensorflow_v1"
    manifest = json.loads((folder / "manifest.json").read_text())
    path = folder / f"{split}.jsonl"
    if digest(path) != manifest["artifacts"][path.name]:
        raise ValueError("Language dataset checksum mismatch")
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def features(frame, vocabulary=None):
    records = []
    for r in frame.to_dict("records"):
        record = {f"{k}={r[k]}": 1.0 for k in ["market", "role", "location"]}
        record["experience_years"] = float(r["experience_years"])
        record.update({"skill=" + s: 1.0 for s in str(r["skills"]).split(";") if s})
        records.append(record)
    if vocabulary is None:
        vocabulary = sorted({k for r in records for k in r})
    return np.asarray(
        [[r.get(k, 0.0) for k in vocabulary] for r in records], dtype="float32"
    ), vocabulary


def baseline_normalization(x, vocabulary):
    # Standardize the continuous feature only; rare one-hot categories stay 0/1.
    mean = np.zeros(x.shape[1], dtype="float32")
    variance = np.ones(x.shape[1], dtype="float32")
    i = vocabulary.index("experience_years")
    mean[i] = x[:, i].mean()
    variance[i] = max(float(x[:, i].var()), 1.0)
    return mean, variance


def target(frame):
    return np.log1p(frame.salary.to_numpy() / frame.market.map(SCALES).to_numpy()).astype("float32")


def inverse(values, markets):
    values = np.asarray(values).reshape(-1)
    if not np.isfinite(values).all() or (values < 0).any() or (values > 30).any():
        raise ValueError("Invalid prediction domain")
    return np.expm1(values) * np.array([SCALES[m] for m in markets])


def validate_profile(row):
    result = {k: row.get(k) for k in FEATURES}
    if result["market"] not in UNITS:
        raise ValueError("market must be international or vietnam")
    for k in ["role", "location"]:
        if not isinstance(result[k], str) or not result[k].strip():
            raise ValueError("Missing " + k)
    result["experience_years"] = float(result["experience_years"])
    if not np.isfinite(result["experience_years"]) or not 0 <= result["experience_years"] <= 80:
        raise ValueError("Experience must be 0..80 years")
    skills = result["skills"]
    if isinstance(skills, list):
        if any(not isinstance(s, str) for s in skills):
            raise ValueError("Skills must be strings")
        skills = ";".join(skills)
    if not isinstance(skills, str):
        raise ValueError("Missing skills")
    result["skills"] = ";".join(
        sorted({s.strip().lower() for s in re.split("[;,|]", skills) if s.strip()})
    )
    return result

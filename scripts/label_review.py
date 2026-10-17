"""Rà soát nhãn và nhóm danh tính trước khi chia tập; không fit features/model."""

import hashlib
import math
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from scripts.data_cleaning import fold, normalized_url, numeric, text

DEFAULT_POLICY = {
    "version": "1.0.1",
    "seed": 42,
    "fractions": [0.7, 0.15, 0.15],
    "minimum_cohort_groups": 50,
    "minimum_partition_rows": 5,
    "maximum_salary_range_ratio": 5,
    "near_description_similarity": 0.92,
    "near_title_similarity": 0.90,
    "near_skills_jaccard": 0.85,
    "minimum_description_chars": 200,
    "developer_roles": [
        "Software Developer",
        "Backend Developer",
        "Frontend Developer",
        "Full-stack Developer",
        "Mobile Developer",
        "Embedded Engineer",
        "ML Engineer",
        "Data Engineer",
    ],
}
NON_SOFTWARE = re.compile(
    r"footwear|construction supervisor|qc.*(?:vinfast|vung ang)|"
    r"ielts.*tester|english.*tester|giao vien|gia su|tro giang|teaching assistant|"
    r"research and teaching|lap trinh.*(?:plc|ddc)|lap trinh khuon mau|"
    r"chien luoc gia sang tao|chu so huu san pham|kiem tien ads|"
    r"tiep thi|cham soc khach hang qa|nhan vien qc$"
)
SOFTWARE_QA = re.compile(
    r"software|phan mem|\bapi\b|\bsql\b|\berp\b|selenium|playwright|"
    r"test.?case|test.?plan|postman|jira|bug|kiem thu|\btester\b|\bweb\b"
)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def identity_text(value):
    """Normalize for grouping only; numbers/salary snippets never become model features."""
    value = fold(value)
    value = re.sub(r"\d+(?:[.,]\d+)*", " ", value)
    return re.sub(r"\W+", " ", value).strip()


def review_labels(frame, policy, overrides=None):
    df = frame.copy(deep=True)
    df["review_status"] = "accepted"
    df["review_reasons"] = ""
    override_map = {row["record_id"]: row for row in (overrides or [])}
    for i, row in df.iterrows():
        reasons = []
        low, high, target = (numeric(row.get(k)) for k in ["salary_min", "salary_max", "target"])
        if target is None or target <= 0:
            reasons.append("invalid_target")
        if row.source_dataset != "stackoverflow_2025":
            if low is None or high is None or low <= 0 or high < low:
                reasons.append("invalid_source_range")
            else:
                divisor = 12 if row.salary_period == "year" else 1
                expected = (low + high) / (2 * divisor)
                if target is None or not math.isclose(target, expected, rel_tol=1e-9, abs_tol=0.01):
                    reasons.append("target_source_mismatch")
                if high / low > policy["maximum_salary_range_ratio"]:
                    reasons.append("wide_salary_range")
            title = fold(row.title)
            if NON_SOFTWARE.search(title):
                reasons.append("role_outside_or_misclassified")
            if row.cohort == "vn_it" and re.search(
                r"sang nhat lam|lam viec (?:tai|o) (?:nhat ban|japan|han quoc|singapore)",
                fold(row.get("description")),
            ):
                reasons.append("vietnam_work_location_conflict")
            if row.role == "QA Engineer":
                evidence = " ".join(fold(row.get(k)) for k in ["title", "skills", "description"])
                if not SOFTWARE_QA.search(evidence):
                    reasons.append("qa_software_context_unverified")
        elif target is None or low is None or not math.isclose(target, low):
            reasons.append("target_source_mismatch")
        if row.salary_period not in {"month", "year"}:
            reasons.append("unsupported_salary_period")
        if row.cohort == "vn_it" and text(row.get("country")) != "Vietnam":
            reasons.append("vietnam_location_unverified")
        if row.source_dataset == "user_vietnam_it_jobs":
            if row.get("platform") == "ybox" and not text(row.get("description")):
                reasons.append("salary_without_supporting_text_ybox")
        decision = override_map.get(row.record_id)
        if decision and decision["action"] in {"review", "exclude"}:
            reasons.append("inspected:" + decision["reason"])
        if reasons:
            df.at[i, "review_status"] = "review"
            df.at[i, "review_reasons"] = ";".join(sorted(set(reasons)))
    # Only identical source identity/content is collapsed. Near matches are grouped, not deleted.
    for _, group in df.groupby("group_id", sort=True):
        if len(group) < 2:
            continue
        units = group[["currency", "salary_period", "salary_basis"]].drop_duplicates()
        conflict = len(units) > 1 or group.target.round(4).nunique() > 1
        if conflict:
            for i in group.index:
                prior = df.at[i, "review_reasons"]
                df.at[i, "review_status"] = "review"
                df.at[i, "review_reasons"] = ";".join(
                    filter(None, [prior, "conflicting_labels_same_identity"])
                )
        else:
            eligible = group[group.review_status.eq("accepted")].copy()
            if len(eligible) < 2:
                continue
            eligible["completeness"] = eligible.apply(
                lambda row: bool(text(row.skills)) + int(pd.notna(row.experience_years)), axis=1
            )
            eligible = eligible.sort_values(["completeness", "record_id"], ascending=[False, True])
            for i in eligible.index[1:]:
                df.at[i, "review_status"] = "duplicate"
                df.at[i, "review_reasons"] = (
                    "same_identity_and_target_as:" + eligible.iloc[0].record_id
                )
    return df


def group_records(frame, policy):
    df = frame.copy(deep=True).sort_values("record_id").reset_index(drop=True)
    parent = {ident: ident for ident in df.record_id}
    edges = []

    def find(ident):
        while parent[ident] != ident:
            parent[ident] = parent[parent[ident]]
            ident = parent[ident]
        return ident

    def join(left, right, kind, score=1.0):
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)
        edges.append(dict(left=left, right=right, kind=kind, similarity=round(float(score), 6)))

    def group_keys(rows, key_function, kind):
        first = {}
        for row in rows.itertuples():
            key = key_function(row)
            if not key:
                continue
            if key in first:
                join(first[key], row.record_id, kind)
            else:
                first[key] = row.record_id

    group_keys(df, lambda r: text(r.group_id), "exact_source_identity")
    offers = df[df.source_dataset.ne("stackoverflow_2025")]
    group_keys(offers, lambda r: normalized_url(r.source_url), "normalized_url")
    dataforge = offers[offers.source_dataset.eq("dataforge_2026_08")]
    group_keys(
        dataforge,
        lambda r: (
            "|".join(
                identity_text(r.title) if k == "title" else fold(getattr(r, k))
                for k in ["company", "title", "country", "location"]
            )
            if text(r.company)
            else None
        ),
        "company_title_location_group",
    )
    # Restrict expensive similarity review to the small Vietnam offer cohort.
    vn = offers[offers.source_dataset.isin(["vietjobs_2025", "user_vietnam_it_jobs"])].copy()
    if len(vn) > 1:
        titles = vn.title.map(identity_text).tolist()
        bodies = vn.description.map(identity_text).tolist()
        title_vectors = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(
            titles
        )
        title_scores = cosine_similarity(title_vectors)
        long = [
            i for i, value in enumerate(bodies) if len(value) >= policy["minimum_description_chars"]
        ]
        body_scores = {}
        if len(long) > 1:
            matrix = TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5), max_features=30000
            ).fit_transform([bodies[i] for i in long])
            similarities = cosine_similarity(matrix)
            body_scores = {
                (long[i], long[j]): similarities[i, j]
                for i in range(len(long))
                for j in range(i + 1, len(long))
            }
        rows = list(vn.itertuples())
        for i, left in enumerate(rows):
            for j in range(i + 1, len(rows)):
                right = rows[j]
                if left.role != right.role or title_scores[i, j] < 0.6:
                    continue
                loc_left, loc_right = text(left.location), text(right.location)
                if loc_left and loc_right and loc_left != loc_right:
                    continue
                if (
                    text(left.company)
                    and text(right.company)
                    and fold(left.company) != fold(right.company)
                ):
                    continue
                score = body_scores.get((i, j), 0)
                if score >= policy["near_description_similarity"]:
                    join(left.record_id, right.record_id, "near_description_group", score)
                elif left.source_dataset != right.source_dataset:
                    a = set(fold(left.skills).split(";")) - {""}
                    b = set(fold(right.skills).split(";")) - {""}
                    jaccard = len(a & b) / len(a | b) if a | b else 0
                    if (
                        len(a & b) >= 3
                        and jaccard >= policy["near_skills_jaccard"]
                        and title_scores[i, j] >= policy["near_title_similarity"]
                    ):
                        join(
                            left.record_id, right.record_id, "possible_cross_source_group", jaccard
                        )
    df["leakage_group_id"] = df.record_id.map(lambda ident: digest("review-v1:" + find(ident)))
    return df, pd.DataFrame(edges, columns=["left", "right", "kind", "similarity"])


def assign_splits(frame, seed, fractions):
    if len(fractions) != 3 or not math.isclose(sum(fractions), 1) or min(fractions) <= 0:
        raise ValueError("Three positive split fractions must sum to one")
    groups = sorted(frame.leakage_group_id.unique())
    if len(groups) < 3:
        raise ValueError("At least three independent groups are needed")
    shuffled = np.random.default_rng(seed).permutation(groups)
    ntrain = max(1, int(len(groups) * fractions[0]))
    nvalid = max(1, int(len(groups) * fractions[1]))
    if ntrain + nvalid >= len(groups):
        ntrain = len(groups) - nvalid - 1
    assigned = {
        ident: "train" if i < ntrain else "valid" if i < ntrain + nvalid else "test"
        for i, ident in enumerate(shuffled)
    }
    result = frame.copy(deep=True)
    result["split"] = result.leakage_group_id.map(assigned)
    return result.sort_values("record_id").reset_index(drop=True)

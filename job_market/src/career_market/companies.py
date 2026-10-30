"""Conservative company aliases and indivisible audit groups (ML02)."""

import hashlib
import json
import unicodedata
from collections import defaultdict

from .postings import posting_key
from .snapshots import csv_bytes

RULES_VERSION = "company-groups-v1"


def canonical_name(value):
    # NFC keeps canonical Unicode equivalence without removing accents or suffixes.
    return unicodedata.normalize("NFC", " ".join((value or "").split()).casefold())


def stable_id(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def company_report(rows):
    assignments = []
    buckets = defaultdict(list)
    for original in rows:
        row = dict(original)
        canonical = canonical_name(row.get("company_raw"))
        entity = row.get("posting_id") or "unresolved:" + stable_id(
            [
                row.get("source_id"),
                row.get("job_id"),
                row.get("job_url"),
                row.get("raw", {}),
                canonical,
            ]
        )
        company_id = row.get("company_source_id") or (row.get("raw") or {}).get("company_id")
        source_id = row.get("source_id")
        reasons = []
        if not canonical:
            reasons.append("missing_company")
        if not row.get("posting_id"):
            reasons.append("missing_posting_identity")
        if not source_id:
            reasons.append("missing_source_identity")
        reasons.extend("entity_conflict:" + field for field in row.get("entity_conflicts", []))
        row.update(
            company_canonical=canonical,
            entity_id=entity,
            company_source_id=company_id,
            preparation_review_reasons=row.get("review_reasons", []),
            review_reasons=sorted(set(reasons)),
        )
        index = len(assignments)
        assignments.append(row)
        url_key = None
        if row.get("job_url"):
            try:
                url_key = posting_key("shared-url", row["job_url"])
            except ValueError:
                pass
        for kind, value in (
            ("company", canonical),
            ("posting_url", url_key),
            ("posting_id", row.get("posting_id")),
            ("unresolved_evidence", entity if not row.get("posting_id") else None),
            ("repost_group_id", row.get("repost_group_id")),
            (
                "source_posting_id",
                json.dumps([source_id, row["job_id"]]) if source_id and row.get("job_id") else None,
            ),
            (
                "source_company_id",
                json.dumps([source_id, company_id]) if company_id and source_id else None,
            ),
        ):
            if value:
                buckets[kind, value].append(index)
    row_references = defaultdict(list)
    for index, row in enumerate(assignments):
        if row.get("row_id"):
            row_references[row["row_id"]].append(index)
    for index, row in enumerate(assignments):
        reference = row.get("duplicate_of")
        if reference:
            targets = row_references.get(reference, [])
            if not targets:
                row["review_reasons"].append("unresolved_duplicate_link")
            else:
                buckets["duplicate_of", reference].extend([index, *targets])
    company_ids = defaultdict(set)
    for row in assignments:
        if row.get("source_id") and row["company_canonical"] and row["company_source_id"]:
            company_ids[row["source_id"], row["company_canonical"]].add(
                str(row["company_source_id"])
            )
    for row in assignments:
        if len(company_ids[row.get("source_id"), row["company_canonical"]]) > 1:
            row["review_reasons"].append("conflicting_company_source_ids")
    parents = list(range(len(assignments)))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    links = []
    for (kind, value), indices in sorted(buckets.items()):
        indices = sorted(set(indices))
        for index in indices[1:]:
            parents[root(index)] = root(indices[0])
        names = {
            assignments[i]["company_canonical"]
            for i in indices
            if assignments[i]["company_canonical"]
        }
        if (
            kind
            in {
                "posting_id",
                "posting_url",
                "source_posting_id",
                "source_company_id",
                "duplicate_of",
            }
            and len(names) > 1
        ):
            reason = (
                "conflicting_posting_company"
                if kind != "source_company_id"
                else "conflicting_source_company_id"
            )
            for index in indices:
                assignments[index]["review_reasons"].append(reason)
        links.append(
            {
                "kind": kind,
                "value": value,
                "entity_ids": sorted({assignments[i]["entity_id"] for i in indices}),
                "row_count": len(indices),
            }
        )
    components = defaultdict(list)
    for index, row in enumerate(assignments):
        components[root(index)].append(row)
    groups = []
    for members in components.values():
        entities = sorted({row["entity_id"] for row in members})
        companies = sorted(
            {row["company_canonical"] for row in members if row["company_canonical"]}
        )
        group_id = "company-group:" + stable_id(entities)
        reasons = sorted({reason for row in members for reason in row["review_reasons"]})
        status = "review" if reasons else "ready_for_split"
        for row in members:
            row.update(group_id=group_id, status=status, review_reasons=reasons)
        groups.append(
            {
                "group_id": group_id,
                "entity_ids": entities,
                "companies": companies,
                "row_count": len(members),
                "status": status,
                "review_reasons": reasons,
            }
        )
    assignments.sort(key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True))
    groups.sort(key=lambda group: group["group_id"])
    alias_members = defaultdict(list)
    for row in assignments:
        alias_members[
            (
                row.get("source_id"),
                row.get("company_source_id"),
                row.get("company_raw"),
                row["company_canonical"],
                row["group_id"],
            )
        ].append(row)
    aliases = []
    for (source, source_company, raw, canonical, group), members in alias_members.items():
        aliases.append(
            {
                "source_id": source,
                "company_source_id": source_company,
                "company_raw": raw,
                "company_canonical": canonical,
                "group_id": group,
                "status": members[0]["status"],
                "review_reasons": members[0]["review_reasons"],
                "row_count": len(members),
                "posting_ids": sorted({r["posting_id"] for r in members if r.get("posting_id")}),
                "job_ids": sorted({str(r["job_id"]) for r in members if r.get("job_id")}),
                "job_urls": sorted({r["job_url"] for r in members if r.get("job_url")}),
            }
        )
    aliases.sort(key=lambda alias: json.dumps(alias, ensure_ascii=False, sort_keys=True))

    def export(table, default_fields):
        fields = sorted({key for row in table for key in row}) or default_fields
        return csv_bytes(table, fields).decode("utf-8")

    # Count only prepared labeled entities in identity-ready components. This is
    # a structural impossibility check, not a training/support gate or splitter.
    labeled = [
        row
        for row in assignments
        if row["status"] == "ready_for_split"
        and row.get("salary_target_vnd_month") is not None
        and row.get("partition") in {None, "eda", "duplicates"}
    ]

    def labeled_counts(members):
        return {
            "usable_labeled_groups": len({r["group_id"] for r in members}),
            "usable_labeled_companies": len({r["company_canonical"] for r in members}),
            "usable_labeled_entities": len({r["entity_id"] for r in members}),
        }

    cohort_members = defaultdict(list)
    for row in labeled:
        cohort_members[
            row.get("salary_basis", "unknown"), row.get("compensation_scope", "unknown")
        ].append(row)
    cohorts = []
    for (basis, scope), members in cohort_members.items():
        counts = labeled_counts(members)
        cohorts.append(
            {
                "salary_basis": basis,
                "compensation_scope": scope,
                **counts,
                "minimum_group_count_met": counts["usable_labeled_groups"] >= 3,
            }
        )
    cohorts.sort(key=lambda cohort: json.dumps(cohort, sort_keys=True))
    counts = labeled_counts(labeled)
    minimum_met = any(cohort["minimum_group_count_met"] for cohort in cohorts)
    names = sorted({r["company_raw"].strip() for r in labeled})
    name_note = f" ({', '.join(names)})" if counts["usable_labeled_companies"] == 1 else ""
    if not minimum_met:
        reason = (
            f"Có {counts['usable_labeled_entities']} entity có nhãn, "
            f"{counts['usable_labeled_companies']} công ty{name_note}, "
            f"{counts['usable_labeled_groups']} nhóm độc lập dùng được. "
            "Chưa có cohort cùng basis/phạm vi thu nhập với ít nhất 3 nhóm dùng được; "
            "không thể tạo ba tập train/validation/test đều không rỗng mà không cắt nhóm công ty. "
            "Hai nhãn cùng một công ty vẫn chỉ là một nhóm; chưa thể huấn luyện."
        )
    else:
        reason = (
            "Đủ tối thiểu 3 nhóm trong ít nhất một cohort chỉ là điều kiện cấu trúc cần thiết. "
            "Chưa chia train/validation/test hoặc huấn luyện; ML06 vẫn chờ policy hỗ trợ và gate."
        )
    split_readiness = {
        "independent_groups": len(groups),
        "labeled_company_count": counts["usable_labeled_companies"],
        "labeled_split_group_count": counts["usable_labeled_groups"],
        **counts,
        "identity_ready_groups": sum(g["status"] == "ready_for_split" for g in groups),
        "minimum_group_count_met": minimum_met,
        "cohorts": cohorts,
        "training_ready": False,
        "reason": reason,
    }

    return {
        "split_readiness": split_readiness,
        "rules_version": RULES_VERSION,
        "rows": assignments,
        "aliases": aliases,
        "csv": export(
            assignments,
            [
                "source_id",
                "posting_id",
                "company_raw",
                "company_canonical",
                "group_id",
                "status",
                "review_reasons",
            ],
        ),
        "aliases_csv": export(aliases, ["company_raw", "company_canonical", "group_id"]),
        "groups_csv": export(groups, ["group_id", "status", "review_reasons"]),
        "links_csv": export(links, ["kind", "value", "entity_ids", "row_count"]),
        "policy": {
            "split_ratios": [0.70, 0.15, 0.15],
            "seed": 42,
            "company_disjoint": True,
            "split_performed": False,
            "training_performed": False,
            "note": "Identity audit only; ML06 must keep entire ready groups in one partition. Review groups are quarantined. No group may be cut to meet target ratios.",
        },
        "groups": groups,
        "links": links,
        "summary": {
            "rows": len(assignments),
            "entities": len({r["entity_id"] for r in assignments}),
            "companies": len(
                {r["company_canonical"] for r in assignments if r["company_canonical"]}
            ),
            "groups": len(groups),
            "review_groups": sum(g["status"] == "review" for g in groups),
        },
    }

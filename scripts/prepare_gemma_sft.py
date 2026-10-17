"""Build traceable silver job-card extraction JSONL, without starting model training."""

import argparse
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.data_cleaning import fold, numeric, text  # noqa: E402

FIELDS = [
    "role",
    "location",
    "experience_years",
    "skills",
    "salary_min",
    "salary_max",
    "currency",
    "salary_period",
]
SYSTEM = (
    "Đọc phiếu tin tuyển dụng, trả đúng một JSON, không giải thích. "
    "Các khóa: role, location, experience_years, skills, salary_min, salary_max, currency, "
    "salary_period. Chuẩn hóa role về một trong: Software Developer, Backend Developer, "
    "Frontend Developer, Full-stack Developer, Mobile Developer, Embedded Engineer, "
    "ML Engineer, Data Engineer. Chuẩn địa điểm Hà Nội, TP.HCM, Đà Nẵng khi tương đương; "
    "giữ tên khác. Kỹ năng là danh sách tên công nghệ được nêu, chuẩn hóa alias thông dụng. "
    "Không suy số năm từ seniority. Không yêu cầu kinh nghiệm là 0. Thiếu thông tin trả null. "
    "Lương là số tiền hai cận theo tiền tệ/kỳ gốc, không lấy trung điểm, không đổi ngoại tệ. "
    "Không có số tiền lương thì salary_min, salary_max, currency, salary_period đều null. "
    "Kỳ lương: month hoặc year. Đọc đơn vị nguồn được ghi rõ trong phiếu, không đoán."
)


def validate_label(label):
    if set(label) != set(FIELDS):
        raise ValueError("Extraction JSON must contain exactly the eight schema keys")
    for key in ["role", "location", "currency", "salary_period"]:
        if label[key] is not None and not isinstance(label[key], str):
            raise ValueError(f"Invalid string field: {key}")
    for key in ["experience_years", "salary_min", "salary_max"]:
        value = label[key]
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Invalid numeric field: {key}")
    skills = label["skills"]
    if skills is not None and (
        not isinstance(skills, list) or any(not isinstance(x, str) or not x.strip() for x in skills)
    ):
        raise ValueError("skills must be null or a string list")
    if skills is not None and len(skills) != len(set(skills)):
        raise ValueError("Duplicate skill")
    if label["salary_period"] not in {None, "month", "year"}:
        raise ValueError("Unsupported salary period")
    low, high = label["salary_min"], label["salary_max"]
    if low is not None and high is not None and high < low:
        raise ValueError("Reversed salary range")


def make_example(row, variant):
    if variant not in {"original", "omit_salary", "omit_experience"}:
        raise ValueError("Unsupported augmentation")
    title = text(row["title"])
    other_fields = " ".join(text(row.get(k)) for k in ["title", "skills_raw", "location_raw"])
    if variant == "omit_salary" and re.search(
        r"luong|thu nhap|salary|trieu|\busd\b|\bvnd\b|₫|\$|up.?to|\d+\s*(?:tr\b|m\b)",
        fold(other_fields),
    ):
        return None
    if variant == "omit_experience" and re.search(
        r"\bnam\b|\bthang\b|\byears?\b|\bmonths?\b|\byoe\b", fold(other_fields)
    ):
        return None
    label = {
        "role": text(row.get("role")) or None,
        "location": text(row.get("location")) or None,
        "experience_years": numeric(row.get("experience_years")),
        "skills": json.loads(row["skills_json"]),
        "salary_min": numeric(row.get("salary_min")),
        "salary_max": numeric(row.get("salary_max")),
        "currency": text(row.get("currency")) or None,
        "salary_period": text(row.get("salary_period")) or None,
    }
    lines = ["Phiếu tin tuyển dụng từ dữ liệu đã thu thập:", f"Chức danh: {title}"]
    if text(row.get("company")):
        lines.append("Công ty: " + text(row["company"]))
    lines.append("Địa điểm: " + text(row.get("location_raw")))
    if variant != "omit_experience":
        lines.append("Kinh nghiệm: " + text(row.get("experience_raw")))
    else:
        label["experience_years"] = None
    lines.append("Kỹ năng: " + text(row.get("skills_raw")))
    if variant != "omit_salary":
        if row["source_dataset"] == "vietjobs_2025":
            lines.append("Đơn vị lương do nguồn VietJobs công bố: triệu VND/tháng.")
        lines.append("Lương: " + text(row.get("salary_raw")))
    else:
        for key in ["salary_min", "salary_max", "currency", "salary_period"]:
            label[key] = None
    validate_label(label)
    return {
        "source_record_id": row["record_id"],
        "group_id": row["leakage_group_id"],
        "source_dataset": row["source_dataset"],
        "variant": variant,
        "label_quality": "silver_source_fields",
        "task": "job_card_extraction",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "\n".join(lines)},
            {"role": "assistant", "content": json.dumps(label, ensure_ascii=False)},
        ],
    }


def main():
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-tokens", type=int, default=1024)
    args = parser.parse_args()
    output = ROOT / "data/finetune"
    if any(
        (output / f"{s}.jsonl").exists() and (output / f"{s}.jsonl").stat().st_size
        for s in ["train", "valid", "test"]
    ):
        raise SystemExit("JSONL already populated; preserve/version the existing corpus first")
    cohort_path = ROOT / "data/splits/v1.0.1/vn_developer/manifest.json"
    cohort = json.loads(cohort_path.read_text())
    cleaning = json.loads((ROOT / "outputs/data_quality/cleaning/all_sources.json").read_text())
    clean_parts, inputs = [], []
    for source in cleaning["sources"]:
        if source["source"] not in {"user_vietnam_it_jobs", "vietjobs_2025"}:
            continue
        item = source["files"]["clean"]
        path = ROOT / item["path"]
        assert checksum(path) == item["sha256"]
        inputs.append(item)
        clean_parts.append(pd.read_csv(path, low_memory=False))
    clean = pd.concat(clean_parts, ignore_index=True).set_index("record_id", drop=False)
    tokenizer = AutoTokenizer.from_pretrained(ROOT / "models/gemma-mlx-4bit", local_files_only=True)
    candidates, excluded = [], []
    for split in ["train", "valid", "test"]:
        item = cohort["files"][split]
        assert checksum(ROOT / item["path"]) == item["sha256"]
        inputs.append(item)
        ids = pd.read_csv(ROOT / item["path"])
        for record in ids.to_dict("records"):
            row = clean.loc[record["record_id"]].to_dict()
            row["leakage_group_id"] = record["leakage_group_id"]
            for variant in ["original", "omit_salary", "omit_experience"]:
                example = make_example(row, variant)
                if example is None:
                    excluded.append(
                        {
                            "record_id": row["record_id"],
                            "split": split,
                            "variant": variant,
                            "reason": "field_evidence_elsewhere",
                        }
                    )
                    continue
                messages = example["messages"]
                tokens = tokenizer.apply_chat_template(messages, return_dict=False)
                prompt_tokens = tokenizer.apply_chat_template(
                    messages[:-1], add_generation_prompt=True, return_dict=False
                )
                assert tokens[: len(prompt_tokens)] == prompt_tokens, "Prompt masking mismatch"
                if not 0 < len(prompt_tokens) < len(tokens) <= args.max_tokens:
                    excluded.append(
                        {
                            "record_id": row["record_id"],
                            "split": split,
                            "variant": variant,
                            "reason": "length_limit_no_truncation",
                        }
                    )
                    continue
                example["tokens"] = len(tokens)
                example["prompt_tokens"] = len(prompt_tokens)
                example["split"] = split
                candidates.append(example)
    # All prompt variants inherit their source split. Quarantine a coincident cross-split prompt.
    prompt_splits = {}
    for row in candidates:
        prompt_splits.setdefault(row["messages"][1]["content"], set()).add(row["split"])
    seen, kept = set(), []
    for row in candidates:
        prompt = row["messages"][1]["content"]
        key = (row["split"], prompt, row["messages"][-1]["content"])
        reason = (
            "prompt_collision_across_splits"
            if len(prompt_splits[prompt]) > 1
            else ("duplicate_prompt_and_target" if key in seen else None)
        )
        if reason:
            excluded.append(
                {
                    "record_id": row["source_record_id"],
                    "split": row["split"],
                    "variant": row["variant"],
                    "reason": reason,
                }
            )
        else:
            kept.append(row)
            seen.add(key)
    stats = {}
    output.mkdir(parents=True, exist_ok=True)
    for split in ["train", "valid", "test"]:
        rows = [row for row in kept if row["split"] == split]
        if not rows:
            raise ValueError("Empty split")
        path = output / f"{split}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        stats[split] = {
            "examples": len(rows),
            "source_records": len({r["source_record_id"] for r in rows}),
            "groups": len({r["group_id"] for r in rows}),
            "max_tokens": max(r["tokens"] for r in rows),
            "sha256": checksum(path),
            "original_examples": sum(r["variant"] == "original" for r in rows),
        }
    for left, right in [("train", "valid"), ("train", "test"), ("valid", "test")]:
        assert {r["group_id"] for r in kept if r["split"] == left}.isdisjoint(
            r["group_id"] for r in kept if r["split"] == right
        )
    ledger = pd.DataFrame(
        [
            {
                "record_id": r["source_record_id"],
                "group_id": r["group_id"],
                "split": r["split"],
                "variant": r["variant"],
                "tokens": r["tokens"],
                "quality": r["label_quality"],
            }
            for r in kept
        ]
    )
    prep = ROOT / "outputs/gemma_preparation"
    prep.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(prep / "sft_ledger.csv", index=False)
    pd.DataFrame(excluded).to_csv(prep / "sft_excluded.csv", index=False)
    manifest = {
        "version": "1.0.0",
        "task": "job_card_extraction",
        "quality": "silver_source_fields",
        "source_salary_snapshot": "vn_developer/v1.0.1",
        "splits": stats,
        "max_seq_length": args.max_tokens,
        "inputs": inputs,
        "builder_sha256": checksum(Path(__file__)),
        "tokenizer_sha256": checksum(ROOT / "models/gemma-mlx-4bit/tokenizer.json"),
        "system_prompt": SYSTEM,
        "augments": "Omit salary or experience only when no remaining text contains field evidence",
        "excluded_examples": len(excluded),
        "training_started": False,
        "limits": [
            "Real source job cards, not complete original free-text ads",
            "Derived silver labels, not independent human gold labels",
            "Missing-field variants are augmentations, not additional independent jobs",
            "Not career-advice training data",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

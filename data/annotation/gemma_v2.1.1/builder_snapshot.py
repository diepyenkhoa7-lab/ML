"""Versioned source-grounded label corrections; never reads the sealed test."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.data_cleaning import fold  # noqa: E402
from scripts.review_gemma_labels import CANONICAL, explicit_experience  # noqa: E402

SOURCE = ROOT / "data/finetune_reviewed/v2.0.0"
OUTPUT = ROOT / "data/annotation/gemma_v2.1.1"
ADDITIONS = {
    name.casefold(): name
    for name in [
        "BERT",
        "T5",
        "Mistral",
        "LLaMA",
        "GPT",
        "Deep Learning",
        "LangChain",
        "LlamaIndex",
        "TensorRT",
        "ONNX",
        "OpenVINO",
        "Qt",
        "Blazor",
        "Liquid",
        "Yii2",
        "Android SDK",
        "Jetpack",
        "Razor Pages",
        "ASP.NET Web API",
        "Claude",
        "Gemini",
        "Copilot",
        "Sequelize",
        "Vite",
        "TanStack Query",
        "Ant Design",
        "RBAC",
    ]
}
ADDITIONS.update({"restapi": "REST API", "restfulapi": "REST API"})
NUMBER_WORDS = {
    "mot": "1",
    "hai": "2",
    "ba": "3",
    "bon": "4",
    "nam": "5",
    "sau": "6",
    "bay": "7",
    "tam": "8",
    "chin": "9",
    "muoi": "10",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}


def experience_with_words(content):
    """Only normalize number words immediately before a year/month unit."""
    normalized = fold(content)
    pattern = r"\b(" + "|".join(NUMBER_WORDS) + r")\s+(?=nam\b|thang\b|years?\b|months?\b)"
    normalized = re.sub(pattern, lambda m: NUMBER_WORDS[m[1]] + " ", normalized)
    # Source descriptions often concatenate text and use "4–6+ năm kinh nghiệm".
    # Drop only a numeric lower-bound '+' immediately before its time unit.
    normalized = re.sub(r"(?<=\d)\+\s*(?=nam\b|thang\b|years?\b|months?\b)", " ", normalized)
    return explicit_experience(normalized)


def literal_skills(content):
    """Closed alias inventory, literal evidence, longest span wins."""
    matches = []
    for alias, canonical in (CANONICAL | ADDITIONS).items():
        flags = 0 if alias in {"c", "r", "go"} else re.I
        literal = {"c": "C", "r": "R", "go": "Go"}.get(alias, alias)
        pattern = r"(?<![\w])" + re.escape(literal) + r"(?![\w+#&])"
        for match in re.finditer(pattern, content, flags):
            matches.append((match.start(), match.end(), canonical, match.group()))
    occupied, evidence = set(), {}
    for start, end, canonical, span in sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0])):
        positions = set(range(start, end))
        if not positions & occupied:
            evidence.setdefault(canonical, span)
            occupied.update(positions)
    return sorted(evidence, key=str.casefold), evidence


def proposed_correction(row):
    original = json.loads(row["messages"][-1]["content"])
    card = next(m["content"] for m in row["messages"] if m["role"] == "user")
    # Salary, address, company names cannot provide technology/experience evidence.
    title = re.search(r"^Chức danh: (.*)$", card, re.M)
    requirements = card.partition("Yêu cầu trích nguyên văn: ")[2]
    visible = (title[1] if title else "") + "\n" + requirements
    skills, skill_evidence = literal_skills(visible)
    experience, experience_evidence = experience_with_words(visible)
    correction = {}
    if skills != original["skills"]:
        correction["skills"] = dict(
            before=original["skills"], after=skills, evidence=skill_evidence
        )
    if experience != original["experience_years"]:
        correction["experience_years"] = dict(
            before=original["experience_years"],
            after=experience,
            evidence=experience_evidence,
        )
    return dict(
        source_record_id=row["source_record_id"],
        split=row["split"],
        input_sha256=hashlib.sha256(card.encode()).hexdigest(),
        quality="AI-assisted correction proposal; not human gold",
        status="pending_adjudication",
        changes=correction,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve the existing correction audit; use a new version")
    corrections = []
    counts = {}
    hashes = {}
    for split in ["train", "valid"]:
        source = SOURCE / f"{split}.jsonl"
        hashes[split] = checksum(source)
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        rows = [row for row in rows if row.get("source_dataset") == "tinixai_reviewed"]
        counts[split] = len(rows)
        corrections.extend(proposed_correction(row) for row in rows)
    args.output.mkdir(parents=True)
    (args.output / "builder_snapshot.py").write_bytes(Path(__file__).read_bytes())
    path = args.output / "correction_proposals.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in corrections))
    manifest = dict(
        status="proposals_only_not_a_training_corpus",
        source="data/finetune_reviewed/v2.0.0",
        sources_scanned=counts,
        changed_records={
            split: sum(bool(row["changes"]) for row in corrections if row["split"] == split)
            for split in counts
        },
        source_hashes=hashes,
        audit_sha256=checksum(path),
        builder_sha256=checksum(Path(__file__)),
        test_read=False,
        training_started=False,
        limitations=[
            "Closed vocabulary remains incomplete; proposals require adjudication",
            "Existing manually adjudicated experience may override a generic parser",
            "Do not report rescored corrected references as model improvement",
            "Do not copy validation rows into training",
        ],
    )
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

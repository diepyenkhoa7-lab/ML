"""Freeze a corrected silver corpus under one text policy before the next trial."""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.prepare_gemma_sft import validate_label  # noqa: E402
from scripts.refine_gemma_references import experience_with_words, literal_skills  # noqa: E402
from scripts.validate_sft import validate_corpus  # noqa: E402

SOURCE = ROOT / "data/finetune_reviewed/v2.0.0"
DESTINATION = ROOT / "data/finetune_reviewed/v2.2.0"


def corrected_label(row):
    """Same policy in all splits; no predictions, metadata or split-specific targets."""
    import re

    label = json.loads(row["messages"][-1]["content"])
    card = next(m["content"] for m in row["messages"] if m["role"] == "user")
    title = re.search(r"^Chức danh: (.*)$", card, re.M)
    visible = (title[1] if title else "") + "\n" + card.partition("Yêu cầu trích nguyên văn: ")[2]
    label["skills"], evidence = literal_skills(
        visible, aliases={"ant design mobile": "Ant Design Mobile"}
    )
    label["experience_years"], experience = experience_with_words(visible)
    # Preserve the source-reviewed distinction between total and component experience.
    if row["source_record_id"] == "tinixai:4622":
        assert "Tối thiểu 2 năm kinh nghiệm" in visible
        label["experience_years"] = 2.0
    validate_label(label)
    return label, dict(skills=evidence, experience=experience)


def main():
    from transformers import AutoTokenizer

    if DESTINATION.exists():
        raise ValueError("Preserve corrected corpus; choose another version")
    tokenizer = AutoTokenizer.from_pretrained(ROOT / "models/gemma-mlx-4bit", local_files_only=True)
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    result = copy.deepcopy(manifest)
    result.update(
        version="2.2.0",
        builder_sha256=checksum(Path(__file__)),
        parent_corpus_manifest_sha256=checksum(SOURCE / "manifest.json"),
        correction_policy_sha256=checksum(ROOT / "scripts/refine_gemma_references.py"),
        corrections_adjudicated_sha256=checksum(
            ROOT / "data/annotation/gemma_v2.1.1/adjudicated_changes.jsonl"
        ),
        test_reference_policy=(
            "Blind deterministic label rebuild with policy fixed from train/validation; "
            "no test predictions, test-driven alias additions or training decisions. "
            "AI silver, not independent human gold."
        ),
        prompts_and_company_assignments_unchanged=True,
    )
    DESTINATION.mkdir(parents=True)
    decisions = []
    for split in ["train", "valid", "test"]:
        path = SOURCE / f"{split}.jsonl"
        assert checksum(path) == manifest["splits"][split]["sha256"]
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        changed = 0
        for row in rows:
            if row["source_dataset"] != "tinixai_reviewed":
                continue
            original = json.loads(row["messages"][-1]["content"])
            label, evidence = corrected_label(row)
            changes = {
                k: dict(before=original[k], after=v) for k, v in label.items() if v != original[k]
            }
            changed += bool(changes)
            row["messages"][-1]["content"] = json.dumps(label, ensure_ascii=False)
            row["tokens"] = len(tokenizer.apply_chat_template(row["messages"], return_dict=False))
            assert row["tokens"] <= 1024
            assert row["tokens"] - row["prompt_tokens"] <= 256
            decisions.append(
                dict(
                    source_record_id=row["source_record_id"],
                    split=split,
                    quality="AI-reviewed silver, not human gold",
                    changes=changes,
                    evidence=evidence,
                )
            )
        destination = DESTINATION / path.name
        destination.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
        result["splits"][split].update(
            sha256=checksum(destination),
            max_tokens=max(row["tokens"] for row in rows),
            corrected_records=changed,
        )
    decisions_path = DESTINATION / "label_decisions.jsonl"
    decisions_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in decisions)
    )
    result["label_decisions_sha256"] = checksum(decisions_path)
    (DESTINATION / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    validation = validate_corpus(DESTINATION, strict=True)
    assert validation["ok"], validation["errors"]
    print(
        json.dumps(
            dict(
                version="2.2.0",
                validation=validation,
                splits=result["splits"],
                training_started=False,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

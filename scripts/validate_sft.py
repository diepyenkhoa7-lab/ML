"""Validate chat JSONL, source/group leakage, conflicting prompts and extraction schema."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.prepare_gemma_sft import validate_label  # noqa: E402


def validate_corpus(data, strict=False):
    registries = {key: {} for key in ("source_record_id", "group_id", "prompt")}
    targets, counts, errors = {}, {}, []
    manifest = None
    if strict:
        try:
            manifest = json.loads((data / "manifest.json").read_text())
        except (OSError, ValueError) as exc:
            errors.append(f"Manifest: {exc}")
    for split in ("train", "valid", "test"):
        path = data / f"{split}.jsonl"
        counts[split] = 0
        if not path.exists():
            errors.append(f"Missing {path}")
            continue
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path}:{line_no}"
            try:
                row = json.loads(line)
                assert isinstance(row["source_record_id"], str) and row["source_record_id"].strip()
                messages = row["messages"]
                assert isinstance(messages, list) and len(messages) >= 2
                assert messages[-1]["role"] == "assistant"
                assert any(m["role"] == "user" for m in messages)
                for message in messages:
                    assert message["role"] in {"system", "user", "assistant"}
                    assert isinstance(message["content"], str) and message["content"].strip()
                prompt = " ".join(
                    " ".join(m["content"].casefold().split())
                    for m in messages
                    if m["role"] == "user"
                )
                values = {"source_record_id": row["source_record_id"], "prompt": prompt}
                if "group_id" in row:
                    assert isinstance(row["group_id"], str) and row["group_id"].strip()
                    values["group_id"] = row["group_id"]
                if strict:
                    assert row["split"] == split and "group_id" in row
                    validate_label(json.loads(messages[-1]["content"]))
                    assert 0 < row["prompt_tokens"] < row["tokens"] <= manifest["max_seq_length"]
                for kind, value in values.items():
                    registry = registries[kind]
                    if value in registry and registry[value] != split:
                        errors.append(f"{where}: {kind} overlaps {registry[value]}")
                    registry[value] = split
                target = messages[-1]["content"]
                if prompt in targets and targets[prompt] != target:
                    errors.append(f"{where}: conflicting targets for the same prompt")
                targets[prompt] = target
                counts[split] += 1
            except (ValueError, KeyError, TypeError, AssertionError, IndexError) as exc:
                errors.append(f"{where}: {exc}")
        if not counts[split]:
            errors.append(f"{path}: empty or invalid corpus")
        if manifest:
            item = manifest["splits"][split]
            if counts[split] != item["examples"] or checksum(path) != item["sha256"]:
                errors.append(f"{path}: manifest count/checksum mismatch")
    return {"counts": counts, "ok": not errors, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/finetune"))
    parser.add_argument("--strict-extraction", action="store_true")
    args = parser.parse_args()
    result = validate_corpus(args.data, args.strict_extraction)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

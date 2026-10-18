"""Save explicit AI source-review decisions; diagnose cached validation predictions only."""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.evaluate_gemma import score  # noqa: E402

DIRECTORY = ROOT / "data/annotation/gemma_v2.1.1"
ACCEPTED = {
    "tinixai:17749",
    "tinixai:277770",
    "tinixai:32057",
    "tinixai:35981",
    "tinixai:370761",
    "tinixai:38690",
    "tinixai:8639",
    "tinixai:16925",
    "tinixai:198658",
    "tinixai:327913",
    "tinixai:335784",
    "tinixai:449770",
    "tinixai:466600",
    "tinixai:50869",
    "tinixai:555834",
    "tinixai:604610",
    "tinixai:605424",
}


def adjudicate(proposal):
    row = copy.deepcopy(proposal)
    row.update(reviewer="Codex AI source-text adjudication", human_gold=False)
    if row["source_record_id"] == "tinixai:4622":
        row["status"] = "rejected_correction_keep_existing"
        row["reason"] = (
            "Original visible requirements explicitly require 2 years overall production, "
            "including 1 year LLM and 1 year Computer Vision; retain overall experience 2."
        )
    else:
        assert row["source_record_id"] in ACCEPTED
        row["status"] = "accepted_ai_review_not_human_gold"
        row["reason"] = (
            "Checked visible source text: explicit technology name "
            "or numeric/word-number experience."
        )
        if row["source_record_id"] == "tinixai:277770":
            change = row["changes"]["skills"]
            change["after"].remove("Ant Design")
            change["after"].append("Ant Design Mobile")
            change["after"].sort(key=str.casefold)
            change["evidence"].pop("Ant Design")
            change["evidence"]["Ant Design Mobile"] = "Ant Design Mobile"
            row["reason"] += " Keep specific framework Ant Design Mobile, not its parent."
    return row


def main():
    decisions_path = DIRECTORY / "adjudicated_changes.jsonl"
    report_path = DIRECTORY / "cached_validation_diagnostic.json"
    if decisions_path.exists() or report_path.exists():
        raise ValueError("Preserve completed review evidence")
    proposals = DIRECTORY / "correction_proposals.jsonl"
    rows = [json.loads(line) for line in proposals.read_text().splitlines()]
    decisions = [adjudicate(row) for row in rows if row["changes"]]
    assert len(decisions) == 18 and len(ACCEPTED) == 17
    decisions_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in decisions)
    )
    valid_path = ROOT / "data/finetune_reviewed/v2.0.0/valid.jsonl"
    valid = [json.loads(line) for line in valid_path.read_text().splitlines()]
    by_id = {row["source_record_id"]: row for row in decisions if row["split"] == "valid"}
    for row in valid:
        decision = by_id.get(row["source_record_id"])
        if not decision or not decision["status"].startswith("accepted"):
            continue
        label = json.loads(row["messages"][-1]["content"])
        for field, change in decision["changes"].items():
            assert label[field] == change["before"]
            label[field] = change["after"]
        row["messages"][-1]["content"] = json.dumps(label, ensure_ascii=False)
    diagnostic = dict(
        status="label_sensitivity_diagnostic_only_not_promotion",
        decisions_sha256=checksum(decisions_path),
        source_validation_sha256=checksum(valid_path),
        accepted_train=7,
        accepted_validation=10,
        rejected_corrections=1,
        old_references_unchanged=True,
        test_examples_read=False,
        training_started=False,
        warning=(
            "Changed reference labels, unchanged raw predictions/weights. "
            "Metric changes are NOT model improvements. "
            "Legacy regression still fails; retain serving adapter."
        ),
        results={},
    )
    for name in ["baseline_new_valid", "candidate_new_valid"]:
        path = ROOT / "outputs/metrics/gemma_reviewed_v2" / name / "predictions.jsonl"
        predictions = [json.loads(line) for line in path.read_text().splitlines()]
        diagnostic["results"][name] = dict(
            predictions_sha256=checksum(path), corrected_reference_metrics=score(valid, predictions)
        )
    report_path.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(diagnostic, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

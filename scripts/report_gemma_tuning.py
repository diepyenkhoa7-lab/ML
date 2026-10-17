"""Join validation selection and one final test evaluation; never select using test."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.select_gemma_adapter import diagnostics, load_evaluation, quality  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-evaluation", type=Path, required=True)
    args = parser.parse_args()
    folder = ROOT / "outputs/metrics/gemma_tuning"
    selection_path = folder / "selection.json"
    selection = json.loads(selection_path.read_text())
    if not selection["stop_reason"]:
        raise ValueError("Finish validation selection before final test report")
    valid, _, _ = load_evaluation(ROOT / selection["selected_evaluation"])
    test, rows, predictions = load_evaluation(ROOT / args.test_evaluation, "test")
    for key in ["adapter", "adapter_sha256", "model_manifest_sha256", "generation"]:
        if valid[key] != test[key]:
            raise ValueError(f"Test configuration differs from selected adapter: {key}")
    detail = diagnostics(rows, predictions)
    (ROOT / args.test_evaluation / "error_analysis.json").write_text(
        json.dumps(detail, ensure_ascii=False, indent=2) + "\n"
    )
    result = dict(
        adapter=selection["selected_adapter"],
        adapter_sha256=valid["adapter_sha256"],
        selection_sha256=checksum(selection_path),
        protocol_sha256=selection["protocol_sha256"],
        selected_using="valid_only",
        stop_reason=selection["stop_reason"],
        validation_targets_met=selection["targets_met"],
        validation=dict(valid, **quality(valid)),
        test=dict(test, **{k: v for k, v in quality(test).items() if k != "selection_score"}),
        test_evaluation=str(args.test_evaluation),
        test_used_for_tuning=False,
        primary_scores="Raw JSON; no repairs, alias normalization or duplicate removal",
        limits=(
            "Silver labels and dependent variants; not arbitrary full ads, advice "
            "or salary regression accuracy"
        ),
    )
    (folder / "recommendation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    import os

    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    records = selection["records"]
    for key, label in [
        ("mean_field_exact_accuracy", "Mean field exact accuracy"),
        ("skill_micro_f1", "Skill micro F1"),
        ("schema_validity", "Schema validity"),
    ]:
        ax.plot(range(len(records)), [record[key] for record in records], marker="o", label=label)
    ax.set_xticks(
        range(len(records)), ["Full baseline"] + [f"Candidate {i}" for i in range(1, len(records))]
    )
    ax.set_ylim(0.8, 1.01)
    ax.set_ylabel("Raw validation score (axis zoomed to 0.8–1.0)")
    ax.set_title("Gemma validation progression · 72 variants / 25 source jobs")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(folder / "validation_progress.png", dpi=160)
    plt.close(fig)
    lines = [
        "# Gemma — kết quả cuối sau cải tiến",
        "",
        f"Adapter được chọn bằng validation: `{result['adapter']}`.",
        f"Dừng: {selection['stop_reason']}. Đạt toàn bộ mục tiêu: {selection['targets_met']}.",
        "",
        "| Metric thô | Validation (72 mẫu / 25 tin) | Test (82 mẫu / 28 tin) |",
        "|---|---:|---:|",
    ]
    for label, key in [
        ("JSON hợp lệ", "json_validity"),
        ("Schema hợp lệ", "schema_validity"),
        ("Accuracy trung bình 8 trường", "mean_field_exact_accuracy"),
        ("Skill micro F1", "skill_micro_f1"),
    ]:
        lines.append(f"| {label} | {result['validation'][key]:.2%} | {result['test'][key]:.2%} |")
    lines += ["", "| Accuracy từng trường | Validation | Test |", "|---|---:|---:|"]
    for field, value in valid["field_exact_accuracy"].items():
        lines.append(f"| {field} | {value:.2%} | {test['field_exact_accuracy'][field]:.2%} |")
    lines += [
        "",
        "![Validation progression](validation_progress.png)",
        "",
        "Test chỉ chấm cho adapter đã chọn; không đổi model hoặc train tiếp theo lỗi test.",
        "Điểm chọn tổng hợp chỉ dùng validation, không dùng điểm tổng hợp test để xếp hạng.",
        "Đây là nhãn silver; biến thể không phải tin độc lập. Kết quả phản ánh trích xuất",
        "phiếu tin theo schema, không phải MAE dự đoán lương của Ridge/Random Forest.",
        "Không cam kết điểm đẹp trên dữ liệu mới hoặc sai số cực tiểu toàn cục.",
        "",
        "Lỗi cụ thể, slice theo biến thể và MAE số cùng đơn vị: error_analysis.json",
        "trong thư mục evaluation tương ứng. Dự đoán thô và checksum đều được giữ.",
        "Muốn cải thiện sau đợt này: thêm tin độc lập, duyệt nhãn gold và chuẩn bị",
        "holdout mới trước khi mở vòng nghiên cứu tiếp theo; không dùng test đã mở làm validation.",
        "",
        "Suy luận (không train):",
        "",
        "```bash",
        f"GEMMA_ADAPTER={result['adapter']} make gemma-infer-adapter",
        "```",
    ]
    (folder / "FINAL_REPORT.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k not in {"validation", "test"}}, indent=2)
    )


if __name__ == "__main__":
    main()

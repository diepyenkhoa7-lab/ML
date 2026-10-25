"""Generate a factual handoff report after final tests and demo have finished."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .state import FOLDER, ROOT, read, write


def report():
    import pandas as pd

    state = read(FOLDER / "state.json")
    if not state.get("test_authorized") or state.get("final_step", 0) < 6:
        raise ValueError("Final model, test, demo and notebook checks are not finished")
    selected = ROOT / state["selected_run"]
    if not read(selected / "fresh_process_reload.json").get("passed"):
        raise ValueError("Selected model fresh-process reload has not passed")
    policy = read(ROOT / "configs/auto_goal.json")
    baseline = ROOT / policy["baseline_run"]
    acceptance = read(FOLDER / "demo/acceptance.json")
    if not acceptance.get("passed"):
        raise ValueError("Demo acceptance is missing")
    if not acceptance.get("text_extraction", {}).get("passed"):
        raise ValueError("Text extraction-to-salary demo has not passed")
    notebooks = sorted((ROOT / "notebooks").glob("*.ipynb"))
    if len(notebooks) != 5:
        raise ValueError("Exactly five completed notebooks are required")
    for path in notebooks:
        cells = [c for c in read(path)["cells"] if c["cell_type"] == "code"]
        if not cells or any(
            c.get("execution_count") is None
            or any(o.get("output_type") == "error" for o in c.get("outputs", []))
            for c in cells
        ):
            raise ValueError(f"Notebook not fully executed: {path.name}")
    numeric = read(selected / "llm_test_metrics.json")
    reference = read(baseline / "baseline_test_metrics.json")
    language = read(selected / "language_test.json")
    frame = pd.read_csv(selected / "llm_test_predictions.csv")
    frame["absolute_error"] = (frame.prediction - frame.salary).abs()
    errors = frame.sort_values("absolute_error", ascending=False).groupby("market").head(10)
    errors.to_csv(FOLDER / "largest_errors.csv", index=False)
    rows = []
    for market, values in numeric["by_market"].items():
        base = reference["by_market"][market]
        if values["unit"] != base["unit"] or values["samples"] != base["samples"]:
            raise ValueError("Final comparison has incompatible samples or units")
        rows.append(
            dict(
                market=market,
                unit=values["unit"],
                samples=values["samples"],
                llm=values,
                baseline=base,
                llm_lower_mae=values["mae"] < base["mae"],
            )
        )
    summary = dict(
        captured_at=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(),
        selected_run=state["selected_run"],
        selection_score=state["best_score"],
        additional_experiments_used=state["additional_experiments_used"],
        markets=rows,
        language=language,
        demo=acceptance,
        test_previously_opened=policy["test_previously_opened"],
    )
    from career_ai.data import digest

    paths = [
        selected / name
        for name in [
            "qwen.lora.h5",
            "salary_head.keras",
            "llm.json",
            "lineage.json",
            "fresh_process_reload.json",
            "llm_history.json",
            "llm_valid_metrics.json",
            "llm_test_metrics.json",
            "language_valid.json",
            "language_test.json",
        ]
    ] + [
        ROOT / "data/tensorflow_v1/manifest.json",
        ROOT / "configs/qwen_source.json",
        ROOT / "configs/auto_goal.json",
        ROOT / "requirements-lock-tf-macos-arm64.txt",
        FOLDER / "demo/acceptance.json",
        *notebooks,
    ]
    summary["artifacts"] = {
        str(path.relative_to(ROOT)): dict(bytes=path.stat().st_size, sha256=digest(path))
        for path in paths
    }
    write(FOLDER / "handoff.json", summary)
    lines = [
        "# Kết quả goal TensorFlow",
        "",
        f"Model được chọn: `{state['selected_run']}`.",
        "Chọn bằng validation; không dùng kết quả test để thay cấu hình.",
        "",
        "| Thị trường | Đơn vị | n | MAE baseline | MAE LLM | RMSE LLM | R² LLM |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        v = row["llm"]
        lines.append(
            f"| {row['market']} | {row['unit']} | {row['samples']} | "
            f"{row['baseline']['mae']:.2f} | {v['mae']:.2f} | {v['rmse']:.2f} | {v['r2']} |"
        )
    lines += [
        "",
        f"JSON schema rate: {language['json_schema_rate']}; Skill F1: {language['skill_f1']}.",
        "Nhãn ngôn ngữ là silver, chưa phải human gold; "
        "xem độ khớp từng trường trong handoff.json.",
        "",
        "## Phân tích lỗi và giới hạn",
        "",
        "Các nhóm sai số theo vai trò/kinh nghiệm nằm trong metric JSON; "
        "10 dòng có sai số tuyệt đối lớn nhất mỗi thị trường ở largest_errors.csv.",
    ]
    for market in numeric["by_market"]:
        groups = [
            (k, v)
            for k, v in numeric["by_role"].items()
            if k.startswith(market + " | ") and v["samples"] >= 10
        ]
        if groups:
            key, value = max(groups, key=lambda item: item[1]["mae"])
            lines.append(
                f"- Nhóm vai trò MAE cao nhất với ít nhất10 mẫu: {key}, "
                f"MAE {value['mae']:.2f}, n={value['samples']}."
            )
    lines += [
        "",
        "Đây là mô tả lỗi, không chứng minh nguyên nhân. "
        "Khác biệt khu vực, thành phần thu nhập và độ nhiễu nhãn "
        "là giả thuyết cần nghiên cứu riêng.",
        "Dữ liệu Việt Nam ít và là lương chào tuyển; khảo sát quốc tế là tổng thu nhập USD/năm. "
        "Không gộp hai đơn vị, không bảo đảm tăng lương khi học kỹ năng.",
        "Nguồn từng được nghiên cứu và baseline test đã mở trước; "
        "không gọi là benchmark độc lập mới.",
        "Không công bố LLM tốt hơn baseline nếu metric thực tế không cho thấy điều đó.",
    ]
    target = ROOT / "docs/AUTONOMOUS_RESULTS.md"
    target.write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    report()

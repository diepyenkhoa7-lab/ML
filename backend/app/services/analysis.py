"""Upload-to-export engine. Uses existing fitted models; never trains."""

import csv
import hashlib
import json
import math
import platform
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.app.services.charts import build_charts
from backend.app.services.data import ROOT, normalize_row, text
from backend.app.services.gemma import extract_cards
from backend.app.services.salary import salary_service


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def spreadsheet_safe(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def export_results(rows, folder, report):
    flat = []
    for row in rows:
        item = {k: v for k, v in row.items() if k not in {"input", "extraction"}}
        item.update({"input_" + k: v for k, v in row["input"].items()})
        if row.get("extraction"):
            item["gemma_extraction"] = json.dumps(row["extraction"], ensure_ascii=False)
        item = {
            k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            for k, v in item.items()
        }
        flat.append(item)
    frame = pd.DataFrame(flat)
    frame = frame.map(spreadsheet_safe)
    frame.to_csv(
        folder / "results.csv",
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    frame.to_excel(folder / "results.xlsx", index=False, engine="openpyxl")
    write_json(folder / "results.json", rows)
    lines = [
        "# Kết quả phân tích bảng dữ liệu",
        "",
        f"Nguồn: {report['filename']}",
        f"Model: {report['model']['experiment_id']}; "
        f"selected={report['model']['selected_model']}; unit=VND/month.",
        f"Dòng nhập: {report['summary']['rows']}; "
        f"thành công: {report['summary']['predicted']}; lỗi: {report['summary']['invalid']}.",
        "",
        "Độ khớp trên bảng nhập, không phải holdout độc lập:",
        json.dumps(report["metrics"], ensure_ascii=False, indent=2),
        "",
        "Lương VND/năm được chia 12; nhãn là trung điểm khoảng nếu đủ hai cận.",
        "Không đổi ngoại tệ tự động. Lương trích bằng Gemma không dùng làm nhãn đánh giá.",
        "Dòng trùng hoàn toàn vẫn có kết quả nhưng loại khỏi biểu đồ/metric.",
        "Không có ngày đăng hợp lệ thì không tạo xu hướng theo thời gian.",
        "Nhãn nguồn silver, gross/net có thể chưa rõ; gợi ý kỹ năng không phải tác động nhân quả.",
        "",
    ]
    (folder / "report.md").write_text("\n".join(lines))
    files = ["results.csv", "results.xlsx", "results.json", "report.md"] + [
        c["file"] for c in report["charts"]
    ]
    if (folder / "gemma_outputs.json").exists():
        files.append("gemma_outputs.json")
    provenance = dict(
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        filename=report["filename"],
        input_sha256=report["input_sha256"],
        dataset_provenance=report["provenance"],
        request=report["request"],
        dataset_snapshot_sha256=report["dataset_snapshot_sha256"],
        salary_manifest_sha256=report["salary_provenance"]["salary_manifest_sha256"],
        salary_provenance=report["salary_provenance"],
        gemma_execution=report["gemma_execution"],
        adapter=report["gemma_execution"].get("provenance", {}).get("adapter"),
        adapter_sha256=report["gemma_execution"].get("provenance", {}).get("adapter_sha256"),
        predictions_do_not_train=True,
        application_source_sha256={
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [
                *sorted((ROOT / "backend/app").rglob("*.py")),
                ROOT / "scripts/app_gemma_extract.py",
            ]
        },
        environment={
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        files={name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in files},
    )
    write_json(folder / "manifest.json", provenance)
    files += ["manifest.json"]
    with zipfile.ZipFile(folder / "analysis.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(folder / name, name)
    return files + ["analysis.zip"]


def analyze(dataset, options, folder: Path, progress):
    model = salary_service()
    mapping = options.mapping
    if set(mapping.values()) - set(dataset["columns"]):
        raise ValueError("Cột được ghép không tồn tại trong file")
    if not any(k in mapping for k in ["role", "title", "description"]):
        raise ValueError("Cần ghép vai trò, chức danh hoặc mô tả tuyển dụng")
    raw_rows = dataset["rows"]
    extracted = {}
    gemma_execution = dict(requested=options.use_gemma, used=False, rows=0)
    progress("Chuẩn hóa dữ liệu", 10)
    if options.use_gemma and "description" in mapping:
        indices = [i for i, raw in enumerate(raw_rows) if text(raw.get(mapping["description"]))]
        if indices:
            cards = []
            for i in indices:
                raw = raw_rows[i]
                pieces = [f"{key}: {text(raw.get(column))}" for key, column in mapping.items()]
                cards.append("Phiếu tin tuyển dụng từ dữ liệu đã thu thập:\n" + "\n".join(pieces))
            progress(f"Gemma đang đọc {len(cards)} mô tả", 15)
            batch = extract_cards(cards, audit_folder=folder)
            extracted = dict(zip(indices, batch["items"], strict=True))
            gemma_execution = dict(
                requested=True,
                used=True,
                rows=len(cards),
                request_id=batch["request_id"],
                succeeded=sum(item["value"] is not None for item in batch["items"]),
                failed=sum(item["error"] is not None for item in batch["items"]),
                provenance=batch["provenance"],
            )
            write_json(
                folder / "gemma_outputs.json",
                {str(i + 1): result for i, result in extracted.items()},
            )
    rows, seen = [], {}
    for i, raw in enumerate(raw_rows):
        result = extracted.get(i, {})
        try:
            row = normalize_row(raw, mapping, options, result.get("value"))
        except (ValueError, TypeError) as exc:
            row = dict(
                role=None,
                level="Unknown",
                location=None,
                experience_years=None,
                skills=[],
                salary_monthly_vnd=None,
                salary_status="invalid",
                posted_date=None,
                warnings=[],
                errors=[str(exc)],
                extraction=None,
            )
        row["gemma_status"] = (
            "failed" if result.get("error") else "succeeded" if result else "not_used"
        )
        if result.get("error"):
            row["warnings"].append("Gemma thất bại; chỉ dùng cột đã cung cấp: " + result["error"])
        if row["role"] and row["role"] not in model.roles:
            row["errors"].append("Vai trò chưa hỗ trợ; model hiện dành cho nhóm lập trình viên")
        if (
            len(row["skills"]) > 100
            or any(len(s) > 200 for s in row["skills"])
            or len(row["location"] or "") > 200
        ):
            row["errors"].append("Tên kỹ năng/khu vực quá dài hoặc vượt 100 kỹ năng")
        key = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        duplicate_of = seen.get(key)
        seen.setdefault(key, i + 1)
        row.update(
            source_row=i + 1,
            input=raw,
            duplicate_of=duplicate_of,
            status="invalid" if row["errors"] else "ok",
            predicted_salary_vnd=None,
            ridge_salary_vnd=None,
            random_forest_salary_vnd=None,
            comparison_salary_vnd=None,
            error_vnd=None,
        )
        if row["status"] == "ok":
            row["warnings"].extend(model.warnings(row))
        if duplicate_of:
            row["warnings"].append(
                f"Trùng hoàn toàn dòng {duplicate_of}; không đếm lại trong thống kê"
            )
        rows.append(row)
    valid = [r for r in rows if r["status"] == "ok"]
    progress("Dự đoán bằng Random Forest và Ridge", 40)
    if valid:
        predictions = model.predict(valid)
        for i, row in enumerate(valid):
            rf, ridge = predictions["random_forest"][i], predictions["ridge"][i]
            if not math.isfinite(rf) or not math.isfinite(ridge):
                raise ValueError("Model trả kết quả không hữu hạn")
            chosen = predictions[model.selected_model][i]
            other = ridge if model.selected_model == "random_forest" else rf
            row.update(
                predicted_salary_vnd=round(chosen),
                ridge_salary_vnd=round(ridge),
                random_forest_salary_vnd=round(rf),
                comparison_salary_vnd=round(other),
            )
            if row["salary_monthly_vnd"] is not None:
                row["error_vnd"] = round(chosen - row["salary_monthly_vnd"])
    unique = [r for r in valid if r["duplicate_of"] is None]
    labeled = [r for r in unique if r["salary_monthly_vnd"] is not None]
    metrics = {}
    if labeled:
        target = [r["salary_monthly_vnd"] for r in labeled]
        for name, col in [
            ("random_forest", "random_forest_salary_vnd"),
            ("ridge", "ridge_salary_vnd"),
        ]:
            pred = [r[col] for r in labeled]
            metrics[name] = dict(
                samples=len(target),
                mae_vnd=mean_absolute_error(target, pred),
                rmse_vnd=math.sqrt(mean_squared_error(target, pred)),
                r2=r2_score(target, pred) if len(target) > 1 and np.var(target) > 0 else None,
            )
    progress("Vẽ biểu đồ Matplotlib & Seaborn", 60)
    charts = build_charts(rows, folder, model_name=model.selected_model)
    warnings = [
        "Metric trên bảng nhập chỉ là độ khớp tại đây, không thay thế test độc lập.",
        "Lương dự đoán: VND/tháng; gross/net chưa xác định. Không phải cam kết thu nhập.",
    ]
    if not labeled:
        warnings.append("Không có nhãn lương VND/tháng hợp lệ; không tính MAE/RMSE/R².")
    if not any(r["posted_date"] for r in unique):
        warnings.append(
            "Không có ngày đăng hợp lệ; chỉ thể hiện thống kê tại bảng, "
            "không có xu hướng thời gian."
        )
    report = dict(
        filename=dataset["filename"],
        provenance=dataset["provenance"],
        input_sha256=dataset["input_sha256"],
        dataset_snapshot_sha256=dataset["snapshot_sha256"],
        salary_provenance=model.provenance,
        gemma_execution=gemma_execution,
        request=options.model_dump(),
        summary=dict(
            rows=len(rows),
            predicted=len(valid),
            invalid=len(rows) - len(valid),
            duplicates=sum(r["duplicate_of"] is not None for r in rows),
            labeled=len(labeled),
            unique_jobs=len(unique),
            median_prediction_vnd=float(np.median([r["predicted_salary_vnd"] for r in unique]))
            if unique
            else None,
            skill_count=len({s for r in unique for s in r["skills"]}),
        ),
        metrics=metrics,
        charts=charts,
        warnings=warnings,
        model=dict(
            experiment_id=model.experiment,
            selected_model=model.selected_model,
            train_jobs=len(model.train),
            historical_test=model.historical_test,
            label_quality=model.label_quality,
            train_label_counts=model.train.label_quality.value_counts().to_dict()
            if "label_quality" in model.train
            else {"silver": len(model.train)},
        ),
    )
    progress("Xuất bảng và gói kết quả", 90)
    report["files"] = export_results(rows, folder, report)
    write_json(folder / "report.json", report)
    return report

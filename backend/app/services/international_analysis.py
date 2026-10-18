"""Batch annual-USD inference; never reinterpret it as Vietnam monthly job offers."""

import json
import math

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.app.services.analysis import export_results, write_json
from backend.app.services.charts import build_charts
from backend.app.services.data import numeric
from backend.app.services.international import international_service


def analyze_international(dataset, options, folder, progress):
    if options.use_gemma:
        raise ValueError(
            "Adapter Gemma hiện dùng hợp đồng tin Việt Nam; nhánh khảo sát dùng cột có sẵn"
        )
    mapping = options.mapping
    if set(mapping.values()) - set(dataset["columns"]):
        raise ValueError("Cột ghép không có trong bảng")
    if not {"role", "country"}.issubset(mapping):
        raise ValueError("Nhánh quốc tế cần ghép cột vai trò và quốc gia")
    model = international_service()
    rows, seen = [], {}
    progress("Chuẩn hóa hồ sơ quốc tế · USD/năm", 15)
    for i, raw in enumerate(dataset["rows"]):
        source = {key: raw.get(column) for key, column in mapping.items()}
        row = model.normalize(source)
        actual = None
        salary_raw = source.get("salary")
        if salary_raw is not None and str(salary_raw).strip():
            known_annual_usd = mapping.get("salary", "").casefold() in {
                "salary_annual_usd",
                "convertedcompyearly",
            }
            if mapping.get("salary", "").casefold() == "salary_monthly_vnd":
                row["warnings"].append("Cột VND/tháng không dùng chấm nhánh thu nhập USD/năm")
            elif known_annual_usd or (options.currency == "USD" and options.period == "year"):
                actual = numeric(salary_raw)
                if actual is not None:
                    actual *= options.salary_scale
                if actual is None or not math.isfinite(actual) or actual <= 0:
                    actual = None
                    row["warnings"].append("Lương đối chiếu cần là số USD/năm dương")
            else:
                row["warnings"].append("Không chấm nhãn lương thiếu xác nhận đơn vị USD/năm")
        signature = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        duplicate = seen.get(signature)
        seen.setdefault(signature, i + 1)
        row.update(
            source_row=i + 1,
            input=raw,
            duplicate_of=duplicate,
            status="invalid" if row["errors"] else "ok",
            extraction=None,
            gemma_status="not_used",
            posted_date=None,
            salary_annual_usd=actual,
            predicted_salary_usd_year=None,
            ridge_salary_usd_year=None,
            random_forest_salary_usd_year=None,
            comparison_salary_usd_year=None,
            error_usd_year=None,
            unit="USD/year",
        )
        if duplicate:
            row["warnings"].append(f"Trùng dòng {duplicate}; không đếm lại trong metric/biểu đồ")
        rows.append(row)
    valid = [row for row in rows if row["status"] == "ok"]
    progress("Dự đoán thu nhập quốc tế bằng Ridge / Random Forest", 40)
    if valid:
        values = model.predict(valid)
        for i, row in enumerate(valid):
            if any(not math.isfinite(v[i]) or v[i] <= 0 for v in values.values()):
                row["status"] = "invalid"
                row["errors"].append("Hồ sơ ngoài phạm vi dự đoán thu nhập dương/hữu hạn")
                row["prediction_diagnostic"] = {
                    family: float(v[i]) if math.isfinite(v[i]) else str(v[i])
                    for family, v in values.items()
                }
                continue
            for family, values_family in values.items():
                row[family + "_salary_usd_year"] = round(values_family[i])
            selected = values[model.selected_model][i]
            other = "ridge" if model.selected_model == "random_forest" else "random_forest"
            row["predicted_salary_usd_year"] = round(selected)
            row["comparison_salary_usd_year"] = round(values[other][i])
            if row["salary_annual_usd"] is not None:
                row["error_usd_year"] = round(selected - row["salary_annual_usd"])
    valid = [r for r in rows if r["status"] == "ok"]
    unique = [r for r in valid if r["duplicate_of"] is None]
    labeled = [r for r in unique if r["salary_annual_usd"] is not None]
    metrics = {}
    for family in ["ridge", "random_forest"]:
        if not labeled:
            break
        actual = [r["salary_annual_usd"] for r in labeled]
        pred = [r[family + "_salary_usd_year"] for r in labeled]
        metrics[family] = dict(
            samples=len(actual),
            mae_usd_year=mean_absolute_error(actual, pred),
            rmse_usd_year=math.sqrt(mean_squared_error(actual, pred)),
            r2=r2_score(actual, pred) if len(actual) > 1 and np.var(actual) > 0 else None,
        )
    progress("Vẽ biểu đồ thu nhập · nghìn USD/năm", 65)
    charts = build_charts(rows, folder, model_name=model.selected_model, unit="USD/year")
    warnings = [
        "Dự đoán tổng thu nhập tự khai theo USD/năm, không phải lương chào tuyển VND/tháng.",
        "Metric chỉ trên dòng được chấp nhận trong bảng nhập; không phải test độc lập.",
        "Kỹ năng và thu nhập có liên hệ quan sát; không chứng minh tác động nhân quả.",
    ]
    if not labeled:
        warnings.append("Không có nhãn USD/năm hợp lệ; không tính metric trên bảng nhập.")
    rejected = sum("prediction_diagnostic" in r for r in rows)
    if rejected:
        warnings.append(
            f"Có {rejected} dòng ngoài phạm vi dự đoán dương/hữu hạn; "
            "loại khỏi biểu đồ/metric và giữ chẩn đoán trong bảng lỗi. "
            "Metric chỉ mô tả các dòng được chấp nhận, không chứng minh sai số model giảm."
        )
    report = dict(
        filename=dataset["filename"],
        provenance=dataset["provenance"],
        input_sha256=dataset["input_sha256"],
        dataset_snapshot_sha256=dataset["snapshot_sha256"],
        unit="USD/year",
        market="international_survey",
        salary_provenance=model.provenance,
        gemma_execution=dict(requested=False, used=False, rows=0),
        request=options.model_dump(),
        summary=dict(
            rows=len(rows),
            predicted=len(valid),
            invalid=len(rows) - len(valid),
            duplicates=sum(r["duplicate_of"] is not None for r in rows),
            labeled=len(labeled),
            unique_jobs=len(unique),
            median_prediction_usd_year=float(
                np.median([r["predicted_salary_usd_year"] for r in unique])
            )
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
            unit="USD/year",
        ),
    )
    progress("Xuất CSV / Excel / ZIP · USD/năm", 90)
    report["files"] = export_results(rows, folder, report)
    write_json(folder / "report.json", report)
    return report

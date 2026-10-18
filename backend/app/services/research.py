"""Read-only research views backed by frozen train charts and paired test metrics."""

import hashlib
import json

from backend.app.services.data import ROOT
from backend.app.services.salary import salary_service

EXPERIMENT = "v2_042e3aa1a886"
FOLDER = "outputs/eda/salary_v2_strict_train_042e3aa1a886"
SUMMARY_SHA256 = "6ec9d14c1e6fc2a41fd65a71e6c813e40e055c47c09ce582687f40fe842b5c8d"
CHARTS = [
    (
        "skill_demand",
        "Công nghệ có nhu cầu tuyển dụng cao",
        "Số tin đề cập từng công nghệ; một tin có thể yêu cầu nhiều kỹ năng.",
    ),
    (
        "skill_salary",
        "Công nghệ có mức lương cao",
        "Trung vị lương chào tuyển; chỉ nhóm có ít nhất 5 tin và 5 công ty.",
    ),
    (
        "experience_salary",
        "Kinh nghiệm và mức lương",
        "Tương quan trên train, không phải tác động nhân quả hay điểm đánh giá model.",
    ),
    (
        "salary_by_role",
        "So sánh lương theo vai trò",
        "Phân bố lương của nhóm có ít nhất 5 tin; không suy diễn vai trò chưa có trong mẫu.",
    ),
    (
        "salary_by_location",
        "So sánh lương theo khu vực",
        "Chỉ khu vực có ít nhất 5 tin; giữ nguyên các nhóm nhỏ trong dữ liệu nguồn.",
    ),
]


def verified(path, digest):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("Dữ liệu phân tích không khớp phiên bản đã kiểm chứng")
    return content


def summary():
    service = salary_service()
    if service.experiment != EXPERIMENT:
        raise ValueError("Chưa có bộ biểu đồ train cho phiên bản model đang phục vụ")
    data = json.loads(verified(ROOT / FOLDER / "summary.json", SUMMARY_SHA256))
    if data["dataset_manifest_sha256"] != service.manifest["dataset_manifest"]["sha256"]:
        raise ValueError("Biểu đồ và model thuộc hai phiên bản dữ liệu khác nhau")
    return service, data


def chart_path(key):
    if key.startswith("global_"):
        view, folder = international_view()
        matched = next((item for item in view["charts"] if item["id"] == key), None)
        if not matched:
            raise FileNotFoundError(key)
        path = folder / matched["file"]
        verified(path, view["files"][path.name])
        return path
    if key not in {row[0] for row in CHARTS}:
        raise FileNotFoundError(key)
    _, data = summary()
    path = ROOT / FOLDER / (key + ".png")
    verified(path, data["files"][path.name])
    return path


def international_view():
    config = json.loads((ROOT / "configs/international_research.json").read_text())
    view = json.loads(verified(ROOT / config["view"], config["sha256"]))
    return view, ROOT / config["folder"]


def overview():
    service, data = summary()
    evaluation = service.manifest["evaluation"]
    metrics = json.loads(verified(ROOT / evaluation["path"], evaluation["sha256"]))
    extra = []
    registry = ROOT / "configs/research_benchmarks.json"
    if registry.exists():
        for item in json.loads(registry.read_text())["experiments"]:
            manifest = json.loads(verified(ROOT / item["manifest"], item["sha256"]))
            experiment_metrics = manifest["evaluation"]
            result = json.loads(
                verified(ROOT / experiment_metrics["path"], experiment_metrics["sha256"])
            )
            extra.append(
                dict(
                    id=item["id"],
                    title=item["title"],
                    unit=item["unit"],
                    scope=item["scope"],
                    samples=result["samples"],
                    metrics=result["test"],
                    selected_model=result["selected_family"],
                    selection_note=(
                        "Chọn bằng validation riêng của nhánh quốc tế; "
                        "không so trực tiếp với metric VND/tháng."
                    ),
                    limits=(
                        "Khảo sát thu nhập quốc tế, không phải lương chào tuyển Việt Nam. "
                        + (
                            "Có kỹ năng và WorkExp; dùng nhánh quốc tế để suy luận."
                            if item["id"] == "global_survey"
                            else "AIJobs chỉ nghiên cứu; không có kỹ năng hay số năm kinh nghiệm."
                        )
                    ),
                )
            )
    return dict(
        experiment_id=service.experiment,
        selected_model=service.selected_model,
        dataset=dict(
            name="TiniX · mẫu tuyển dụng lập trình viên",
            source_url="https://huggingface.co/datasets/tinixai/vietnamese-job-descriptions",
            rows=data["rows"],
            companies=data["company_groups"],
            role_counts=data["roles"],
            scope="79 tin train có bằng chứng kỳ tháng; nhãn silver, không phải toàn thị trường",
            target="Trung điểm lương chào tuyển · VND/tháng; gross/net chưa xác định",
            temporal_note="Snapshot mẫu tuyển dụng, chưa phải chuỗi xu hướng theo tháng.",
            weak_rows_excluded_from_charts=1078,
            input_sha256=data["input_sha256"],
        ),
        charts=[
            dict(id=key, title=title, caption=caption, url=f"/api/research/charts/{key}")
            for key, title, caption in CHARTS
        ],
        top_demand=data["top_demand"],
        top_salary_skills=data["top_salary_skills"],
        experience_salary_pearson=data["experience_salary_pearson"],
        additional_benchmarks=extra,
        international=international_view()[0],
        benchmark=dict(
            id="vietnam_offers",
            title="Tin tuyển dụng Việt Nam · VND/tháng",
            unit="VND/month",
            selected_model=service.selected_model,
            scope="Test đã lưu · cùng 30 tin, 23 nhóm công ty; chưa dùng để fit model",
            samples=30,
            metrics={
                name: metrics["test"][name]
                for name in ["ridge", "random_forest", "median_baseline"]
            },
            selection_note=(
                "Ridge được chọn bằng validation, không chọn lại theo test hoặc file vừa nhập."
            ),
            limits="Mẫu test nhỏ, nhãn silver; MAE không phải sai số tối đa cho từng hồ sơ.",
        ),
        training=dict(
            rows=len(service.train),
            strict_rows=79,
            weak_rows=1078,
            weak_weight=0.3,
            note=(
                "Model học cả nhãn thiếu kỳ được giả định tháng; "
                "các nhãn yếu không nằm trong 5 biểu đồ train phía trên."
            ),
        ),
    )

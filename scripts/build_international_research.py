"""Generate descriptive global train charts; never fit models or open holdout examples."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.charts import build_charts  # noqa: E402
from backend.app.services.international import international_service  # noqa: E402


def main():
    root = Path(__file__).resolve().parents[1]
    model = international_service()
    folder = root / "outputs/eda" / model.experiment
    folder.mkdir(parents=True, exist_ok=True)
    f = model.train.copy()
    f["skills"] = f.skills.str.split(";")
    f["status"] = "ok"
    f["duplicate_of"] = None
    f["posted_date"] = None
    charts = build_charts(
        f.to_dict("records"),
        folder,
        model_name=model.selected_model,
        unit="USD/year",
        include_predictions=False,
    )
    ex = f.explode("skills")
    ex = ex[ex.skills.ne("")]
    stats = (
        ex.groupby("skills")
        .agg(
            jobs=("profile_group", "size"),
            groups=("profile_group", "nunique"),
            median_salary=("salary_annual_usd", "median"),
        )
        .reset_index()
        .rename(columns={"skills": "skill"})
    )
    stats["median_salary_display"] = stats.median_salary / 1000
    stats.to_csv(folder / "skill_statistics.csv", index=False)
    for column in ["role", "country"]:
        f.groupby(column).agg(
            rows=("profile_group", "size"), median_salary_usd_year=("salary_annual_usd", "median")
        ).to_csv(folder / (column + "_statistics.csv"))
    stats = stats.sort_values(["jobs", "skill"], ascending=[False, True])
    paid = stats[stats.jobs.ge(5) & stats.groups.ge(5)].sort_values(
        ["median_salary", "skill"], ascending=[False, True]
    )
    labels = {
        "skill_demand": "Công nghệ phổ biến trong khảo sát",
        "skill_salary_observed": "Thu nhập theo công nghệ",
        "experience_observed": "Kinh nghiệm và thu nhập",
        "role_observed": "Thu nhập theo vai trò",
        "location_observed": "Thu nhập theo quốc gia",
    }
    for c in charts:
        c["title"] = labels[c["id"]]
        c["url"] = "/api/research/charts/global_" + c["id"]
        c["id"] = "global_" + c["id"]
    view = dict(
        dataset=dict(
            name="Stack Overflow Developer Survey 2024 · quốc tế",
            tag="TRAIN · KHẢO SÁT QUỐC TẾ",
            unit="USD/year",
            unit_label="nghìn USD/năm",
            entity_label="phản hồi",
            group_label="Nhóm hồ sơ",
            rows=len(f),
            groups=int(f.profile_group.nunique()),
            role_counts=f.role.value_counts().to_dict(),
            source_url="https://survey.stackoverflow.co/2024/",
            scope=(
                "Phản hồi train có WorkExp và thu nhập USD/năm; "
                "không đại diện toàn bộ lập trình viên"
            ),
            target="Tổng thu nhập tự khai · USD/năm, được nhà công bố quy đổi",
            temporal_note=(
                "Khảo sát năm 2024; không suy diễn xu hướng theo tháng hoặc lương thị trường 2026."
            ),
            weak_rows_excluded_from_charts=0,
            input_sha256=model.manifest["training_snapshot"]["sha256"],
        ),
        charts=charts,
        top_demand=stats.head(5).to_dict("records"),
        top_salary_skills=paid.head(5).to_dict("records"),
        experience_salary_pearson=float(f.experience_years.corr(f.salary_annual_usd)),
        training=dict(
            note=(
                "Chỉ dùng train trong phân tích; kỹ năng, quốc gia và thu nhập là dữ liệu tự khai. "
                "Không dùng ITviec hoặc trộn nhãn VND/tháng."
            )
        ),
        files={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.iterdir()
            if p.suffix in {".png", ".csv"}
        },
    )
    p = folder / "view.json"
    p.write_text(json.dumps(view, ensure_ascii=False, indent=2) + "\n")
    (root / "configs/international_research.json").write_text(
        json.dumps(
            dict(
                view=str(p.relative_to(root)),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                folder=str(folder.relative_to(root)),
            ),
            indent=2,
        )
        + "\n"
    )
    print("GLOBAL RESEARCH VIEW", len(f), "train records", len(charts), "charts")


if __name__ == "__main__":
    main()

"""Reproducible Matplotlib/Seaborn figures with explicit salary provenance."""

import os
import textwrap
from pathlib import Path

from backend.app.services.data import ROOT
from scripts.data_cleaning import SKILL_ALIASES

# Explicit display lexicon, separate from the salary model's fitted vocabulary.
TECHNOLOGIES = {name.casefold() for name in SKILL_ALIASES.values()} | {
    "dart",
    "flutter",
    "kotlin",
    "swift",
    "go",
    "golang",
    "rust",
    "ruby",
    "rails",
    "r",
    "scala",
    "perl",
    "objective-c",
    "spring",
    "spring framework",
    "next.js",
    "nest.js",
    "nestjs",
    "express",
    "express.js",
    ".net core",
    ".netcore",
    "asp.net core",
    "azure",
    "google cloud",
    "gcp",
    "redis",
    "elasticsearch",
    "kafka",
    "spark",
    "hadoop",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "machine learning",
    "nlp",
    "android",
    "ios",
    "unity",
    "unreal engine",
    "laravel",
    "symfony",
    "bootstrap",
    "jquery",
    "restful api",
    "restful apis",
    "api",
    "nosql",
    "oracle",
    "sqlite",
}

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


def build_charts(
    rows, folder: Path, model_name="random_forest", unit="VND/month", include_predictions=True
):
    model_label = "Ridge" if model_name == "ridge" else "Random Forest"
    valid = pd.DataFrame([r for r in rows if r["status"] == "ok" and r["duplicate_of"] is None])
    charts = []
    international = unit == "USD/year"
    divisor = 1000 if international else 1e6
    display_unit = "Nghìn USD/năm" if international else "Triệu VND/tháng"
    sns.set_theme(style="whitegrid", palette=["#29816b", "#407e9f", "#c07c55"])
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
        }
    )

    def figure(key, title, caption, draw):
        fig, ax = plt.subplots(figsize=(8, 4.6), layout="constrained")
        ax.set_title(title, loc="left", pad=18, fontsize=12)
        if not draw(ax):
            ax.text(
                0.5,
                0.5,
                "Chưa đủ dữ liệu phù hợp để vẽ biểu đồ này",
                ha="center",
                va="center",
                transform=ax.transAxes,
                wrap=True,
            )
            ax.set_xticks([])
            ax.set_yticks([])
        name = key + ".png"
        fig.savefig(folder / name, dpi=135, facecolor="white")
        plt.close(fig)
        charts.append(dict(id=key, title=title, caption=caption, file=name))

    if valid.empty:
        figure("skill_demand", "Nhu cầu kỹ năng", "Không có dòng dự đoán hợp lệ", lambda ax: False)
        return charts
    observed_key = "salary_annual_usd" if international else "salary_monthly_vnd"
    predicted_key = "predicted_salary_usd_year" if international else "predicted_salary_vnd"
    valid["observed_income"] = valid[observed_key]
    valid["predicted_income"] = valid[predicted_key] if include_predictions else float("nan")
    if international:
        valid["location"] = valid["country"]
    exploded = valid.explode("skills").dropna(subset=["skills"])
    if not international:
        exploded = exploded[exploded.skills.str.casefold().isin(TECHNOLOGIES)]
    demand = exploded["skills"].value_counts().head(10)

    def demand_plot(ax):
        if demand.empty:
            return False
        ax.barh(demand.index[::-1], demand.values[::-1], color="#29816b")
        ax.set_xlabel("Số mẫu có kỹ năng (loại dòng trùng hoàn toàn)")
        return True

    figure(
        "skill_demand",
        "Công nghệ đã sử dụng trong khảo sát"
        if international
        else "Top ngôn ngữ & công nghệ được tuyển dụng",
        ("Công nghệ trong khảo sát; " if international else "Danh mục công nghệ v1; ")
        + f"{len(valid)} mẫu hợp lệ, loại bản trùng. "
        "Kỹ năng ngoài danh mục vẫn được giữ trong bảng kết quả.",
        demand_plot,
    )

    sources = (
        [("predicted", "predicted_income", f"Dự đoán {model_label}")] if include_predictions else []
    )
    if valid.observed_income.notna().any():
        sources.insert(
            0,
            (
                "observed",
                "observed_income",
                "Thu nhập tự khai" if international else "Lương được cung cấp",
            ),
        )
    for source, column, label in sources:
        subset = valid.dropna(subset=[column]).copy()
        subset["income_display"] = subset[column] / divisor
        ex = subset.explode("skills").dropna(subset=["skills"])
        if not international:
            ex = ex[ex.skills.str.casefold().isin(TECHNOLOGIES)]
        stats = ex.groupby("skills")["income_display"].agg(["median", "count"])
        top = stats[stats["count"].ge(3)].nlargest(10, "median").sort_values("median")

        def skill_salary(ax, top=top):
            if top.empty:
                return False
            ax.barh(
                [f"{k} (n={int(v)})" for k, v in zip(top.index, top["count"])],
                top["median"],
                color="#407e9f",
            )
            ax.set_xlabel("Trung vị, " + display_unit)
            return True

        figure(
            f"skill_salary_{source}",
            f"{'Thu nhập' if international else 'Lương'} theo công nghệ · {label}",
            "Chỉ hiển thị kỹ năng có ít nhất 3 mẫu; liên hệ quan sát, không suy nhân quả",
            skill_salary,
        )

        def experience(ax, subset=subset):
            points = subset.dropna(subset=["experience_years"])
            if points.empty:
                return False
            if international:
                sns.scatterplot(
                    data=points,
                    x="experience_years",
                    y="income_display",
                    color="#407e9f",
                    ax=ax,
                    s=14,
                    alpha=0.25,
                    linewidth=0,
                )
            else:
                sns.scatterplot(
                    data=points,
                    x="experience_years",
                    y="income_display",
                    hue="role",
                    ax=ax,
                    s=44,
                    alpha=0.8,
                )
                ax.legend(title=None, fontsize=6, loc="best")
            ax.set(xlabel="Kinh nghiệm (năm)", ylabel=display_unit)
            return True

        figure(
            f"experience_{source}",
            f"Kinh nghiệm & thu nhập · {label}",
            f"{subset.experience_years.notna().sum()} mẫu đủ kinh nghiệm/lương",
            experience,
        )
        for category, category_label in [
            ("role", "vai trò"),
            ("location", "quốc gia" if international else "khu vực"),
        ]:

            def comparison(ax, category=category, subset=subset):
                groups = subset[category].fillna("Unknown").value_counts().head(8).index
                data = subset.copy()
                data[category] = data[category].fillna("Unknown")
                data = data[data[category].isin(groups)]
                if data.empty:
                    return False
                ax.boxplot(
                    [data.loc[data[category].eq(group), "income_display"] for group in groups],
                    orientation="horizontal",
                    tick_labels=[textwrap.fill(g, 29) for g in groups] if international else groups,
                    patch_artist=True,
                    boxprops={"facecolor": "#9bc5b5"},
                    flierprops={"markersize": 3},
                )
                ax.set(xlabel=display_unit, ylabel="")
                ax.tick_params(axis="y", labelsize=8)
                return True

            figure(
                f"{category}_{source}",
                f"{'Thu nhập' if international else 'Lương'} theo {category_label} · {label}",
                f"{len(subset)} mẫu; tối đa 8 nhóm phổ biến",
                comparison,
            )
    dated = valid.dropna(subset=["posted_date"])
    if len(dated):
        counts = (
            pd.to_datetime(dated.posted_date)
            .dt.to_period("M")
            .astype(str)
            .value_counts()
            .sort_index()
        )

        def timeline(ax):
            ax.plot(counts.index, counts.values, marker="o", color="#29816b")
            ax.set(xlabel="Tháng đăng", ylabel="Số tin")
            ax.tick_params(axis="x", rotation=35)
            return True

        figure(
            "posting_trend",
            "Số tin theo tháng đăng",
            "Chỉ dùng dòng có ngày đăng hợp lệ; không dự báo số tin tương lai",
            timeline,
        )
    labeled = valid.dropna(subset=["observed_income"])

    def actual_predicted(ax):
        if labeled.empty:
            return False
        ax.scatter(
            labeled.observed_income / divisor,
            labeled.predicted_income / divisor,
            color="#407e9f",
            alpha=0.8,
        )
        low = min(labeled.observed_income.min(), labeled.predicted_income.min()) / divisor
        high = max(labeled.observed_income.max(), labeled.predicted_income.max()) / divisor
        ax.plot([low, high], [low, high], "--", color="#c07c55")
        ax.set(
            xlabel=f"Cung cấp ({display_unit})", ylabel=f"Dự đoán {model_label} ({display_unit})"
        )
        return True

    if not labeled.empty and include_predictions:
        figure(
            "actual_predicted",
            "Đối chiếu lương cung cấp và dự đoán",
            "Độ khớp trên bảng nhập, chưa phải kiểm định độc lập",
            actual_predicted,
        )
    return charts

"""Reproducible Matplotlib/Seaborn figures with explicit salary provenance."""

import os
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


def build_charts(rows, folder: Path):
    valid = pd.DataFrame([r for r in rows if r["status"] == "ok" and r["duplicate_of"] is None])
    charts = []
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
    exploded = valid.explode("skills").dropna(subset=["skills"])
    exploded = exploded[exploded.skills.str.casefold().isin(TECHNOLOGIES)]
    demand = exploded["skills"].value_counts().head(10)

    def demand_plot(ax):
        if demand.empty:
            return False
        ax.barh(demand.index[::-1], demand.values[::-1], color="#29816b")
        ax.set_xlabel("Số tin có kỹ năng (loại dòng trùng hoàn toàn)")
        return True

    figure(
        "skill_demand",
        "Top ngôn ngữ & công nghệ được tuyển dụng",
        f"Danh mục công nghệ v1; {len(valid)} tin hợp lệ, loại bản trùng. "
        "Kỹ năng ngoài danh mục vẫn được giữ trong bảng kết quả.",
        demand_plot,
    )

    sources = [("predicted", "predicted_salary_vnd", "Dự đoán RF")]
    if valid.salary_monthly_vnd.notna().any():
        sources.insert(0, ("observed", "salary_monthly_vnd", "Lương được cung cấp"))
    for source, column, label in sources:
        subset = valid.dropna(subset=[column]).copy()
        subset["income_million"] = subset[column] / 1e6
        ex = subset.explode("skills").dropna(subset=["skills"])
        ex = ex[ex.skills.str.casefold().isin(TECHNOLOGIES)]
        stats = ex.groupby("skills")["income_million"].agg(["median", "count"])
        top = stats[stats["count"].ge(3)].nlargest(10, "median").sort_values("median")

        def skill_salary(ax, top=top):
            if top.empty:
                return False
            ax.barh(
                [f"{k} (n={int(v)})" for k, v in zip(top.index, top["count"])],
                top["median"],
                color="#407e9f",
            )
            ax.set_xlabel("Trung vị, triệu VND/tháng")
            return True

        figure(
            f"skill_salary_{source}",
            f"Lương theo công nghệ · {label}",
            "Chỉ hiển thị kỹ năng có ít nhất 3 mẫu; liên hệ quan sát, không suy nhân quả",
            skill_salary,
        )

        def experience(ax, subset=subset):
            points = subset.dropna(subset=["experience_years"])
            if points.empty:
                return False
            sns.scatterplot(
                data=points,
                x="experience_years",
                y="income_million",
                hue="role",
                ax=ax,
                s=44,
                alpha=0.8,
            )
            ax.set(xlabel="Kinh nghiệm (năm)", ylabel="Triệu VND/tháng")
            ax.legend(title=None, fontsize=6, loc="best")
            return True

        figure(
            f"experience_{source}",
            f"Kinh nghiệm & thu nhập · {label}",
            f"{subset.experience_years.notna().sum()} mẫu đủ kinh nghiệm/lương",
            experience,
        )
        for category, category_label in [("role", "vai trò"), ("location", "khu vực")]:

            def comparison(ax, category=category, subset=subset):
                groups = subset[category].fillna("Unknown").value_counts().head(8).index
                data = subset.copy()
                data[category] = data[category].fillna("Unknown")
                data = data[data[category].isin(groups)]
                if data.empty:
                    return False
                ax.boxplot(
                    [data.loc[data[category].eq(group), "income_million"] for group in groups],
                    orientation="horizontal",
                    tick_labels=groups,
                    patch_artist=True,
                    boxprops={"facecolor": "#9bc5b5"},
                    flierprops={"markersize": 3},
                )
                ax.set(xlabel="Triệu VND/tháng", ylabel="")
                ax.tick_params(axis="y", labelsize=8)
                return True

            figure(
                f"{category}_{source}",
                f"Lương theo {category_label} · {label}",
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
    labeled = valid.dropna(subset=["salary_monthly_vnd"])

    def actual_predicted(ax):
        if labeled.empty:
            return False
        ax.scatter(
            labeled.salary_monthly_vnd / 1e6,
            labeled.predicted_salary_vnd / 1e6,
            color="#407e9f",
            alpha=0.8,
        )
        low = min(labeled.salary_monthly_vnd.min(), labeled.predicted_salary_vnd.min()) / 1e6
        high = max(labeled.salary_monthly_vnd.max(), labeled.predicted_salary_vnd.max()) / 1e6
        ax.plot([low, high], [low, high], "--", color="#c07c55")
        ax.set(xlabel="Cung cấp (triệu VND/tháng)", ylabel="Dự đoán RF (triệu VND/tháng)")
        return True

    if not labeled.empty:
        figure(
            "actual_predicted",
            "Đối chiếu lương cung cấp và dự đoán",
            "Độ khớp trên bảng nhập, chưa phải kiểm định độc lập",
            actual_predicted,
        )
    return charts

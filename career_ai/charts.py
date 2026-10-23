"""Observed statistics; survey technology usage is distinct from hiring demand."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from .data import UNITS


def charts(frame, folder):
    folder.mkdir(parents=True, exist_ok=True)
    if frame.empty:
        return
    frame = frame.drop_duplicates(
        subset=["market", "role", "location", "experience_years", "skills"]
    )
    for market, f in frame.groupby("market"):
        money = "salary" if "salary" in f else "prediction"
        ex = f.assign(skills=f.skills.fillna("").str.split(";")).explode("skills")
        counts = ex[ex.skills.ne("")].skills.value_counts().head(10)
        counts.to_csv(folder / f"{market}_skill_counts.csv")
        fig, ax = plt.subplots(figsize=(9, 5))
        counts.sort_values().plot.barh(ax=ax)
        ax.set_title(
            "Technology usage in survey"
            if market == "international"
            else "Technology demand in job sample"
        )
        fig.tight_layout()
        fig.savefig(folder / f"{market}_skills.png")
        plt.close(fig)
        stats = ex[ex.skills.ne("")].groupby("skills")[money].agg(["count", "median"])
        stats.to_csv(folder / f"{market}_skill_income.csv")
        stats = stats[stats["count"] >= 5].nlargest(10, "median")
        if len(stats):
            fig, ax = plt.subplots(figsize=(9, 5))
            stats.sort_values("median")["median"].plot.barh(ax=ax)
            ax.set_xlabel(UNITS[market])
            fig.tight_layout()
            fig.savefig(folder / f"{market}_skill_income.png")
            plt.close(fig)
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.scatterplot(data=f, x="experience_years", y=money, alpha=0.25, ax=ax)
        ax.set_ylabel(UNITS[market])
        fig.tight_layout()
        fig.savefig(folder / f"{market}_experience.png")
        plt.close(fig)
        for col in ["role", "location"]:
            selected = f[col].value_counts().head(8).index
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.boxplot(data=f[f[col].isin(selected)], x=money, y=col, ax=ax)
            ax.set_xlabel(UNITS[market])
            fig.tight_layout()
            fig.savefig(folder / f"{market}_{col}.png")
            plt.close(fig)

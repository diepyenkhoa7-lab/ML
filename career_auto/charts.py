"""Observed statistics; survey technology usage is distinct from hiring demand."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from career_ai.data import UNITS


def charts(frame, folder):
    folder.mkdir(parents=True, exist_ok=True)
    if frame.empty:
        return
    for market, f in frame.groupby("market"):
        money = "salary" if "salary" in f else "prediction"
        qualifier = "Observed income" if money == "salary" else "Predicted income"
        ex = f.assign(skills=f.skills.fillna("").str.split(";")).explode("skills")
        counts = ex[ex.skills.ne("")].skills.value_counts().head(10)
        counts.to_csv(folder / f"{market}_skill_counts.csv")
        fig, ax = plt.subplots(figsize=(9, 5))
        if len(counts):
            counts.sort_values().plot.barh(ax=ax)
        else:
            ax.text(0.5, 0.5, "No observed skills", ha="center")
        ax.set_title(
            "Skills in input profiles (not measured hiring demand)"
            if money == "prediction"
            else (
                "Technology usage in survey"
                if market == "international"
                else "Technology demand in job sample"
            )
        )
        ax.set_xlabel("Number of rows reporting skill")
        fig.tight_layout()
        fig.savefig(folder / f"{market}_skills.png")
        plt.close(fig)
        stats = ex[ex.skills.ne("")].groupby("skills")[money].agg(["count", "median"])
        stats["low_support"] = stats["count"] < 10
        stats.to_csv(folder / f"{market}_skill_income.csv")
        stats = stats[~stats.low_support].nlargest(10, "median")
        fig, ax = plt.subplots(figsize=(9, 5))
        if len(stats):
            stats.sort_values("median")["median"].plot.barh(ax=ax)
        else:
            ax.text(0.5, 0.5, "Insufficient support: need >=10 rows per skill", ha="center")
        ax.set_title(f"{qualifier} by skill (observational association)")
        ax.set_xlabel(UNITS[market])
        fig.tight_layout()
        fig.savefig(folder / f"{market}_skill_income.png")
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.scatterplot(data=f, x="experience_years", y=money, alpha=0.25, ax=ax)
        ax.set_ylabel(UNITS[market])
        ax.set_title(f"{qualifier} and experience — {market}, n={len(f)}")
        fig.tight_layout()
        fig.savefig(folder / f"{market}_experience.png")
        plt.close(fig)
        for col in ["role", "location"]:
            selected = f[col].value_counts().head(8).index
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.boxplot(data=f[f[col].isin(selected)], x=money, y=col, ax=ax)
            ax.set_xlabel(UNITS[market])
            ax.set_title(f"{qualifier} by {col} — {market}, n={len(f)}")
            fig.tight_layout()
            fig.savefig(folder / f"{market}_{col}.png")
            plt.close(fig)

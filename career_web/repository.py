"""Read-only access to frozen data and measured model results."""

import json
import threading
from functools import lru_cache

from career_ai.data import ROOT, UNITS, load

from .config import BASELINE_RUN, MODEL_RUN

PLOT_LOCK = threading.Lock()
CHARTS = ["skills", "skill_income", "experience", "role", "location"]
LABELS = {"vietnam": "Việt Nam", "international": "Quốc tế"}


def read_json(path):
    return json.loads(path.read_text())


def records(frame):
    # NaN/Inf cannot appear in JSON responses.
    return json.loads(frame.to_json(orient="records", force_ascii=False))


@lru_cache(maxsize=1)
def training_data():
    return load("train")


def selected(market):
    frame = training_data()
    return frame[frame.market.eq(market)]


def chart_urls(folder, market):
    return [dict(kind=k, url=f"{folder}/{market}/{k}") for k in CHARTS]


def ensure_charts():
    folder = ROOT / "outputs/eda"
    if not all((folder / f"{m}_{k}.png").exists() for m in UNITS for k in CHARTS):
        from career_auto.charts import charts

        with PLOT_LOCK:
            charts(training_data(), folder)


def overview(market):
    frame = selected(market)
    skills = frame.skills.fillna("").str.split(";").explode()
    counts = skills[skills.ne("")].value_counts().head(10)
    income = frame.assign(skill=frame.skills.str.split(";")).explode("skill")
    income = income.groupby("skill").salary.agg(["count", "median"])
    income = income[income["count"].ge(10)].nlargest(10, "median").reset_index()
    manifest = read_json(ROOT / "data/tensorflow_v1/manifest.json")
    return dict(
        market=market,
        label=LABELS[market],
        unit=UNITS[market],
        samples=len(frame),
        median_salary=float(frame.salary.median()),
        median_experience=float(frame.experience_years.median()),
        locations=int(frame.location.nunique()),
        roles=sorted(frame.role.unique().tolist()),
        countries=sorted(frame.location.unique().tolist()),
        top_skills=[dict(skill=s, count=int(n)) for s, n in counts.items()],
        income_by_skill=records(income),
        charts=chart_urls("/api/charts/data", market),
        source="Tin tuyển dụng TiniX 2026" if market == "vietnam" else "Stack Overflow Survey 2024",
        source_kind="job_posts" if market == "vietnam" else "survey",
        population="Tập train; không dùng dữ liệu test để mô tả hay gợi ý kỹ năng.",
        split_counts={k: v["rows"] for k, v in manifest["files"].items() if "rows" in v},
    )


def browse(market, query="", role="", location="", page=1, size=15):
    frame = selected(market)
    if role:
        frame = frame[frame.role.eq(role)]
    if location:
        frame = frame[frame.location.eq(location)]
    if query:
        text = frame[["role", "location", "skills"]].fillna("").agg(" ".join, axis=1)
        frame = frame[text.str.contains(query, case=False, regex=False)]
    return frame, dict(
        total=len(frame),
        page=page,
        size=size,
        unit=UNITS[market],
        rows=records(frame.iloc[(page - 1) * size : page * size]),
    )


@lru_cache(maxsize=1)
def model_metrics():
    meta = read_json(MODEL_RUN / "llm.json")
    return dict(
        model="Qwen3-1.7B + LoRA + đầu hồi quy",
        model_version=f"llm:{MODEL_RUN.name}",
        selected_epoch=meta["selected_epoch"],
        training_rows=meta["training_rows"],
        rank=meta["rank"],
        context=meta["context"],
        llm=read_json(MODEL_RUN / "llm_test_metrics.json"),
        baseline=read_json(BASELINE_RUN / "baseline_test_metrics.json"),
        language=read_json(MODEL_RUN / "language_test.json"),
        validation=read_json(MODEL_RUN / "llm_valid_metrics.json"),
        note="Chọn model theo validation. Test dùng báo cáo cuối; nhãn trích xuất là silver.",
    )

"""Real local-model HTTP smoke; no training, no fixture model, no quality claim."""

import json
import sys
import time
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import pandas as pd

    from career_ai.data import FEATURES, UNITS, digest, load

    folder = ROOT / "outputs/web"
    run = ROOT / "outputs/qwen_20261023T082631"
    weights = {name: digest(run / name) for name in ["qwen.lora.h5", "salary_head.keras"]}
    source = load("train")
    rows = [
        source[source.market.eq(m)].iloc[0][FEATURES + ["salary"]].to_dict()
        for m in ["vietnam", "international"]
    ]
    for row in rows:
        row["unit"] = UNITS[row["market"]]
    rows.append(
        dict(market="vietnam", role=None, location="Hà Nội", experience_years=3, skills="python")
    )
    samples = folder / "samples"
    samples.mkdir(parents=True, exist_ok=True)
    (samples / "profiles.json").write_text(json.dumps(rows, ensure_ascii=False))
    pd.DataFrame(rows).to_csv(samples / "profiles.csv", index=False)
    pd.DataFrame(rows).to_excel(samples / "profiles.xlsx", index=False)
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30)
    checks = []

    def finish(job):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            value = client.get(f"/api/jobs/{job['id']}").raise_for_status().json()
            if value["status"] == "completed":
                return value, client.get(f"/api/jobs/{job['id']}/results").raise_for_status().json()
            if value["status"] in ["failed", "interrupted"]:
                raise ValueError(value)
            time.sleep(0.5)
        raise TimeoutError("Real model job did not finish within smoke timeout")

    reference = None
    for format in ["csv", "json", "xlsx"]:
        path = folder / "samples" / f"profiles.{format}"
        with path.open("rb") as stream:
            upload = (
                client.post("/api/uploads", files={"file": (path.name, stream)})
                .raise_for_status()
                .json()
            )
        job = (
            client.post(
                "/api/analyses",
                json=dict(
                    upload_id=upload["id"],
                    mapping=upload["mapping"],
                    market="vietnam",
                    include_advice=False,
                ),
            )
            .raise_for_status()
            .json()
        )
        status, result = finish(job)
        assert (status["valid"], status["errors"]) == (2, 1)
        values = [r["prediction"] for r in result["rows"][:2]]
        assert all(r["model_version"] == "llm:qwen_20261023T082631" for r in result["rows"][:2])
        assert result["rows"][0]["unit"] == "VND/month"
        assert result["rows"][1]["unit"] == "USD/year"
        if reference is not None:
            np.testing.assert_allclose(values, reference, rtol=1e-5)
        reference = values
        for output_format in ["csv", "json", "xlsx"]:
            data = client.get(f"/api/jobs/{job['id']}/download/{output_format}").raise_for_status()
            assert data.content
        for market in result["markets"]:
            for chart in market["charts"]:
                response = client.get(chart["url"]).raise_for_status()
                assert response.content.startswith(b"\x89PNG")
        checks.append(
            dict(
                format=format,
                job_id=job["id"],
                valid=2,
                errors=1,
                predictions=values,
                downloads=3,
                charts=10,
            )
        )
        print("Real HTTP inference passed:", format, flush=True)

    job = (
        client.post(
            "/api/profiles",
            json=dict(
                market="vietnam",
                location="Hà Nội",
                description="Tuyển Frontend Developer, 2 năm kinh nghiệm git, javascript.",
                include_advice=True,
            ),
        )
        .raise_for_status()
        .json()
    )
    status, result = finish(job)
    assert status["valid"] == 1
    assert result["rows"][0]["role"] and result["rows"][0]["skills"]
    checks.append(dict(text_extraction=True, job_id=job["id"], result=result["rows"][0]))
    assert all(digest(run / name) == expected for name, expected in weights.items())
    (folder / "real_http_acceptance.json").write_text(
        json.dumps(
            dict(
                passed=True,
                model_version="llm:qwen_20261023T082631",
                weights_unchanged=weights,
                checks=checks,
                quality_metric=False,
                note="Train-derived/synthetic demo cases; not a new independent benchmark",
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print("Real web smoke completed; model weights unchanged", flush=True)


if __name__ == "__main__":
    main()

"""Verify a running local application with synthetic inputs; never train or benchmark quality."""

import argparse
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--gemma", action="store_true", help="Also run one real GPU extraction")
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/app_verification/api_smoke.json")
    )
    args = parser.parse_args()
    session = requests.Session()
    checks = []

    def request(method, path, **kwargs):
        response = session.request(method, args.url + path, timeout=30, **kwargs)
        response.raise_for_status()
        return response

    def analyze(content, filename, mapping, gemma=False):
        preview = request("POST", "/api/datasets", files={"file": (filename, content)}).json()
        state = request(
            "POST",
            "/api/analyses",
            json=dict(
                dataset_id=preview["dataset_id"],
                mapping=mapping or preview["suggested_mapping"],
                use_gemma=gemma,
            ),
        ).json()
        started = time.monotonic()
        while state["status"] in {"running", "queued"}:
            if time.monotonic() - started > 330:
                raise TimeoutError("Analysis did not finish within 330 seconds")
            time.sleep(0.3)
            state = request("GET", "/api/analyses/" + state["id"]).json()
        assert state["status"] == "completed", state
        return state

    sample = pd.DataFrame(
        [
            dict(
                role="Backend Developer",
                level="Junior",
                location="Hà Nội",
                experience_years=3,
                skills="Python;SQL",
            )
        ]
    )
    buffer = io.BytesIO()
    sample.to_excel(buffer, index=False)
    for extension, content in [
        ("csv", sample.to_csv(index=False).encode()),
        ("xlsx", buffer.getvalue()),
        ("json", sample.to_json(orient="records").encode()),
    ]:
        result = analyze(content, "functional_sample." + extension, None)
        assert result["result"]["summary"]["predicted"] == 1
        assert result["result"]["metrics"] == {}
        archive = zipfile.ZipFile(
            io.BytesIO(
                request("GET", f"/api/analyses/{result['id']}/artifacts/analysis.zip").content
            )
        )
        assert archive.testzip() is None
        manifest = json.loads(archive.read("manifest.json"))
        for name, digest in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        checks.append(dict(format=extension, status="passed", summary=result["result"]["summary"]))
        print(extension, "passed", flush=True)
    if args.gemma:
        card = (
            "Phiếu tin tuyển dụng từ dữ liệu đã thu thập:\nChức danh: Backend Developer\n"
            "Địa điểm: Hà Nội\nKinh nghiệm: 3 năm\nKỹ năng: Python, FastAPI, PostgreSQL\n"
            "Lương: 20–30 triệu VND/tháng"
        )
        result = analyze(
            json.dumps([dict(description=card)], ensure_ascii=False).encode(),
            "synthetic_gemma.json",
            {"description": "description"},
            True,
        )
        row = request("GET", f"/api/analyses/{result['id']}/rows").json()["rows"][0]
        assert row["status"] == "ok" and row["extraction"]["role"] == "Backend Developer", row
        assert result["result"]["metrics"] == {}
        assert "gemma_outputs.json" in result["result"]["files"]
        selected = result["result"]["model"]["selected_model"]
        expected = (
            row["ridge_salary_vnd"] if selected == "ridge" else row["random_forest_salary_vnd"]
        )
        assert row["predicted_salary_vnd"] == expected
        checks.append(
            dict(
                format="gemma_description",
                status="passed",
                row=row,
                model=result["result"]["model"],
                gemma_execution=result["result"]["gemma_execution"],
            )
        )
        print(f"Gemma extraction -> {selected} prediction passed", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            dict(
                status="passed",
                scope="Synthetic functional checks, not model quality or training",
                checks=checks,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()

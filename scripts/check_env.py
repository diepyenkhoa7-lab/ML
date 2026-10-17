"""Kiểm tra môi trường, không tải model hoặc huấn luyện trên dữ liệu thật."""

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlx", action="store_true", help="Yêu cầu Metal/MLX chạy thành công")
    args = parser.parse_args()
    packages = [
        "numpy",
        "pandas",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "openpyxl",
        "joblib",
        "fastapi",
        "uvicorn",
        "pydantic-settings",
        "PyYAML",
        "jupyterlab",
        "ipykernel",
        "httpx",
        "ruff",
    ]
    if args.mlx:
        packages += ["mlx", "mlx-lm", "datasets", "huggingface_hub"]
    versions, errors = {}, []
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"Thiếu package: {name}")

    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "versions": versions,
        "synthetic_only": True,
    }
    if not errors:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import seaborn as sns
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import Ridge
        from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        # Dữ liệu sinh ngẫu nhiên chỉ kiểm tra thư viện và metric, không dùng báo cáo đề tài.
        rng = np.random.default_rng(42)
        x = rng.normal(size=(120, 4))
        y = 20_000_000 + x @ np.array([3e6, 2e6, 1e6, 5e5]) + rng.normal(0, 1e5, 120)
        x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=42)
        result["synthetic_smoke_metrics"] = {}
        for name, estimator in {
            "ridge": make_pipeline(StandardScaler(), Ridge()),
            "random_forest": RandomForestRegressor(n_estimators=20, random_state=42, n_jobs=1),
        }.items():
            estimator.fit(x_train, y_train)
            prediction = estimator.predict(x_test)
            result["synthetic_smoke_metrics"][name] = {
                "mae": mean_absolute_error(y_test, prediction),
                "rmse": root_mean_squared_error(y_test, prediction),
                "r2": r2_score(y_test, prediction),
            }
        smoke_dir = ROOT / "outputs/environment"
        smoke_dir.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame({"x": x[:, 0], "y": y})
        sns.scatterplot(data=frame, x="x", y="y")
        plt.title("Environment check — synthetic data only")
        plt.tight_layout()
        plt.savefig(smoke_dir / "synthetic_smoke.png")
        plt.close()
        frame.to_excel(smoke_dir / "synthetic_smoke.xlsx", index=False)
        assert pd.read_excel(smoke_dir / "synthetic_smoke.xlsx").shape == frame.shape
        from fastapi.testclient import TestClient

        sys.path.insert(0, str(ROOT))
        from backend.app.main import app

        response = TestClient(app).get("/health")
        assert response.status_code == 200, response.text
        result["api_health"] = response.json()

    if args.mlx:
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json; import mlx.core as mx; "
                    "x=mx.array([1.,2.,3.]); y=(x*x).sum(); mx.eval(y); "
                    "assert y.item()==14.; assert mx.metal.is_available(); "
                    "print(json.dumps(mx.device_info()))"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if probe.returncode:
            errors.append("Metal/MLX không truy cập được GPU: " + probe.stderr[-1500:])
        else:
            result["metal_device"] = json.loads(probe.stdout)

    result["errors"] = errors
    result["ok"] = not errors
    filename = "check_mlx.json" if args.mlx else "check.json"
    output = ROOT / "outputs/environment" / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

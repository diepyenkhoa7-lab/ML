"""Load only checksum-verified trusted artifacts; preserve fitted preprocessing."""

import hashlib
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from backend.app.services.data import ROOT

EXPERIMENT = "bd9af2fa002caae8"
FEATURES = ["experience_years", "role", "level", "location", "skills"]


class SalaryService:
    def __init__(self):
        folder = ROOT / "models/salary" / EXPERIMENT
        self.manifest = json.loads((folder / "manifest.json").read_text())
        self.models = {}
        for name in ["ridge", "random_forest"]:
            item = self.manifest["artifacts"][name]
            path = ROOT / item["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError("Model checksum mismatch; refusing to load")
            self.models[name] = joblib.load(path)
        self.train = pd.read_csv(ROOT / "data/splits/v1.0.1/vn_developer/train.csv")
        self.roles = sorted(self.train.role.dropna().unique().tolist())
        self.locations = set(self.train.location.dropna())
        self.levels = set(self.train.level.dropna())
        self.experience_range = [
            float(self.train.experience_years.min()),
            float(self.train.experience_years.max()),
        ]
        vectorizer = (
            self.models["ridge"]
            .named_steps["preprocess"]
            .named_transformers_["skills"]
            .named_steps["vectorizer"]
        )
        self.skill_vocabulary = set(vectorizer.get_feature_names_out())
        self.associations = pd.read_csv(
            ROOT / f"outputs/metrics/salary_{EXPERIMENT}/ridge_skill_associations_train.csv"
        )

    def warnings(self, row):
        output = []
        if row["location"] and row["location"] not in self.locations:
            output.append("Khu vực chưa xuất hiện trong train")
        if row["level"] not in self.levels:
            output.append("Cấp bậc chưa xuất hiện trong train")
        exp = row["experience_years"]
        if exp is not None and not self.experience_range[0] <= exp <= self.experience_range[1]:
            output.append("Kinh nghiệm ngoài khoảng quan sát trong train")
        unknown = [s for s in row["skills"] if s.casefold() not in self.skill_vocabulary]
        if unknown:
            output.append("Kỹ năng chưa có trong từ vựng model: " + ", ".join(unknown))
        actual = row.get("salary_monthly_vnd")
        if (
            actual is not None
            and not self.train.salary_monthly_vnd.min()
            <= actual
            <= self.train.salary_monthly_vnd.max()
        ):
            output.append("Lương cung cấp ngoài khoảng train; kiểm tra đơn vị và kỳ lương")
        return output

    @staticmethod
    def features(rows):
        # Exactly matches notebook 02: numeric float, categorical objects, semicolon skills.
        frame = pd.DataFrame(
            [{k: (";".join(row[k]) if k == "skills" else row[k]) for k in FEATURES} for row in rows]
        )
        frame["experience_years"] = pd.to_numeric(frame.experience_years, errors="raise").astype(
            float
        )
        for col in FEATURES[1:]:
            frame[col] = frame[col].astype(object).where(frame[col].notna(), np.nan)
        frame["skills"] = frame["skills"].replace("", np.nan)
        return frame

    def predict(self, rows):
        features = self.features(rows)
        return {name: model.predict(features).tolist() for name, model in self.models.items()}

    def advise(self, row):
        if row["errors"]:
            raise ValueError("; ".join(row["errors"]))
        if row["role"] not in self.roles:
            raise ValueError("Vai trò chưa được model hỗ trợ")
        base = self.predict([row])
        candidates = self.associations[self.associations.coefficient_vnd.gt(0)].to_dict("records")
        known = {s.casefold() for s in row["skills"]}
        recommendations = []
        for item in candidates:
            skill = item["skill"]
            if skill in known:
                continue
            changed = dict(row, skills=row["skills"] + [skill])
            delta = self.predict([changed])["random_forest"][0] - base["random_forest"][0]
            if delta <= 0:
                continue
            recommendations.append(
                dict(
                    skill=skill,
                    train_support=int(item["train_rows"]),
                    predicted_delta_vnd=round(delta),
                    ridge_association_vnd=round(item["coefficient_vnd"]),
                )
            )
        recommendations.sort(key=lambda r: r["predicted_delta_vnd"], reverse=True)
        return dict(
            profile={k: row[k] for k in FEATURES},
            predictions={k: round(v[0]) for k, v in base.items()},
            selected_model="random_forest",
            warnings=row["warnings"] + self.warnings(row),
            recommendations=recommendations[:4],
            explanation=(
                "Gợi ý từ kỹ năng có ít nhất 5 mẫu train và hệ số Ridge dương; "
                "chênh lệch là dự đoán RF khi thay một kỹ năng, "
                "không phải mức tăng lương được bảo đảm."
            ),
            evidence=dict(
                experiment_id=EXPERIMENT,
                train_jobs=len(self.train),
                label_quality="silver",
                historical_test_mae_vnd=6656370,
                supported_experience_years=self.experience_range,
            ),
        )


@lru_cache(maxsize=1)
def salary_service():
    return SalaryService()

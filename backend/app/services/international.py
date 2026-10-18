"""Annual-USD compensation predictions with an explicit international survey contract."""

import hashlib
import io
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from backend.app.services.data import ROOT, skills_from


class InternationalSalaryService:
    def __init__(self):
        config = json.loads((ROOT / "configs/international_application.json").read_text())

        def verified(item):
            content = (ROOT / item["path"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("International artifact checksum mismatch")
            return content

        manifest_bytes = verified(config["manifest"])
        self.manifest = json.loads(manifest_bytes)
        if (
            self.manifest.get("serving_scope") != "international_survey_only"
            or self.manifest.get("unit") != "USD/year"
            or not self.manifest.get("profile_serving_eligible")
        ):
            raise ValueError("Model không phù hợp hợp đồng khảo sát quốc tế")
        evaluation = json.loads(verified(self.manifest["evaluation"]))
        if not all(evaluation["profile_serving_gates"].values()):
            raise ValueError("International serving gates failed")
        self.experiment = self.manifest["experiment_id"]
        self.selected_model = self.manifest["selected_model"]
        self.models = {
            name: joblib.load(io.BytesIO(verified(item)))
            for name, item in self.manifest["artifacts"].items()
        }
        verified(self.manifest["dataset_manifest"])
        self.train = pd.read_csv(io.BytesIO(verified(self.manifest["training_snapshot"])))
        self.train["skills"] = self.train.skills.fillna("")
        self.roles = sorted(self.train.role.unique().tolist())
        self.countries = sorted(self.train.country.unique().tolist())
        self.historical_test = evaluation["test"][self.selected_model]
        self.experience_range = [
            float(self.train.experience_years.min()),
            float(self.train.experience_years.max()),
        ]
        self.label_quality = "Thu nhập tự khai trong khảo sát Stack Overflow 2024"
        self.provenance = dict(
            salary_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
            models=self.manifest["artifacts"],
            unit="USD/year",
        )
        self.vectorizer = (
            self.models["ridge"]
            .named_steps["preprocess"]
            .named_transformers_["skills"]
            .named_steps["vectorizer"]
        )
        self.vocabulary = set(self.vectorizer.get_feature_names_out())

    def metadata(self):
        return dict(
            experiment_id=self.experiment,
            selected_model=self.selected_model,
            roles=self.roles,
            countries=self.countries,
            unit="USD/year",
            train_jobs=len(self.train),
            test_jobs=self.historical_test["samples"],
            test_mae_usd_year=self.historical_test["mae_usd_year"],
            label_quality=self.label_quality,
        )

    def normalize(self, raw):
        role = str(raw.get("role") or "").strip()
        country = str(raw.get("country") or "").strip()
        errors, warnings = [], []
        if role not in self.roles:
            errors.append("Vai trò chưa có trong nhánh khảo sát quốc tế")
        if country not in self.countries:
            errors.append("Chọn quốc gia thuộc tập khảo sát quốc tế")
        experience = raw.get("experience_years")
        if experience is None or experience == "":
            experience = float(self.train.experience_years.median())
            warnings.append("Thiếu kinh nghiệm; dùng trung vị train để suy luận")
        try:
            experience = float(experience)
            if not np.isfinite(experience) or not 0 <= experience <= 80:
                raise ValueError
        except (ValueError, TypeError):
            experience = None
            errors.append("Kinh nghiệm cần là số từ 0 đến 80 năm")
        if (
            experience is not None
            and not self.experience_range[0] <= experience <= self.experience_range[1]
        ):
            warnings.append("Kinh nghiệm ngoài khoảng quan sát của train quốc tế")
        try:
            skills = skills_from(raw.get("skills"))
        except ValueError as exc:
            skills = []
            errors.append(str(exc))
        if len(skills) > 100 or any(len(s) > 200 for s in skills):
            errors.append("Tối đa 100 kỹ năng, mỗi tên không quá 200 ký tự")
        unknown = [s for s in skills if s.casefold() not in self.vocabulary]
        if unknown:
            warnings.append("Kỹ năng chưa có trong từ vựng model: " + ", ".join(unknown))
        if not skills:
            warnings.append("Chưa cung cấp kỹ năng cho hồ sơ")
        return dict(
            role=role,
            country=country,
            experience_years=experience,
            skills=skills,
            errors=errors,
            warnings=warnings,
        )

    def features(self, rows):
        return pd.DataFrame(
            [
                dict(
                    experience_years=r["experience_years"],
                    role=r["role"],
                    country=r["country"],
                    skills=";".join(r["skills"]).casefold(),
                )
                for r in rows
            ]
        )

    def predict(self, rows):
        frame = self.features(rows)
        return {name: model.predict(frame).tolist() for name, model in self.models.items()}

    def advise(self, raw):
        row = self.normalize(raw)
        if row["errors"]:
            raise ValueError("; ".join(row["errors"]))
        base = self.predict([row])
        if any(not np.isfinite(v[0]) or v[0] <= 0 for v in base.values()):
            raise ValueError("Hồ sơ ngoài phạm vi dự đoán thu nhập dương")
        subset = self.train[self.train.role.eq(row["role"])]
        counts = np.asarray(self.vectorizer.transform(subset.skills).sum(axis=0)).ravel()
        known = {s.casefold() for s in row["skills"]}
        names = self.vectorizer.get_feature_names_out()
        eligible = [
            (skill, int(count))
            for skill, count in zip(names, counts, strict=True)
            if count >= 5 and skill not in known
        ]
        recommendations = []
        if eligible:
            variants = [dict(row, skills=row["skills"] + [skill]) for skill, _ in eligible]
            changed = self.models[self.selected_model].predict(self.features(variants))
            for (skill, count), prediction in zip(eligible, changed, strict=True):
                delta = prediction - base[self.selected_model][0]
                if delta > 0:
                    recommendations.append(
                        dict(
                            skill=skill,
                            role_support=count,
                            train_support=count,
                            predicted_delta_usd_year=round(delta),
                        )
                    )
        recommendations.sort(key=lambda r: r["predicted_delta_usd_year"], reverse=True)
        return dict(
            unit="USD/year",
            target_label="Tổng thu nhập tự khai theo năm",
            market_reference=None,
            profile={k: row[k] for k in self.manifest["features"]},
            predictions={k: round(v[0]) for k, v in base.items()},
            selected_model=self.selected_model,
            warnings=row["warnings"],
            recommendations=recommendations[:4],
            explanation=(
                "Kỹ năng có ít nhất 5 phản hồi train cùng vai trò; "
                "chênh lệch do model dự đoán, không phải cam kết tăng thu nhập."
            ),
            evidence=dict(
                experiment_id=self.experiment,
                unit="USD/year",
                train_jobs=len(self.train),
                label_quality=self.label_quality,
                historical_test_mae_usd_year=self.historical_test["mae_usd_year"],
                historical_test_samples=self.historical_test["samples"],
                supported_experience_years=self.experience_range,
            ),
        )


@lru_cache(maxsize=1)
def international_service():
    return InternationalSalaryService()

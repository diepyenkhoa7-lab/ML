"""Load only checksum-verified trusted artifacts; preserve fitted preprocessing."""

import hashlib
import io
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from backend.app.services.data import ROOT
from backend.app.services.market import market_reference

EXPERIMENT = "bd9af2fa002caae8"
FEATURES = ["experience_years", "role", "level", "location", "skills"]


class SalaryService:
    def __init__(self, experiment=EXPERIMENT):
        folder = ROOT / "models/salary" / experiment
        self.experiment = experiment
        manifest_bytes = (folder / "manifest.json").read_bytes()
        self.manifest = json.loads(manifest_bytes)
        if self.manifest.get("promotion_eligible") is False:
            raise ValueError("Model chưa vượt điều kiện nghiệm thu; giữ model đang phục vụ")
        self.provenance = dict(
            salary_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(), models={}
        )
        self.selected_model = self.manifest["selected_model"]
        self.label_quality = self.manifest.get("label_quality", "silver")
        self.models = {}
        for name in ["ridge", "random_forest"]:
            item = self.manifest["artifacts"][name]
            path = ROOT / item["path"]
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("Model checksum mismatch; refusing to load")
            self.models[name] = joblib.load(io.BytesIO(content))
            self.provenance["models"][name] = item.copy()

        def verified(item):
            content = (ROOT / item["path"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError("Train/evaluation snapshot checksum mismatch")
            return content

        if "dataset_manifest" in self.manifest:
            dataset = json.loads(verified(self.manifest["dataset_manifest"]))
            content = verified(self.manifest["training_snapshot"])
            train_sha = self.manifest["training_snapshot"]["sha256"]
            evaluation = json.loads(verified(self.manifest["evaluation"]))
            if not evaluation["promotion_eligible"] or not all(
                evaluation["promotion_gates"].values()
            ):
                raise ValueError("Model chưa vượt điều kiện đưa vào ứng dụng")
            selection_path = (ROOT / self.manifest["evaluation"]["path"]).parent / "selection.json"
            selection_bytes = selection_path.read_bytes()
            if hashlib.sha256(selection_bytes).hexdigest() != self.manifest["selection_sha256"]:
                raise ValueError("Selection checksum mismatch")
            selection = json.loads(selection_bytes)
            if len({v["arm"] for v in selection["selected"].values()}) != 1:
                raise ValueError("Cần snapshot riêng cho từng model trước khi phục vụ")
            self.historical_test = evaluation["test"][self.selected_model]
            self.provenance["evaluation_sha256"] = self.manifest["evaluation"]["sha256"]
            self.provenance["dataset_manifest_sha256"] = self.manifest["dataset_manifest"]["sha256"]
            self.dataset_version = dataset["schema_version"]
        else:
            snapshot = (ROOT / "outputs/label_review/v1.0.1/manifest.json").read_bytes()
            if (
                hashlib.sha256(snapshot).hexdigest()
                != self.manifest["protocol"]["frozen_snapshot_sha256"]
            ):
                raise ValueError("Frozen manifest checksum mismatch")
            cohort = next(
                c for c in json.loads(snapshot)["cohorts"] if c["cohort"] == "vn_developer"
            )
            train_meta = cohort["files"]["train"]
            content = (ROOT / train_meta["path"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != train_meta["sha256"]:
                raise ValueError("Train snapshot checksum mismatch")
            train_sha = train_meta["sha256"]
            historical = json.loads(
                (ROOT / f"outputs/metrics/salary_{experiment}/test_metrics.json").read_text()
            )
            self.historical_test = dict(
                next(m for m in historical["metrics"] if m["model"] == self.selected_model),
                samples=cohort["files"]["test"]["rows"],
            )
            self.dataset_version = "v1.0.1"
        self.provenance["train_snapshot_sha256"] = train_sha
        self.train = pd.read_csv(io.BytesIO(content))
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
        # Recompute evidence from fitted Ridge + verified train. Never trust a mutable report CSV.
        pipeline = self.models["ridge"]
        preprocess = pipeline.named_steps["preprocess"]
        coefficient = dict(
            zip(
                preprocess.get_feature_names_out(),
                np.ravel(pipeline.named_steps["model"].coef_),
                strict=True,
            )
        )
        support = np.asarray(
            preprocess.named_transformers_["skills"].transform(self.train[["skills"]]).sum(axis=0)
        ).ravel()
        self.role_skill_support = {}
        for role, subset in self.train.groupby("role"):
            counts = np.asarray(
                preprocess.named_transformers_["skills"].transform(subset[["skills"]]).sum(axis=0)
            ).ravel()
            self.role_skill_support[role] = dict(
                zip(vectorizer.get_feature_names_out(), counts.astype(int), strict=True)
            )
        self.associations = pd.DataFrame(
            [
                dict(
                    skill=skill,
                    train_rows=int(count),
                    coefficient_vnd=coefficient["skills__" + skill],
                )
                for skill, count in zip(vectorizer.get_feature_names_out(), support, strict=True)
                if count >= 5
            ]
        ).sort_values("coefficient_vnd", ascending=False)

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
        if not np.isfinite(base[self.selected_model][0]) or base[self.selected_model][0] <= 0:
            raise ValueError("Hồ sơ ngoài phạm vi dự đoán lương dương; kiểm tra lại thông tin")
        candidates = self.associations[
            self.associations.coefficient_vnd.gt(0) & self.associations.train_rows.ge(5)
        ].to_dict("records")
        known = {s.casefold() for s in row["skills"]}
        recommendations = []
        for item in candidates:
            skill = item["skill"]
            role_support = int(self.role_skill_support.get(row["role"], {}).get(skill, 0))
            if skill in known or role_support < 5:
                continue
            changed = dict(row, skills=row["skills"] + [skill])
            delta = self.predict([changed])[self.selected_model][0] - base[self.selected_model][0]
            if delta <= 0:
                continue
            recommendations.append(
                dict(
                    skill=skill,
                    train_support=int(item["train_rows"]),
                    role_support=role_support,
                    predicted_delta_vnd=round(delta),
                    ridge_association_vnd=round(item["coefficient_vnd"]),
                )
            )
        recommendations.sort(key=lambda r: r["predicted_delta_vnd"], reverse=True)
        selected_label = "Ridge" if self.selected_model == "ridge" else "Random Forest"
        return dict(
            market_reference=market_reference(
                row["role"], row["experience_years"], base[self.selected_model][0]
            ),
            profile={k: row[k] for k in FEATURES},
            predictions={k: round(v[0]) for k, v in base.items()},
            selected_model=self.selected_model,
            warnings=row["warnings"] + self.warnings(row),
            recommendations=recommendations[:4],
            explanation=(
                "Gợi ý từ kỹ năng có ít nhất 5 mẫu train cùng vai trò và hệ số Ridge dương; "
                f"chênh lệch là dự đoán {selected_label} "
                "khi thêm một kỹ năng, "
                "không phải mức tăng lương được bảo đảm."
            ),
            evidence=dict(
                experiment_id=self.experiment,
                train_jobs=len(self.train),
                label_quality=self.label_quality,
                historical_test_mae_vnd=self.historical_test["mae_vnd"],
                historical_test_samples=self.historical_test["samples"],
                supported_experience_years=self.experience_range,
            ),
        )


@lru_cache(maxsize=1)
def salary_service():
    path = ROOT / "configs/application.json"
    config_bytes = path.read_bytes()
    service = SalaryService(json.loads(config_bytes)["salary_experiment"])
    service.provenance["deployment_config_sha256"] = hashlib.sha256(config_bytes).hexdigest()
    return service

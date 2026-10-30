"""One local inference worker, persistent progress and isolated result artifacts."""

import logging
import math
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from career_ai.data import FEATURES, UNITS, validate_profile
from career_ai.inputs import missing
from career_auto.state import read, write

from .config import BASELINE_RUN, MAX_ADVICE_ROWS, MAX_PENDING, MODEL_RUN, WEB_OUTPUT
from .repository import PLOT_LOCK, chart_urls
from .uploads import export_frame

logger = logging.getLogger(__name__)


def now():
    return datetime.now(UTC).isoformat()


def data_error(exc):
    message = str(exc)
    translated = {
        "Missing role": "Thiếu vai trò công việc.",
        "Missing location": "Thiếu khu vực hoặc quốc gia.",
        "Missing skills": "Thiếu danh sách kỹ năng.",
        "market must be international or vietnam": "Thị trường phải là vietnam hoặc international.",
        "Experience must be 0..80 years": "Kinh nghiệm phải từ 0 đến 80 năm.",
    }
    if message in translated:
        return translated[message]
    if "float()" in message or "could not convert string to float" in message:
        return "Kinh nghiệm cần là một số năm hợp lệ."
    if "context" in message.lower() or "1024" in message:
        return "Mô tả/hồ sơ vượt ngữ cảnh model; hãy rút gọn và thử lại."
    return message


class JobService:
    def __init__(self, folder=None, processor=None):
        self.folder = Path(folder or WEB_OUTPUT / "jobs")
        self.folder.mkdir(parents=True, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="career-ai")
        self.lock = threading.RLock()
        self.processor = processor or self.process_row
        self.model_loaded = False
        # A previous process cannot still own an in-process worker after restart.
        for path in self.folder.glob("*/status.json"):
            status = read(path)
            if status["status"] in ["queued", "running"]:
                status.update(
                    status="interrupted", stage="Phiên máy chủ đã dừng; hãy gửi lại tác vụ."
                )
                write(path, status)

    def list(self):
        with self.lock:
            rows = [read(p) for p in self.folder.glob("*/status.json")]
        return sorted(rows, key=lambda r: r["created_at"], reverse=True)[:20]

    def get(self, identifier):
        if len(identifier) != 32 or any(c not in "0123456789abcdef" for c in identifier):
            raise FileNotFoundError("Không tìm thấy tác vụ.")
        path = self.folder / identifier / "status.json"
        if not path.exists():
            raise FileNotFoundError("Không tìm thấy tác vụ.")
        with self.lock:
            return read(path)

    def update(self, identifier, **values):
        with self.lock:
            path = self.folder / identifier / "status.json"
            data = read(path)
            data.update(values, updated_at=now())
            write(path, data)

    def submit(self, rows, filename, include_advice=False):
        if not rows:
            raise ValueError("Không có hồ sơ để phân tích.")
        if include_advice and len(rows) > MAX_ADVICE_ROWS:
            raise ValueError(
                f"Tư vấn kỹ năng tối đa{MAX_ADVICE_ROWS} hồ sơ/lần; hãy tắt tư vấn cho file lớn."
            )
        with self.lock:
            active = sum(s["status"] in ["queued", "running"] for s in self.list())
            if active >= MAX_PENDING:
                raise OverflowError("Hàng đợi đang đầy. Vui lòng chờ tác vụ hiện tại hoàn tất.")
            identifier = uuid.uuid4().hex
            folder = self.folder / identifier
            folder.mkdir()
            write(folder / "input.json", rows)
            status = dict(
                id=identifier,
                filename=filename,
                status="queued",
                stage="Đang chờ xử lý",
                processed=0,
                total=len(rows),
                valid=0,
                errors=0,
                created_at=now(),
                updated_at=now(),
                include_advice=include_advice,
                model_version=f"llm:{MODEL_RUN.name}",
            )
            write(folder / "status.json", status)
            self.executor.submit(self.run, identifier, rows, include_advice)
            return status

    def process_row(self, row, include_advice):
        # This is the only path that loads TensorFlow/Qwen; API browsing stays lightweight.
        from career_ai.language import advise, extract
        from career_ai.models import loaded_llm, predict

        item = dict(row)
        if (
            isinstance(item.get("description"), str)
            and item["description"].strip()
            and any(missing(item.get(k)) for k in ["role", "experience_years", "skills"])
        ):
            extracted = extract(loaded_llm(MODEL_RUN)[0], item["description"])
            for key, value in extracted.items():
                if missing(item.get(key)):
                    item[key] = value
        if isinstance(item.get("experience_years"), bool):
            raise ValueError("Kinh nghiệm phải là số năm, không phải đúng/sai.")
        profile = validate_profile(item)
        if len(str(profile)) > 16000:
            raise ValueError("Hồ sơ quá dài; hãy rút gọn kỹ năng/mô tả.")
        frame = pd.DataFrame([profile])
        prediction = float(predict(frame, MODEL_RUN, "llm")[0])
        self.model_loaded = True
        baseline = float(predict(frame, BASELINE_RUN, "baseline")[0])
        if not math.isfinite(prediction) or not math.isfinite(baseline):
            raise ValueError("Model không trả mức lương hữu hạn cho hồ sơ này.")
        result = dict(
            **profile,
            prediction=prediction,
            baseline_prediction=baseline,
            unit=UNITS[profile["market"]],
            model_version=f"llm:{MODEL_RUN.name}",
        )
        if item.get("salary") is not None and item.get("unit") == result["unit"]:
            try:
                observed = float(item["salary"])
                if math.isfinite(observed) and observed > 0:
                    result.update(actual_salary=observed, absolute_error=abs(observed - prediction))
            except (TypeError, ValueError):
                pass
        if include_advice:
            try:
                result["advice"] = advise(loaded_llm(MODEL_RUN)[0], profile)
            except (ValueError, TypeError, KeyError) as exc:
                # Salary remains usable; a language failure is shown, never fabricated advice.
                result["advice"] = dict(status="error", error=str(exc), recommendations=[])
        return result

    def run(self, identifier, rows, include_advice):
        folder = self.folder / identifier
        output = []
        try:
            self.update(
                identifier, status="running", stage="Đang nạp model đã fine-tune và phân tích"
            )
            for index, row in enumerate(rows, 1):
                try:
                    result = self.processor(row, include_advice)
                    result.update(source_row=index, error=None)
                except (ValueError, TypeError, KeyError, OverflowError) as exc:
                    result = dict(source_row=index, error=data_error(exc), prediction=None)
                output.append(result)
                good = sum(r.get("error") is None for r in output)
                self.update(
                    identifier,
                    processed=index,
                    valid=good,
                    errors=index - good,
                    stage=f"Đã phân tích {index}/{len(rows)} hồ sơ",
                )
            self.update(identifier, stage="Đang tổng hợp nhận định và vẽ biểu đồ")
            frame = pd.DataFrame(output)
            export_frame(frame.drop(columns=["advice"], errors="ignore")).to_csv(
                folder / "predictions.csv", index=False, encoding="utf-8-sig"
            )
            export_frame(frame.drop(columns=["advice"], errors="ignore")).to_excel(
                folder / "predictions.xlsx", index=False
            )
            write(folder / "predictions.json", output)
            valid = frame[frame.error.isna()] if "error" in frame else frame.iloc[:0]
            markets = []
            if not valid.empty:
                from career_auto.charts import charts

                with PLOT_LOCK:
                    charts(valid[FEATURES + ["prediction"]], folder / "figures")
                for market, group in valid.groupby("market"):
                    markets.append(
                        dict(
                            market=market,
                            unit=UNITS[market],
                            samples=len(group),
                            median_prediction=float(group.prediction.median()),
                            min_prediction=float(group.prediction.min()),
                            max_prediction=float(group.prediction.max()),
                            charts=chart_urls(f"/api/jobs/{identifier}/charts", market),
                        )
                    )
            comparison = {}
            if not valid.empty and "actual_salary" in valid:
                from career_ai.evaluation import metrics

                labelled = valid[valid.actual_salary.notna()].copy()
                if not labelled.empty:
                    labelled["salary"] = labelled.actual_salary
                    comparison = metrics(labelled, labelled.prediction.to_numpy())
            summary = dict(
                rows=output,
                markets=markets,
                comparison=comparison,
                notes=[
                    "Thu nhập dự đoán là ước tính; đơn vị từng thị trường được giữ riêng.",
                    "Thống kê kỹ năng là liên hệ quan sát, không bảo đảm tăng lương.",
                    "Đối chiếu thu nhập chỉ khi bạn xác nhận đơn vị; không dùng để train.",
                ],
            )
            write(folder / "results.json", summary)
            self.update(
                identifier, status="completed", stage="Phân tích hoàn tất", finished_at=now()
            )
        except Exception:
            logger.exception("Analysis job failed: %s", identifier)
            self.update(
                identifier,
                status="failed",
                stage="Không thể hoàn tất tác vụ; xem log máy chủ.",
                error="Lỗi xử lý model hoặc file đầu ra. Dữ liệu gốc và trọng số được giữ nguyên.",
            )

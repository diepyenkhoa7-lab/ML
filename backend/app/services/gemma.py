"""Isolated, inference-only MLX worker; adapter never follows an unvalidated new run."""

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from backend.app.services.contracts import GemmaBatch, strict_json
from backend.app.services.data import ROOT
from scripts.gpu_lock import gpu_is_busy

ADAPTER = "adapters/gemma-jobs/20261017T105728Z"
CONTEXT_LIMIT = 2048


def availability():
    ready = (ROOT / "models/gemma-mlx-4bit/model.safetensors").is_file() and (
        ROOT / ADAPTER / "adapters.safetensors"
    ).is_file()
    check_error = False
    try:
        process = subprocess.run(["pgrep", "-f", r"mlx_lm.*lora"], capture_output=True, timeout=3)
        check_error = process.returncode not in {0, 1} or bool(process.stderr.strip())
        busy = process.returncode == 0 or check_error
    except (OSError, subprocess.TimeoutExpired):
        busy = check_error = True
    try:
        gpu_busy = gpu_is_busy()
    except OSError:
        gpu_busy = check_error = True
    return dict(
        available=ready,
        training_active=busy,
        training_check_error=check_error,
        gpu_busy=gpu_busy,
        adapter=ADAPTER,
        scope="job_card_extraction; inference only",
        max_rows=20,
        max_context=CONTEXT_LIMIT,
    )


def extract_cards(cards, audit_folder=None):
    if not cards or any(not isinstance(card, str) for card in cards):
        raise ValueError("Cần ít nhất một mô tả dạng văn bản")
    request_id = uuid.uuid4().hex
    status = availability()
    if not status["available"]:
        raise ValueError("Chưa có trọng số Gemma trên máy này; xem hướng dẫn tải model")
    if status.get("training_check_error"):
        raise ValueError("Không kiểm tra được trạng thái GPU; chạy app từ Terminal và thử lại")
    if status["training_active"]:
        raise ValueError("Gemma đang train trên GPU; chờ hoàn tất rồi chạy trích xuất")
    if status.get("gpu_busy"):
        raise ValueError("GPU đang đánh giá hoặc suy luận Gemma; chờ lượt hiện tại hoàn tất")
    if len(cards) > 20:
        raise ValueError("Mỗi lượt Gemma tối đa 20 mô tả; tách file hoặc dùng các cột có sẵn")
    with tempfile.TemporaryDirectory(prefix="career-gemma-") as temporary:
        folder = Path(temporary)
        source, target = folder / "input.json", folder / "output.json"
        source.write_text(json.dumps(dict(request_id=request_id, cards=cards), ensure_ascii=False))
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/app_gemma_extract.py"),
                    "--input",
                    str(source),
                    "--output",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            save_diagnostic(audit_folder, request_id, "timeout", exc.stdout, exc.stderr)
            raise ValueError("Gemma vượt 300 giây; giảm số dòng/mô tả và thử lại") from exc
        save_diagnostic(audit_folder, request_id, result.returncode, result.stdout, result.stderr)
        if result.returncode or not target.exists():
            raise ValueError(
                "Gemma không thực hiện được suy luận; kiểm tra trọng số/Metal và thử lại"
            )
        try:
            payload = strict_json(target.read_text())
            batch = GemmaBatch.model_validate(payload).check_request(request_id, cards)
        except (ValueError, TypeError) as exc:
            if audit_folder:
                (Path(audit_folder) / "gemma_invalid_transport.txt").write_text(target.read_text())
            raise ValueError("Phản hồi Gemma sai hợp đồng; xem log riêng của job") from exc
        return batch.model_dump()


def save_diagnostic(folder, request_id, returncode, stdout, stderr):
    if folder:

        def safe(value):
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            return (value or "")[-32000:]

        (Path(folder) / "gemma_worker.json").write_text(
            json.dumps(
                dict(
                    request_id=request_id,
                    returncode=returncode,
                    stdout=safe(stdout),
                    stderr=safe(stderr),
                ),
                ensure_ascii=False,
                indent=2,
            )
        )

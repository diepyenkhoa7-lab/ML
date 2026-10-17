"""Isolated, inference-only MLX worker; adapter never follows an unvalidated new run."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from backend.app.services.data import ROOT

ADAPTER = "adapters/gemma-jobs/20261017T105728Z"


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
    return dict(
        available=ready,
        training_active=busy,
        training_check_error=check_error,
        adapter=ADAPTER,
        scope="job_card_extraction; inference only",
        max_rows=20,
    )


def extract_cards(cards):
    status = availability()
    if not status["available"]:
        raise ValueError("Chưa có trọng số Gemma trên máy này; xem hướng dẫn tải model")
    if status.get("training_check_error"):
        raise ValueError("Không kiểm tra được trạng thái GPU; chạy app từ Terminal và thử lại")
    if status["training_active"]:
        raise ValueError("Gemma đang train trên GPU; chờ hoàn tất rồi chạy trích xuất")
    if len(cards) > 20:
        raise ValueError("Mỗi lượt Gemma tối đa 20 mô tả; tách file hoặc dùng các cột có sẵn")
    with tempfile.TemporaryDirectory(prefix="career-gemma-") as temporary:
        folder = Path(temporary)
        source, target = folder / "input.json", folder / "output.json"
        source.write_text(json.dumps(cards, ensure_ascii=False))
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
            raise ValueError("Gemma vượt 300 giây; giảm số dòng/mô tả và thử lại") from exc
        if result.returncode or not target.exists():
            raise ValueError(
                "Gemma không thực hiện được suy luận; kiểm tra trọng số/Metal và thử lại"
            )
        return json.loads(target.read_text())

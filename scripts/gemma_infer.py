"""Smoke test suy luận text cho model Google đã chuyển MLX; không phải benchmark."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402
from scripts.prepare_gemma_sft import SYSTEM, validate_label  # noqa: E402

os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=ROOT / "models/gemma-mlx-4bit")
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/environment/gemma_base.json")
    parser.add_argument(
        "--prompt",
        default=(
            "Phiếu tin tuyển dụng từ dữ liệu đã thu thập:\n"
            "Chức danh: Backend Developer\nĐịa điểm: Hà Nội\nKinh nghiệm: 3 năm\n"
            "Kỹ năng: Python, FastAPI, PostgreSQL\nLương: 20–30 triệu VND/tháng"
        ),
    )
    args = parser.parse_args()
    if not (args.model / "manifest.json").exists():
        raise SystemExit("Chưa có model/manifest. Chạy scripts/download_gemma.py --convert trước.")
    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    mx.random.seed(42)
    start = time.perf_counter()
    model, tokenizer = load(
        str(args.model), adapter_path=str(args.adapter) if args.adapter else None
    )
    prompt = tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": args.prompt}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    text = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=args.max_tokens,
        sampler=make_sampler(temp=0.0),
        verbose=True,
    )
    try:
        extracted = json.loads(text.strip())
    except ValueError:
        extracted = None
    schema_error = None
    try:
        if not isinstance(extracted, dict):
            raise ValueError("Expected JSON object")
        validate_label(extracted)
    except (ValueError, TypeError) as exc:
        schema_error = str(exc)
    result = {
        "source_model": "google/gemma-4-E4B-it",
        "manifest": json.loads((args.model / "manifest.json").read_text()),
        "adapter": str(args.adapter) if args.adapter else None,
        "adapter_sha256": checksum(args.adapter / "adapters.safetensors") if args.adapter else None,
        "system_prompt": SYSTEM,
        "prompt": args.prompt,
        "output": text,
        "json_valid": isinstance(extracted, dict),
        "schema_valid": schema_error is None,
        "schema_error": schema_error,
        "gemma_training_started_by_this_command": False,
        "elapsed_seconds_including_load": time.perf_counter() - start,
        "peak_memory_bytes": mx.get_peak_memory(),
        "scope": "single synthetic prompt, not a quality evaluation",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved: {args.output}; JSON valid: {result['json_valid']}")


if __name__ == "__main__":
    main()

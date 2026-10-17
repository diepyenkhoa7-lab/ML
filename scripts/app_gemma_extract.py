"""App worker: strict JSON extraction only, no training or output repair."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.gemma import ADAPTER  # noqa: E402
from scripts.prepare_gemma_sft import SYSTEM, validate_label  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cards = json.loads(args.input.read_text())
    if not isinstance(cards, list) or not 1 <= len(cards) <= 20:
        raise ValueError("Expected 1–20 job cards")
    adapter = ROOT / ADAPTER
    manifest = json.loads((adapter / "manifest.json").read_text())
    if (
        hashlib.sha256((adapter / "adapters.safetensors").read_bytes()).hexdigest()
        != manifest["adapter"]["sha256"]
    ):
        raise ValueError("Adapter checksum mismatch")
    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    mx.random.seed(42)
    model, tokenizer = load(str(ROOT / "models/gemma-mlx-4bit"), adapter_path=str(adapter))
    output = []
    for card in cards:
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": card}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        if len(tokenizer.encode(prompt)) + 256 > 1024:
            output.append(
                dict(
                    value=None,
                    raw_output=None,
                    error="Mô tả vượt context 1.024 token; cần rút gọn, chưa cắt tự động",
                )
            )
            continue
        raw = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=256,
            sampler=make_sampler(temp=0.0),
            verbose=False,
        )
        try:
            value = json.loads(raw.strip())
            if not isinstance(value, dict):
                raise ValueError("Không phải JSON object")
            validate_label(value)
            output.append(dict(value=value, raw_output=raw, error=None))
        except (ValueError, TypeError) as exc:
            output.append(
                dict(value=None, raw_output=raw, error=f"JSON/schema không hợp lệ: {exc}")
            )
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

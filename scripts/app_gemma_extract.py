"""App worker: strict JSON extraction only, no training or output repair."""

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.contracts import GemmaBatch, GemmaLabel, digest, strict_json  # noqa: E402
from backend.app.services.gemma import ADAPTER  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402
from scripts.gpu_lock import gpu_lock  # noqa: E402
from scripts.prepare_gemma_sft import SYSTEM  # noqa: E402


def extract_card_items(cards, tokenizer, model, generate, sampler):
    """Reuse exact duplicate inputs within one request, preserving every row's identity."""
    output, cache = [], {}
    generation_calls = 0
    for index, card in enumerate(cards):
        if card in cache:
            output.append(dict(cache[card], index=index))
            continue
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": card}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        item = dict(index=index, input_sha256=digest(card), value=None, raw_output=None, error=None)
        if len(tokenizer.encode(prompt)) + 256 > 1024:
            item["error"] = "Mô tả vượt context 1.024 token; cần rút gọn, chưa cắt tự động"
        else:
            raw = generate(
                model, tokenizer, prompt=prompt, max_tokens=256, sampler=sampler, verbose=False
            )
            generation_calls += 1
            item["raw_output"] = raw
            try:
                item["value"] = GemmaLabel.model_validate(strict_json(raw.strip())).model_dump()
            except (ValueError, TypeError) as exc:
                item["error"] = f"JSON/schema không hợp lệ: {exc}"
        cache[card] = item
        output.append(item)
    return output, dict(
        unique_cards=str(len(cache)),
        reused_rows=str(len(cards) - len(cache)),
        generation_calls=str(generation_calls),
        reuse_policy="exact input text, within this request only; no persistent input cache",
    )


def run(args):
    request = strict_json(args.input.read_text())
    cards = request["cards"]
    if (
        not isinstance(cards, list)
        or not 1 <= len(cards) <= 20
        or any(not isinstance(card, str) for card in cards)
    ):
        raise ValueError("Expected 1–20 text job cards")
    adapter = ROOT / ADAPTER
    adapter_sha = checksum(adapter / "adapters.safetensors")
    manifest = strict_json((adapter / "manifest.json").read_text())
    if adapter_sha != manifest["adapter"]["sha256"]:
        raise ValueError("Adapter checksum mismatch")
    base = ROOT / "models/gemma-mlx-4bit"
    base_sha = checksum(base / "model.safetensors")
    evidence = strict_json((ROOT / "outputs/gemma_preparation/weights.json").read_text())
    if base_sha != evidence["weights"][base.name]["sha256"]:
        raise ValueError("Base model checksum mismatch")
    provenance = {
        "adapter": ADAPTER,
        "adapter_sha256": adapter_sha,
        "base_weight_sha256": base_sha,
        "base_manifest_sha256": checksum(base / "manifest.json"),
        "system_prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "generation": "temperature=0; seed=42; max_tokens=256; context=1024; thinking=false",
    }
    for name in ["config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"]:
        if (base / name).is_file():
            provenance[name + "_sha256"] = checksum(base / name)
    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    mx.random.seed(42)
    model, tokenizer = load(str(base), adapter_path=str(adapter))
    output, reuse = extract_card_items(cards, tokenizer, model, generate, make_sampler(temp=0.0))
    provenance.update(reuse)
    batch = GemmaBatch(
        schema_version="career.gemma.batch.v1",
        request_id=request["request_id"],
        items=output,
        provenance=provenance,
    ).check_request(request["request_id"], cards)
    args.output.write_text(batch.model_dump_json(indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with gpu_lock():
        run(args)


if __name__ == "__main__":
    main()

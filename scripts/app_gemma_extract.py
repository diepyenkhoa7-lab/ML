"""App worker: strict JSON extraction only, no training or output repair."""

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.contracts import GemmaBatch, GemmaLabel, digest, strict_json  # noqa: E402
from backend.app.services.gemma import ADAPTER, CONTEXT_LIMIT  # noqa: E402
from scripts.clean_data import checksum  # noqa: E402
from scripts.gpu_lock import gpu_lock  # noqa: E402
from scripts.prepare_gemma_sft import SYSTEM  # noqa: E402

RETRY = (
    "JSON vừa trả chưa đúng schema. Đọc lại tin ở trên và trả lại đủ 8 khóa JSON, "
    "không giải thích. Trong skills, mỗi công nghệ chỉ xuất hiện một lần; "
    "chỉ nêu tên công nghệ, không liệt kê chức năng/công việc. "
    "Giữ null cho thông tin thiếu; không tự tạo số liệu."
)


def extract_card_items(cards, tokenizer, model, generate, sampler, context_limit=1024):
    """Reuse exact duplicate inputs within one request, preserving every row's identity."""
    output, cache = [], {}
    if context_limit not in {1024, 2048, 4096}:
        raise ValueError("Unsupported serving context budget")
    generation_calls = schema_retries = 0
    for index, card in enumerate(cards):
        if card in cache:
            output.append(dict(cache[card], index=index))
            continue
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": card}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        item = dict(
            index=index,
            input_sha256=digest(card),
            value=None,
            raw_output=None,
            error=None,
            attempts=[],
        )
        if len(tokenizer.encode(prompt)) + 256 > context_limit:
            item["error"] = (
                f"Mô tả vượt context {context_limit:,} token; cần rút gọn, chưa cắt tự động"
            )
        else:
            for attempt in range(2):
                raw = generate(
                    model, tokenizer, prompt=prompt, max_tokens=256, sampler=sampler, verbose=False
                )
                generation_calls += 1
                schema_retries += int(attempt == 1)
                item["raw_output"] = raw
                item["attempts"].append(raw)
                try:
                    item["value"] = GemmaLabel.model_validate(strict_json(raw.strip())).model_dump()
                    item["error"] = None
                    break
                except (ValueError, TypeError):
                    item["error"] = "Gemma trả JSON/schema chưa hợp lệ; xem đầu ra gốc của dòng này"
                    messages += [
                        dict(role="assistant", content=raw),
                        dict(role="user", content=RETRY),
                    ]
                    prompt = tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
                    )
                    if len(tokenizer.encode(prompt)) + 256 > context_limit:
                        break
        cache[card] = item
        output.append(item)
    return output, dict(
        unique_cards=str(len(cache)),
        reused_rows=str(len(cards) - len(cache)),
        generation_calls=str(generation_calls),
        schema_retries=str(schema_retries),
        retry_policy=(
            "at most one schema-failure model retry per unique input; raw attempts retained"
        ),
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
    native_config = strict_json((base / "config.json").read_text())
    native_context = native_config.get("text_config", native_config)["max_position_embeddings"]
    if args.max_context > native_context:
        raise ValueError("Requested context exceeds the local model configuration")
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
        "generation": (
            f"temperature=0; seed=42; max_tokens=256; context={args.max_context}; thinking=false"
        ),
        "input_policy": "complete input; no truncation or source-sentence deletion",
    }
    for name in ["config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"]:
        if (base / name).is_file():
            provenance[name + "_sha256"] = checksum(base / name)
    import mlx.core as mx
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler

    mx.random.seed(42)
    model, tokenizer = load(str(base), adapter_path=str(adapter))
    output, reuse = extract_card_items(
        cards, tokenizer, model, generate, make_sampler(temp=0.0), args.max_context
    )
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
    parser.add_argument(
        "--max-context", type=int, choices=[1024, 2048, 4096], default=CONTEXT_LIMIT
    )
    args = parser.parse_args()
    with gpu_lock():
        run(args)


if __name__ == "__main__":
    main()

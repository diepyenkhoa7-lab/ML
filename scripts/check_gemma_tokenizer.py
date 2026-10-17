"""Kiểm tra chat template/tokenizer Google đã tải; không cần weights hoặc GPU."""

import json
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]


def main():
    model_path = ROOT / "models/gemma-source"
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    result = {"model": "google/gemma-4-E4B-it", "weights_required": False, "splits": {}}
    for path in sorted((ROOT / "data/examples/finetune").glob("*.jsonl")):
        lengths = []
        for line in path.read_text().splitlines():
            messages = json.loads(line)["messages"]
            tokens = tokenizer.apply_chat_template(
                messages,
                enable_thinking=False,
                return_dict=False,
            )
            prompt_tokens = tokenizer.apply_chat_template(
                messages[:-1],
                enable_thinking=False,
                add_generation_prompt=True,
                return_dict=False,
            )
            assert 0 < len(prompt_tokens) < len(tokens) <= 512
            assert tokens[: len(prompt_tokens)] == prompt_tokens, "Mask prompt không khớp"
            lengths.append(len(tokens))
        assert lengths, f"Không có mẫu: {path}"
        result["splits"][path.stem] = {"count": len(lengths), "max_tokens": max(lengths)}
    assert len(result["splits"]) == 3
    result["ok"] = True
    output = ROOT / "outputs/environment/tokenizer_check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

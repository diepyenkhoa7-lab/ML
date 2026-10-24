"""Real pretrained Vietnamese generation check, before any adapter training."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def check():
    import numpy as np

    from career_ai.data import ROOT, write
    from career_ai.language import chat_prompt
    from career_ai.models import qwen_load

    started = time.monotonic()
    model = qwen_load()
    text = chat_prompt(
        "Trích xuất thành JSON với role, experience_years, skills: "
        "Tuyển Backend Developer tại Hà Nội, kinh nghiệm 3 năm, biết Python và SQL."
    )
    size = int(np.asarray(model.preprocessor.tokenizer(text)).size)
    generated = str(model.generate(text, max_length=size + 128, strip_prompt=True))
    answer = generated.strip().removesuffix("<|im_end|>").strip()
    if not answer:
        raise ValueError("Pretrained generation produced no answer")
    schema_valid = False
    try:
        value = json.loads(answer)
        schema_valid = isinstance(value, dict) and set(value) == {
            "role",
            "experience_years",
            "skills",
        }
    except ValueError:
        pass
    write(
        ROOT / "outputs/qwen_pretrained_check.json",
        dict(
            source="pinned_pretrained_no_adapter",
            answer=answer,
            json_keys_valid=schema_valid,
            elapsed_seconds=time.monotonic() - started,
            note="Single compatibility probe, not a generalization metric.",
        ),
    )
    print("Pretrained Vietnamese generation completed", flush=True)


check()

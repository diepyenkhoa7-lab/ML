"""Resume a pinned official Keras preset; base weights stay outside source Git."""

import json
from pathlib import Path

from huggingface_hub import snapshot_download

root = Path(__file__).resolve().parents[1]
manifest_path = root / "configs/qwen_source.json"
manifest = json.loads(manifest_path.read_text())
path = snapshot_download(
    repo_id=manifest["repo"],
    revision=manifest["revision"],
    local_dir=root / manifest["local_path"],
    max_workers=2,
)
manifest["download_complete"] = True
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print(path)

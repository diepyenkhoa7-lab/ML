"""Download pinned public raw files; never overwrite a mismatching existing raw file."""

import hashlib
import json
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "configs/data_sources.json").read_text())
for item in manifest["files"]:
    path = root / item["path"]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".partial")
        urllib.request.urlretrieve(item["url"], temporary)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Downloaded checksum mismatch: {path.name}")
        temporary.rename(path)
    elif hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError(f"Existing raw checksum mismatch: {path.name}")
    print("Verified", item["path"], flush=True)

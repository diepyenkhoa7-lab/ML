"""Optional resumable parallel HTTP download of the pinned public Keras weights."""

import hashlib
import json
import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from huggingface_hub import get_hf_file_metadata, hf_hub_url, snapshot_download

root = Path(__file__).resolve().parents[1]
manifest_path = root / "configs/qwen_source.json"
manifest = json.loads(manifest_path.read_text())
url = hf_hub_url(manifest["repo"], "model.weights.h5", revision=manifest["revision"])
metadata = get_hf_file_metadata(url)
cache = root / ".cache/qwen-ranges" / metadata.etag
cache.mkdir(parents=True, exist_ok=True)
chunk_size = 32 * 1024 * 1024


def chunk(index):
    start = index * chunk_size
    stop = min(start + chunk_size, metadata.size) - 1
    expected = stop - start + 1
    path = cache / f"{index:04d}.part"
    for attempt in range(5):
        size = path.stat().st_size if path.exists() else 0
        if size == expected:
            return path
        if size > expected:
            raise ValueError("Oversized download part")
        try:
            location = metadata.location if attempt == 0 else get_hf_file_metadata(url).location
            request = urllib.request.Request(
                location, headers={"Range": f"bytes={start + size}-{stop}"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                required = f"bytes {start + size}-{stop}/{metadata.size}"
                if response.status != 206 or response.headers.get("Content-Range") != required:
                    raise ValueError("Server did not honor exact byte range")
                with path.open("ab") as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
            if path.stat().st_size != expected:
                raise ValueError("Incomplete download part")
            return path
        except (OSError, ValueError):
            if attempt == 4:
                raise
            time.sleep(2)


snapshot_download(
    repo_id=manifest["repo"],
    revision=manifest["revision"],
    local_dir=root / manifest["local_path"],
    ignore_patterns=["model.weights.h5"],
)
count = (metadata.size + chunk_size - 1) // chunk_size
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(chunk, i) for i in range(count)]
    for complete, future in enumerate(as_completed(futures), 1):
        future.result()
        print(f"Verified size of part {complete}/{count}", flush=True)
        (cache / "progress.json").write_text(json.dumps(dict(completed=complete, total=count)))
destination = root / manifest["local_path"] / "model.weights.h5"
temporary = destination.with_suffix(".assembling")
hash_value = hashlib.sha256()
with temporary.open("wb") as output:
    for i in range(count):
        with (cache / f"{i:04d}.part").open("rb") as source:
            while block := source.read(4 * 1024 * 1024):
                hash_value.update(block)
                output.write(block)
if hash_value.hexdigest() != metadata.etag:
    raise ValueError("Complete weight SHA256 mismatch")
temporary.replace(destination)
manifest.update(download_complete=True, sha256=hash_value.hexdigest(), bytes=metadata.size)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
shutil.rmtree(cache)
print("Pinned Qwen weights downloaded and SHA256 verified", flush=True)

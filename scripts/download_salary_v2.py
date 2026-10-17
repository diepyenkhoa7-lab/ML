"""Download the pinned academic dataset without Git-tracking its 280 MiB base file."""

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.clean_data import checksum  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    folder = ROOT / "data/raw/tinixai_2026"
    manifest = json.loads((folder / "manifest.json").read_text())
    for name, item in manifest["files"].items():
        path = folder / name
        if path.exists() and checksum(path) == item["sha256"]:
            print(name, "already verified", flush=True)
            continue
        temporary = path.with_suffix(path.suffix + ".part")
        with requests.get(item["url"], stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()
            with temporary.open("wb") as target:
                for chunk in response.iter_content(1024 * 1024):
                    target.write(chunk)
        if temporary.stat().st_size != item["bytes"] or checksum(temporary) != item["sha256"]:
            raise ValueError("Download checksum/size mismatch; original file preserved")
        temporary.replace(path)
        print(name, "downloaded and verified", flush=True)


if __name__ == "__main__":
    main()

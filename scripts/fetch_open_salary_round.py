"""Download immutable public salary snapshots; verify bytes and SHA, never train."""

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configs/open_salary_sources_20261018.json"


def matches(path, item):
    return (
        path.is_file()
        and path.stat().st_size == item["bytes"]
        and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    for source in json.loads(CATALOG.read_text())["sources"]:
        for item in source["files"]:
            path = ROOT / item["path"]
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError("Unsafe snapshot path")
            if matches(path, item):
                print("VERIFIED", item["path"])
                continue
            if args.verify_only:
                raise ValueError("Missing or changed snapshot: " + item["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".part")
            try:
                with (
                    os.fdopen(descriptor, "wb") as out,
                    urllib.request.urlopen(item["url"], timeout=60) as response,
                ):
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
                if not matches(Path(temporary), item):
                    raise ValueError("Downloaded snapshot checksum mismatch: " + item["path"])
                os.replace(temporary, path)
                print("DOWNLOADED", item["path"])
            finally:
                Path(temporary).unlink(missing_ok=True)


if __name__ == "__main__":
    main()

"""Tải các nguồn đã kiểm tra, giữ nguyên raw và ghi URL, phiên bản, SHA-256."""

import argparse
import hashlib
import json
import shutil
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parallel_remainder(spec, partial, total_size):
    offset = partial.stat().st_size if partial.exists() else 0
    workers = int(spec.get("parallel_ranges", 1))
    if workers < 2 or total_size - offset < 8 * 1024 * 1024:
        return
    staging = partial.with_name(partial.name + "s")
    staging.mkdir(exist_ok=True)
    chunk_size = (total_size - offset + workers - 1) // workers
    ranges = [
        (start, min(start + chunk_size, total_size) - 1)
        for start in range(offset, total_size, chunk_size)
    ]

    def fetch_range(bounds):
        start, end = bounds
        target = staging / f"{start}-{end}.part"
        for attempt in range(6):
            received = target.stat().st_size if target.exists() else 0
            if received == end - start + 1:
                return target
            actual_start = start + received
            headers = {"Accept-Encoding": "identity", "Range": f"bytes={actual_start}-{end}"}
            try:
                with requests.get(
                    spec["url"], headers=headers, stream=True, timeout=(30, 60)
                ) as response:
                    response.raise_for_status()
                    expected_range = f"bytes {actual_start}-{end}/{total_size}"
                    if (
                        response.status_code != 206
                        or response.headers.get("Content-Range") != expected_range
                    ):
                        raise ValueError("Máy chủ không trả đoạn byte được yêu cầu")
                    with target.open("ab") as stream:
                        for chunk in response.iter_content(128 * 1024):
                            if chunk:
                                stream.write(chunk)
                if target.stat().st_size != end - start + 1:
                    raise requests.exceptions.ChunkedEncodingError("Đoạn byte chưa đầy đủ")
                print(f"Completed range {start}-{end} of {partial.name}", flush=True)
                return target
            except requests.RequestException:
                if attempt == 5:
                    raise
                time.sleep(min(2**attempt, 5))
        raise RuntimeError("Không tải đủ đoạn byte")

    print(f"Parallel resume {partial.name}: {offset:,}/{total_size:,} bytes", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parts = list(pool.map(fetch_range, ranges))
    with partial.open("ab") as output:
        for part in parts:
            with part.open("rb") as stream:
                shutil.copyfileobj(stream, output)
    for part in parts:
        part.unlink()
    staging.rmdir()


def download(spec, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected_hash = spec.get("expected_sha256")
    expected_size = spec.get("expected_bytes")
    if spec.get("local_path") and not destination.exists():
        shutil.copy2(spec["local_path"], destination)
    if destination.exists():
        digest = sha256(destination)
        if expected_size and destination.stat().st_size != expected_size:
            raise ValueError(f"File đã tồn tại sai kích thước: {destination}")
        if expected_hash and digest != expected_hash:
            raise ValueError(f"File đã tồn tại sai checksum: {destination}")
        return {
            "path": str(destination.relative_to(ROOT)),
            "url": spec.get("url"),
            "original_path": spec.get("local_path"),
            "bytes": destination.stat().st_size,
            "sha256": digest,
            "reused": True,
        }
    partial = destination.with_name(destination.name + ".part")
    start = time.monotonic()
    if expected_size:
        parallel_remainder(spec, partial, expected_size)
    resolved_host = None
    for attempt in range(8):
        offset = partial.stat().st_size if partial.exists() else 0
        if expected_size and offset == expected_size:
            break
        headers = {"Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        try:
            with requests.get(
                spec["url"], headers=headers, stream=True, timeout=(30, 90)
            ) as response:
                response.raise_for_status()
                mode = "wb"
                if response.status_code == 206:
                    if not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                        raise ValueError("Content-Range không khớp vị trí tải tiếp")
                    mode = "ab"
                resolved_host = response.url.split("/")[2]
                with partial.open(mode) as stream:
                    for chunk in response.iter_content(256 * 1024):
                        if chunk:
                            stream.write(chunk)
                if expected_size and partial.stat().st_size != expected_size:
                    raise requests.exceptions.ChunkedEncodingError("Chưa đủ số byte")
                break
        except requests.RequestException as exc:
            current = partial.stat().st_size if partial.exists() else 0
            print(
                f"Retry {attempt + 1}/8 {destination.name}: {current:,} bytes; "
                f"{type(exc).__name__}",
                flush=True,
            )
            if attempt == 7:
                raise
            time.sleep(min(2**attempt, 10))
    digest = sha256(partial)
    if expected_size and partial.stat().st_size != expected_size:
        raise ValueError(f"Sai kích thước: {destination}")
    if expected_hash and digest != expected_hash:
        raise ValueError(f"Sai checksum: {destination}")
    if destination.suffix == ".csv":
        with partial.open("rb") as stream:
            first_line = stream.readline(2048).decode(errors="replace")
        if "git-lfs.github.com/spec" in first_line or "<html" in first_line.lower():
            raise ValueError(f"URL không trả CSV: {spec['url']}")
    partial.replace(destination)
    return {
        "path": str(destination.relative_to(ROOT)),
        "url": spec["url"],
        "resolved_host": resolved_host,
        "bytes": destination.stat().st_size,
        "sha256": digest,
        "download_seconds": round(time.monotonic() - start, 2),
    }


def fetch_source(source):
    folder = ROOT / "data/raw" / source["id"]
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {k: v for k, v in source.items() if k != "files"}
    manifest.update(retrieved_at_utc=datetime.now(timezone.utc).isoformat(), files=[], errors=[])
    for spec in source["files"]:
        try:
            print(f"Downloading {source['id']}/{spec['path']}", flush=True)
            result = download(spec, folder / spec["path"])
            manifest["files"].append(result)
            print(f"Verified {result['path']} ({result['bytes']:,} bytes)", flush=True)
            if spec["path"].endswith(".zip"):
                with zipfile.ZipFile(folder / spec["path"]) as archive:
                    bad = archive.testzip()
                    if bad:
                        raise ValueError(f"ZIP CRC sai: {bad}")
                    extracted = folder / "extracted"
                    for member in archive.infolist():
                        target = (extracted / member.filename).resolve()
                        if not target.is_relative_to(extracted.resolve()):
                            raise ValueError("ZIP có đường dẫn ngoài thư mục đích")
                    archive.extractall(extracted)
                    manifest["archive_members"] = archive.namelist()
        except Exception as exc:
            manifest["errors"].append({"file": spec["path"], "error": str(exc)})
            print(f"ERROR {source['id']}/{spec['path']}: {exc}", flush=True)
        (folder / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
    return source["id"], not manifest["errors"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="ID một nguồn; mặc định tải tất cả")
    args = parser.parse_args()
    sources = json.loads((ROOT / "configs/data_sources.json").read_text())["sources"]
    if args.source:
        sources = [source for source in sources if source["id"] == args.source]
        if not sources:
            parser.error("Không có source ID này")
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(fetch_source, source) for source in sources]):
            key, ok = future.result()
            results[key] = ok
    print(json.dumps(results, indent=2))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

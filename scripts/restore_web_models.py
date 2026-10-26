"""Restore only the selected models/metrics from the verified delivery archive."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def restore(archive, check_only=False):
    expected = json.loads((ROOT / "docs/DELIVERY_MANIFEST.json").read_text())["sha256"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Checksum gói không khớp bản đã bàn giao; không nạp trọng số.")
    model = ROOT / "outputs/qwen_20261023T082631"
    baseline = ROOT / "outputs/baseline_20261023T082631"
    mapping = {
        **{
            f"model/{name}": model / name
            for name in [
                "qwen.lora.h5",
                "salary_head.keras",
                "llm.json",
                "lineage.json",
                "llm_history.json",
                "reload_probe.json",
                "fresh_process_reload.json",
            ]
        },
        **{
            f"baseline/{name}": baseline / name
            for name in ["baseline.keras", "baseline.json", "vocabulary.json"]
        },
        **{
            f"results/{name}": model / name
            for name in [
                "llm_valid_metrics.json",
                "llm_test_metrics.json",
                "language_valid.json",
                "language_test.json",
            ]
        },
        **{
            f"results/{name}": baseline / name
            for name in ["baseline_valid_metrics.json", "baseline_test_metrics.json"]
        },
    }
    contents = {}
    with ZipFile(archive) as z:
        prefixes = [
            n.rsplit("/", 1)[0]
            for n in z.namelist()
            if n.count("/") == 1 and n.endswith("/manifest.json")
        ]
        if len(prefixes) != 1:
            raise ValueError("Cấu trúc gói không hợp lệ.")
        prefix = prefixes[0]
        manifest = json.loads(z.read(prefix + "/manifest.json"))
        for name, target in mapping.items():
            content = z.read(prefix + "/" + name)
            checksum = manifest["files"][name]["sha256"]
            if hashlib.sha256(content).hexdigest() != checksum:
                raise ValueError(f"Artifact không khớp: {name}")
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != checksum:
                raise ValueError(f"File đang có khác bản bàn giao, không ghi đè: {target}")
            contents[target] = content
    if not check_only:
        for target, content in contents.items():
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + ".restoring")
                temporary.write_bytes(content)
                temporary.replace(target)
    print(
        f"Đã kiểm {len(contents)} file model/metric; "
        + ("chưa thay đổi file." if check_only else "đã khôi phục các file còn thiếu.")
    )
    print("Backbone Qwen tải riêng bằng scripts/download_qwen.py nếu chưa có.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive", type=Path, default=ROOT / "outputs/delivery/qwen_salary_demo_20261025.zip"
    )
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    restore(args.archive, args.check_only)

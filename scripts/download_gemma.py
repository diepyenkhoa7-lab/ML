"""Tải model Google chính thức, cố định commit; tùy chọn chuyển nhánh text sang MLX 4-bit."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))


def main():
    from huggingface_hub import HfApi, snapshot_download

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="main")
    parser.add_argument("--convert", action="store_true", help="Chuyển sang MLX 4-bit sau khi tải")
    parser.add_argument(
        "--info-only", action="store_true", help="Chỉ xem metadata, không tải weights"
    )
    args = parser.parse_args()
    repo_id = "google/gemma-4-E4B-it"
    info = HfApi().model_info(repo_id, revision=args.revision, files_metadata=True)
    model_dir = ROOT / "models/gemma-source"
    manifest_path = model_dir / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous["repo_id"] != repo_id or previous["revision"] != info.sha:
            raise SystemExit("Model directory đã có revision khác; hãy lưu riêng trước khi đổi.")
    size = sum(item.size or 0 for item in info.siblings)
    print(f"Repo: {repo_id}\nRevision: {info.sha}\nTotal bytes: {size}", flush=True)
    source_metadata = {
        "repo_id": repo_id,
        "revision": info.sha,
        "total_repo_bytes": size,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": f"https://huggingface.co/{repo_id}/tree/{info.sha}",
        "download_complete": manifest_path.exists(),
        "conversion_complete": (ROOT / "models/gemma-mlx-4bit/manifest.json").exists(),
        "inference_verified": False,
        "qlora_verified": False,
        "download_status": "metadata_only" if args.info_only else "downloading",
    }
    metadata_path = ROOT / "outputs/environment/model_source.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(source_metadata, indent=2) + "\n")
    if args.info_only:
        return
    snapshot_download(
        repo_id=repo_id,
        revision=info.sha,
        local_dir=model_dir,
        max_workers=4,
        allow_patterns=["*.json", "*.safetensors", "*.model", "*.jinja", "*.txt", "*.md"],
    )
    manifest = {
        "repo_id": repo_id,
        "revision": info.sha,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": f"https://huggingface.co/{repo_id}/tree/{info.sha}",
        "license": "apache-2.0 (theo model card tại thời điểm thiết lập)",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    source_metadata.update(download_complete=True, download_status="downloaded")
    metadata_path.write_text(json.dumps(source_metadata, indent=2) + "\n")
    print(f"Downloaded: {model_dir}")
    if args.convert:
        destination = ROOT / "models/gemma-mlx-4bit"
        if destination.exists():
            raise SystemExit(f"Không ghi đè model đã có: {destination}")
        code = (
            "from mlx_lm.convert import convert; "
            "import sys; convert(hf_path=sys.argv[1], mlx_path=sys.argv[2], "
            "quantize=True, q_bits=4, q_group_size=64, dtype='bfloat16')"
        )
        subprocess.run([sys.executable, "-c", code, str(model_dir), str(destination)], check=True)
        import importlib.metadata

        manifest.update(
            {
                "format": "mlx-text-only",
                "quantization": {"bits": 4, "group_size": 64, "mode": "affine"},
                "mlx_lm_version": importlib.metadata.version("mlx-lm"),
            }
        )
        (destination / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        )
        source_metadata.update(conversion_complete=True, download_status="converted")
        metadata_path.write_text(json.dumps(source_metadata, indent=2) + "\n")
        print(f"Converted: {destination}")


if __name__ == "__main__":
    main()

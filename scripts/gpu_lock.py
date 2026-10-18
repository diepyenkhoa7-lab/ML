"""One managed MLX workload per workspace, across training and inference commands."""

import fcntl
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def gpu_is_busy(path=None):
    """Probe the real workspace lock, including evaluation and inference workloads."""
    path = Path(path or ROOT / ".cache/gemma-gpu.lock")
    if not path.exists():
        return False
    with path.open("r+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
        return False


@contextmanager
def gpu_lock(path=None):
    path = Path(path or ROOT / ".cache/gemma-gpu.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("GPU Gemma đang được dùng; chờ train/suy luận hoàn tất") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

import fcntl
import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "outputs/auto_dev"


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        temporary = stream.name
    os.replace(temporary, path)


def command(pid):
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "stat=,command="], capture_output=True, text=True, check=False
    )
    text = result.stdout.strip()
    if not text or text.startswith("Z"):
        return ""
    return text.split(None, 1)[1] if " " in text else ""


def alive(pid, expected):
    return bool(pid and expected and expected in command(pid))


@contextmanager
def lock():
    FOLDER.mkdir(parents=True, exist_ok=True)
    with (FOLDER / "coordinator.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield

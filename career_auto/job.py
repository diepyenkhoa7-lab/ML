"""Detached one-step subprocess with an explicit exit record."""

import argparse
import os
import subprocess

from .state import ROOT, read, write

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()
    spec = read(args.spec)
    os.environ["MPLCONFIGDIR"] = str(ROOT / ".cache/matplotlib")
    os.environ["HF_HOME"] = str(ROOT / ".cache/huggingface")
    try:
        with open(spec["log"], "a") as stream:
            child = subprocess.Popen(
                spec["command"], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT
            )
            write(spec["child"], dict(pid=child.pid, command=spec["command"]))
            code = child.wait()
        write(spec["result"], dict(returncode=code, status="completed" if code == 0 else "failed"))
    except BaseException as exc:
        write(spec["result"], dict(returncode=-1, status="failed", error=str(exc)))
        raise

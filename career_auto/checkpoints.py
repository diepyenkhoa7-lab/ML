"""LoRA/head plus optimizer slots; full frozen backbone is never duplicated."""

import json
import shutil
import time
from pathlib import Path

import numpy as np

from career_ai.data import digest

from .state import write


def save(run, backbone, head, optimizer, state, identity):
    folder = Path(run) / "checkpoints"
    folder.mkdir(exist_ok=True)
    target = folder / f"checkpoint_{time.time_ns()}"
    temporary = folder / (target.name + ".partial")
    temporary.mkdir()
    backbone.save_lora_weights(str(temporary / "adapter.lora.h5"))
    head.save_weights(temporary / "head.weights.h5")
    np.savez(
        temporary / "optimizer.npz",
        **{f"v{i}": v.numpy() for i, v in enumerate(optimizer.variables)},
    )
    write(
        temporary / "state.json",
        dict(
            identity=identity,
            cursor=state,
            optimizer_shapes=[list(v.shape) for v in optimizer.variables],
        ),
    )
    checksums = {p.name: digest(p) for p in temporary.iterdir()}
    write(temporary / "checksums.json", checksums)
    temporary.rename(target)
    write(folder / "latest.json", dict(directory=target.name))
    # Keep one previous committed checkpoint; never delete an incomplete save automatically.
    complete = sorted(p for p in folder.glob("checkpoint_*") if not p.name.endswith(".partial"))
    for old in complete[:-2]:
        shutil.rmtree(old)
    return target


def restore(run, backbone, head, optimizer, identity):
    folder = Path(run) / "checkpoints"
    latest = json.loads((folder / "latest.json").read_text())["directory"]
    if Path(latest).name != latest:
        raise ValueError("Invalid checkpoint pointer")
    checkpoint = folder / latest
    for name, expected in json.loads((checkpoint / "checksums.json").read_text()).items():
        if Path(name).name != name or digest(checkpoint / name) != expected:
            raise ValueError("Checkpoint checksum mismatch")
    data = json.loads((checkpoint / "state.json").read_text())
    if data["identity"] != identity:
        raise ValueError("Resume config/source/data differ from original experiment")
    if data["optimizer_shapes"] != [list(v.shape) for v in optimizer.variables]:
        raise ValueError("Optimizer slot layout changed")
    with np.load(checkpoint / "optimizer.npz", allow_pickle=False) as arrays:
        if len(arrays.files) != len(optimizer.variables):
            raise ValueError("Optimizer variable count changed")
        for i, variable in enumerate(optimizer.variables):
            variable.assign(arrays[f"v{i}"])
    backbone.load_lora_weights(str(checkpoint / "adapter.lora.h5"))
    head.load_weights(checkpoint / "head.weights.h5")
    return data["cursor"]

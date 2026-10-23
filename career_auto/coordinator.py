"""One safe scheduling decision per heartbeat; never import TensorFlow while waiting."""

import argparse
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from .state import FOLDER, ROOT, alive, command, lock, read, write

PYTHON = str(ROOT / ".venv-tf/bin/python")
STATE = FOLDER / "state.json"


def score(history):
    import math

    values = [row["selection_score"] for row in history]
    if not values or not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("Invalid validation selection scores")
    return min(values)


def record_candidate(state, run, learning_rate, reference=False):
    value = score(read(ROOT / run / "llm_history.json"))
    old = state.get("best_score")
    significant = old is None or (old - value) >= 0.01 * max(abs(old), 1e-12)
    if old is None or value < old:
        state.update(best_score=value, best_run=run, best_learning_rate=learning_rate)
    if not reference:
        state["consecutive_no_improvement"] = (
            0 if significant else state["consecutive_no_improvement"] + 1
        )
    return value


def training_processes():
    text = subprocess.check_output(["ps", "-axo", "pid=,stat=,command="], text=True)
    return [
        line.strip()
        for line in text.splitlines()
        if ("Python -m career_ai train-" in line or "Python -m career_auto.training " in line)
        and " Z " not in line
    ]


def start(state, action, arguments, training=False):
    if training and training_processes():
        raise RuntimeError("Another training process exists; refusing duplicate")
    if shutil.disk_usage(ROOT).free < 20 * 1024**3:
        raise RuntimeError("Less than 20 GiB free; refusing a new step")
    tag = f"{action}_{time.time_ns()}"
    spec = FOLDER / f"{tag}.json"
    config = dict(
        command=[PYTHON, *arguments],
        log=str(FOLDER / f"{tag}.log"),
        result=str(FOLDER / f"{tag}.result.json"),
        child=str(FOLDER / f"{tag}.child.json"),
    )
    write(spec, config)
    with open(config["log"], "a") as stream:
        worker = subprocess.Popen(
            [PYTHON, "-m", "career_auto.job", "--spec", str(spec)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    state["job"] = dict(
        pid=worker.pid,
        expected=f"-m career_auto.job --spec {spec}",
        action=action,
        arguments=arguments,
        training=training,
        spec=str(spec),
        **config,
    )
    state["status"] = action
    state["next_action"] = f"Wait for {action}; inspect {config['log']}"


def install_validation_default(state):
    # Executed only after the original training process has completed.
    path = ROOT / "career_ai/__main__.py"
    text = path.read_text()
    if 'p.add_argument("--split"' not in text:
        shutil.copyfile(path, FOLDER / "legacy_main_before_validation_default.py")
        text = text.replace(
            '    p.add_argument("--language-eval", action="store_true")',
            '    p.add_argument("--language-eval", action="store_true")\n'
            '    p.add_argument("--split", choices=["valid", "test"], default="valid")',
        )
        first = text.index('    if a.command == "evaluate":')
        last = text.index("    if not a.input:", first)
        text = (
            text[:first]
            + """    if a.command == "evaluate":
        from career_auto.evaluation import evaluate
        print(json.dumps(evaluate(a.run, a.model, a.split, a.language_eval), indent=2))
        return
"""
            + text[last:]
        )
        path.write_text(text)
    state["validation_default_installed"] = True


def handle_finished_job(state, job):
    action = job["action"]
    if action == "validate_baseline":
        state["status"] = "validate_reference"
    elif action == "validate_reference":
        record_candidate(state, state["reference_run"], 5e-5, reference=True)
        state["status"] = "choose_next_trial"
    elif action == "smoke":
        state["status"] = "resume_smoke"
    elif action == "resume_smoke":
        state["status"] = "check_smoke"
    elif action == "check_smoke":
        state["status"] = "start_full"
    elif action == "full":
        state["status"] = "check_full"
    elif action == "check_full":
        state["status"] = "validate_trial"
    elif action == "validate_trial":
        trial = state["trials"][-1]
        trial.update(
            status="completed", score=record_candidate(state, trial["run"], trial["learning_rate"])
        )
        state["status"] = "choose_next_trial"
    else:
        state["final_step"] += 1
        state["status"] = "finalize"


def tick():
    with lock():
        policy, state = read(ROOT / "configs/auto_goal.json"), read(STATE)
        if state["status"] in ["needs_attention", "ready_for_handoff", "completed"]:
            return state
        from career_ai.data import digest

        if digest(ROOT / "data/tensorflow_v1/manifest.json") != policy["dataset_manifest_sha256"]:
            raise RuntimeError("Frozen dataset manifest changed")
        manifest = read(ROOT / "data/tensorflow_v1/manifest.json")
        for relative, expected in manifest["raw"].items():
            if digest(ROOT / relative) != expected:
                raise RuntimeError(f"Frozen raw source changed: {relative}")
        job = state.get("job")
        if job:
            if alive(job["pid"], job["expected"]):
                return state
            # A wrapper can die while its model subprocess survives: never duplicate it.
            if Path(job["child"]).exists():
                child = read(job["child"])
                if alive(child["pid"], " ".join(child["command"][1:])):
                    return state
            result = read(job["result"]) if Path(job["result"]).exists() else dict(returncode=-1)
            state.pop("job")
            if result["returncode"]:
                key = job["action"] + ":" + str(state.get("additional_experiments_used", 0))
                retries = state["retries"].get(key, 0)
                if retries >= policy["max_step_retries"]:
                    state.update(status="needs_attention", error=f"Retry budget exhausted: {key}")
                else:
                    state["retries"][key] = retries + 1
                    arguments = job["arguments"]
                    if job["training"] and "--run" in arguments:
                        run = ROOT / arguments[arguments.index("--run") + 1]
                        if (
                            run / "checkpoints/latest.json"
                        ).exists() and "--resume" not in arguments:
                            arguments = [*arguments, "--resume"]
                        elif run.exists() and not (run / "checkpoints/latest.json").exists():
                            run.rename(run.with_name(run.name + f"_failed_init_{time.time_ns()}"))
                    start(state, job["action"], arguments, job["training"])
                write(STATE, state)
                return state
            handle_finished_job(state, job)
        if state["status"] == "waiting_current_training":
            if alive(state["current_training_pid"], state["current_training_command"]):
                return state
            run = ROOT / policy["current_run"]
            if (
                not (run / "llm.json").exists()
                or read(run / "lineage.json")["status"] != "completed"
            ):
                state.update(
                    status="needs_attention",
                    error="Original training ended without a completed artifact; "
                    "legacy partial has no optimizer resume",
                )
                write(STATE, state)
                return state
            controller = state["legacy_controller_pid"]
            if "scripts/run_training_pipeline.py" in command(controller):
                try:
                    os.kill(controller, signal.SIGTERM)
                    os.kill(controller, signal.SIGCONT)
                except ProcessLookupError:
                    pass
            legacy_status = ROOT / "outputs/latest_pipeline.json"
            if legacy_status.exists():
                old = read(legacy_status)
                old.update(status="superseded", reason="Intentional autonomous-goal handoff")
                write(legacy_status, old)
            state.update(
                handoff="legacy_controller_retired_after_train", reference_run=policy["current_run"]
            )
            install_validation_default(state)
            start(
                state,
                "validate_baseline",
                [
                    "-m",
                    "career_auto.evaluation",
                    "--model",
                    "baseline",
                    "--run",
                    policy["baseline_run"],
                ],
            )
        elif state["status"] == "validate_reference":
            start(
                state,
                "validate_reference",
                ["-m", "career_auto.evaluation", "--run", state["reference_run"]],
            )
        elif state["status"] == "choose_next_trial":
            if (
                state["additional_experiments_used"] >= policy["max_additional_experiments"]
                or state["consecutive_no_improvement"] >= policy["patience"]
            ):
                state.update(
                    selected_run=state["best_run"],
                    test_authorized=True,
                    status="finalize",
                    final_step=0,
                )
            else:
                item = dict(policy["experiments"][state["additional_experiments_used"]])
                if item["learning_rate"] == "best_validation":
                    item["learning_rate"] = state["best_learning_rate"]
                run = f"outputs/auto_{item['id']}"
                trial = dict(**item, run=run, smoke_run=run + "_smoke", status="reserved")
                state["trials"].append(trial)
                state["additional_experiments_used"] += 1
                for smoke in [False, True]:
                    write(
                        FOLDER / f"{item['id']}{'_smoke' if smoke else ''}.config.json",
                        dict(
                            rank=item["rank"],
                            learning_rate=item["learning_rate"],
                            epochs=1 if smoke else 2,
                            **(dict(limit=20) if smoke else {}),
                        ),
                    )
                config = str((FOLDER / f"{item['id']}_smoke.config.json").relative_to(ROOT))
                start(
                    state,
                    "smoke",
                    ["-m", "career_auto.training", "--config", config, "--run", trial["smoke_run"]],
                    training=True,
                )
        elif state["status"] in [
            "resume_smoke",
            "check_smoke",
            "start_full",
            "check_full",
            "validate_trial",
        ]:
            trial = state["trials"][-1]
            if state["status"] == "resume_smoke":
                config = str((FOLDER / f"{trial['id']}_smoke.config.json").relative_to(ROOT))
                start(
                    state,
                    "resume_smoke",
                    [
                        "-m",
                        "career_auto.training",
                        "--config",
                        config,
                        "--run",
                        trial["smoke_run"],
                        "--resume",
                    ],
                    True,
                )
            elif state["status"] == "check_smoke":
                start(
                    state,
                    "check_smoke",
                    ["scripts/check_saved_run.py", "--model", "llm", "--run", trial["smoke_run"]],
                )
            elif state["status"] == "start_full":
                config = str((FOLDER / f"{trial['id']}.config.json").relative_to(ROOT))
                start(
                    state,
                    "full",
                    ["-m", "career_auto.training", "--config", config, "--run", trial["run"]],
                    True,
                )
            elif state["status"] == "check_full":
                start(
                    state,
                    "check_full",
                    ["scripts/check_saved_run.py", "--model", "llm", "--run", trial["run"]],
                )
            else:
                start(
                    state, "validate_trial", ["-m", "career_auto.evaluation", "--run", trial["run"]]
                )
        elif state["status"] == "finalize":
            steps = [
                (
                    "final_test",
                    [
                        "-m",
                        "career_auto.evaluation",
                        "--split",
                        "test",
                        "--run",
                        state["selected_run"],
                    ],
                ),
                (
                    "comparison",
                    [
                        "scripts/compare_runs.py",
                        "--baseline",
                        policy["baseline_run"],
                        "--llm",
                        state["selected_run"],
                        "--output",
                        "outputs/auto_dev/comparison",
                    ],
                ),
                ("demo", ["-m", "career_auto.demo", "--run", state["selected_run"]]),
                ("notebooks", ["scripts/execute_notebooks.py"]),
                ("tests", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
            ]
            if state["final_step"] >= len(steps):
                state["status"] = "ready_for_handoff"
            else:
                action, arguments = steps[state["final_step"]]
                if (
                    action == "comparison"
                    and (ROOT / "outputs/auto_dev/comparison/comparison.csv").exists()
                ):
                    state["final_step"] += 1
                else:
                    start(state, action, arguments)
        write(STATE, state)
        return state


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    print(__import__("json").dumps(tick(), indent=2))

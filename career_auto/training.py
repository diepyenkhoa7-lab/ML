"""Versioned experiment trainer with optimizer-aware, atomic resume checkpoints."""

import argparse
import json
import os
import shutil
from importlib.metadata import version
from pathlib import Path

os.environ["KERAS_BACKEND"] = "tensorflow"

import keras
import numpy as np
import tensorflow as tf

from career_ai.data import FEATURES, ROOT, digest, inverse, load, load_language, target
from career_ai.language import chat_prompt
from career_ai.models import head_model, pooled, qwen_load, tokenize

from . import checkpoints
from .state import read, write


def identity(config):
    paths = list((ROOT / "career_ai").glob("*.py")) + [
        Path(__file__),
        ROOT / "career_auto/checkpoints.py",
        ROOT / "career_auto/state.py",
    ]
    return dict(
        versions={k: version(k) for k in ["tensorflow", "keras", "keras-hub", "numpy"]},
        config=config,
        dataset=digest(ROOT / "data/tensorflow_v1/manifest.json"),
        source={str(p.relative_to(ROOT)): digest(p) for p in paths},
    )


def answer_batch(model, item):
    prefix = chat_prompt(item["prompt"])
    full = prefix + json.dumps(item["answer"], ensure_ascii=False)
    n = int(np.asarray(model.preprocessor.tokenizer(prefix)).size)
    length = int(np.asarray(model.preprocessor.tokenizer(full)).size)
    if length >= 1024:
        return None
    x, y, w = model.preprocessor([full], sequence_length=length + 1)
    # Qwen has no BOS token; labels are shifted left by one token.
    start = (
        n
        - 1
        + int(
            model.preprocessor.add_start_token
            and model.preprocessor.tokenizer.start_token_id is not None
        )
    )
    w = tf.cast(w, tf.float32) * tf.cast(tf.range(tf.shape(w)[1])[None, :] >= start, tf.float32)
    return x, y, w


def answer_loss(model, batch, training):
    x, y, w = batch
    ce = keras.losses.sparse_categorical_crossentropy(
        y, model(x, training=training), from_logits=True
    )
    return tf.reduce_sum(ce * w) / tf.maximum(tf.reduce_sum(w), 1.0)


def validation(model, head, valid):
    values = [
        float(head(pooled(model, tokenize(model, [r])))[0, 0]) for r in valid.to_dict("records")
    ]
    errors = np.abs(np.asarray(values) - target(valid))
    score = float(np.mean([errors[valid.market.eq(m)].mean() for m in valid.market.unique()]))
    losses = []
    for item in load_language("valid")[:32]:
        batch = answer_batch(model, item)
        if batch is not None:
            losses.append(float(answer_loss(model, batch, False)))
    if not losses:
        raise ValueError("No validation language examples fit context")
    ce = float(np.mean(losses))
    if not np.isfinite([score, ce]).all():
        raise ValueError("Nonfinite validation loss")
    return dict(
        validation_log_mae=score,
        validation_answer_ce=ce,
        validation_language_examples=len(losses),
        selection_score=score + 0.1 * ce,
    )


def train(config, run, resume=False):
    if config["rank"] not in [8, 16] or config["learning_rate"] not in [2e-5, 5e-5, 1e-4]:
        raise ValueError("Experiment outside approved search space")
    if config["epochs"] not in [1, 2]:
        raise ValueError("At most two epochs")
    run = Path(run)
    run.mkdir(parents=True, exist_ok=resume)
    frozen = identity(config)
    if resume:
        previous = read(run / "lineage.json")
        if any(previous.get(k) != frozen[k] for k in frozen):
            raise ValueError("Original experiment identity differs; refusing resume")
    write(run / "lineage.json", dict(status="running", **frozen))
    keras.utils.set_random_seed(42)
    train_data, valid = load("train"), load("valid")
    limited = config.get("limit")
    if limited:
        train_data = train_data.groupby("market").head(limited // 2)
        valid = valid.groupby("market").head(min(16, limited // 2))
    model = qwen_load()
    model.backbone.enable_lora(rank=config["rank"])
    width = int(pooled(model, tokenize(model, train_data.head(1).to_dict("records"))).shape[-1])
    head = head_model(width)
    variables = model.backbone.trainable_weights + head.trainable_weights
    lora_count = len(model.backbone.trainable_weights)
    optimizer = keras.optimizers.AdamW(config["learning_rate"])
    optimizer.build(variables)
    cursor = dict(
        epoch=0,
        phase="numeric",
        next_index=0,
        best=None,
        best_dir=None,
        history=[],
        language_updates=0,
    )
    if resume:
        cursor = checkpoints.restore(run, model.backbone, head, optimizer, frozen)
        write(
            run / "resume_check.json",
            dict(
                optimizer_iterations=int(optimizer.iterations),
                cursor=cursor,
                optimizer_variables=len(optimizer.variables),
                restored=True,
            ),
        )
    else:
        checkpoints.save(run, model.backbone, head, optimizer, cursor, frozen)
    counts = train_data.market.value_counts()
    market_weights = {m: min(len(train_data) / (2 * n), 5.0) for m, n in counts.items()}
    language = load_language("train")[:2] if limited else load_language("train")
    before_lora = [v.numpy().copy() for v in variables[:lora_count]] if not resume else None
    try:
        while cursor["epoch"] < config["epochs"]:
            epoch = cursor["epoch"]
            if cursor["phase"] in ["numeric", "language"]:
                phase = cursor["phase"]
                rows = (
                    train_data.sample(frac=1, random_state=42 + epoch).to_dict("records")
                    if phase == "numeric"
                    else language
                )
                selected_vars = variables if phase == "numeric" else variables[:lora_count]
                accum = [tf.zeros_like(v) for v in selected_vars]
                pending = 0
                last_save = cursor["next_index"]
                for i in range(cursor["next_index"], len(rows)):
                    row = rows[i]
                    batch = answer_batch(model, row) if phase == "language" else None
                    if phase == "language" and batch is None:
                        continue
                    with tf.GradientTape() as tape:
                        if phase == "numeric":
                            y = tf.constant(
                                [
                                    np.log1p(
                                        row["salary"]
                                        / (1000.0 if row["market"] == "international" else 1e6)
                                    )
                                ],
                                tf.float32,
                            )
                            prediction = tf.squeeze(
                                head(pooled(model, tokenize(model, [row]), True), training=True),
                                axis=-1,
                            )
                            loss = keras.losses.huber(y, prediction) * market_weights[row["market"]]
                        else:
                            loss = answer_loss(model, batch, True)
                    if not np.isfinite(float(loss)):
                        raise ValueError("Nonfinite training loss")
                    gradients = tape.gradient(loss, selected_vars)
                    for j, (g, v) in enumerate(zip(gradients, selected_vars)):
                        if g is not None:
                            g = tf.convert_to_tensor(g)
                            tf.debugging.assert_all_finite(g, "Nonfinite gradient")
                            accum[j] = accum[j] + g
                    pending += 1
                    if pending == 8 or i == len(rows) - 1:
                        optimizer.apply_gradients(
                            [(a / pending, v) for a, v in zip(accum, selected_vars)]
                        )
                        if before_lora is not None:
                            if not any(
                                not np.array_equal(a, v.numpy())
                                for a, v in zip(before_lora, variables[:lora_count])
                            ):
                                raise ValueError("First optimizer step did not change LoRA weights")
                            write(run / "weight_update_check.json", dict(actual_lora_changed=True))
                            before_lora = None
                        accum = [tf.zeros_like(v) for v in selected_vars]
                        pending = 0
                        cursor["next_index"] = i + 1
                        if phase == "language":
                            cursor["language_updates"] += 1
                        if i + 1 - last_save >= (100 if phase == "numeric" else 20):
                            checkpoints.save(run, model.backbone, head, optimizer, cursor, frozen)
                            last_save = i + 1
                    if i % 10 == 0:
                        progress = dict(
                            epoch=epoch + 1,
                            phase=phase,
                            examples=i + 1,
                            loss=float(loss),
                            optimizer_steps=int(optimizer.iterations),
                        )
                        write(run / "progress.json", progress)
                        print(json.dumps(progress), flush=True)
                # Flush a partial language batch if the final examples exceeded context.
                if pending:
                    optimizer.apply_gradients(
                        [(a / pending, v) for a, v in zip(accum, selected_vars)]
                    )
                    if phase == "language":
                        cursor["language_updates"] += 1
                cursor.update(phase="language" if phase == "numeric" else "validate", next_index=0)
                checkpoints.save(run, model.backbone, head, optimizer, cursor, frozen)
                continue
            scores = validation(model, head, valid)
            cursor["history"].append(dict(epoch=epoch + 1, **scores))
            if cursor["best"] is None or scores["selection_score"] < cursor["best"]:
                best_dir = run / f"best_epoch_{epoch + 1}"
                best_dir.mkdir(exist_ok=True)
                model.backbone.save_lora_weights(str(best_dir / "qwen.lora.h5"))
                head.save(best_dir / "salary_head.keras")
                probe = valid.groupby("market").head(1)
                values = [
                    float(head(pooled(model, tokenize(model, [r])))[0, 0])
                    for r in probe.to_dict("records")
                ]
                write(
                    best_dir / "reload_probe.json",
                    dict(
                        profiles=probe[FEATURES].to_dict("records"),
                        predictions=inverse(values, probe.market).tolist(),
                    ),
                )
                cursor.update(best=scores["selection_score"], best_dir=best_dir.name)
            cursor.update(epoch=epoch + 1, phase="numeric", next_index=0)
            checkpoints.save(run, model.backbone, head, optimizer, cursor, frozen)
            write(run / "llm_history.json", cursor["history"])
        best = run / cursor["best_dir"]
        for name in ["qwen.lora.h5", "salary_head.keras", "reload_probe.json"]:
            shutil.copyfile(best / name, run / name)
        write(
            run / "llm.json",
            dict(
                dataset_manifest_sha256=frozen["dataset"],
                base_source=read(ROOT / "configs/qwen_source.json"),
                rank=config["rank"],
                learning_rate=config["learning_rate"],
                context=1024,
                training_rows=len(train_data),
                epochs=config["epochs"],
                limited_trial=bool(limited),
                language_finetuned=cursor["language_updates"] > 0,
                selection_score=cursor["best"],
                language_steps=cursor["language_updates"],
                device=[d.name for d in tf.config.list_logical_devices()],
            ),
        )
        write(run / "lineage.json", dict(status="completed", **frozen))
    except BaseException as exc:
        write(run / "lineage.json", dict(status="failed", error=str(exc), **frozen))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    train(read(args.config), args.run, args.resume)

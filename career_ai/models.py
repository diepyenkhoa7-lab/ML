import os

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import json
from functools import lru_cache

import keras
import numpy as np
import tensorflow as tf

from .data import ROOT, features, inverse, load, load_language, prompt, target, write

PRESET = "hf://keras/qwen3_1.7b_en"


def baseline_train(folder, epochs=100):
    keras.utils.set_random_seed(42)
    train, valid = load("train"), load("valid")
    x, vocab = features(train)
    xv, _ = features(valid, vocab)
    normal = keras.layers.Normalization()
    normal.adapt(x)
    model = keras.Sequential([keras.Input((x.shape[1],)), normal, keras.layers.Dense(1)])
    model.compile(optimizer=keras.optimizers.Adam(0.01), loss=keras.losses.Huber())
    history = model.fit(
        x,
        target(train),
        validation_data=(xv, target(valid)),
        batch_size=64,
        epochs=epochs,
        verbose=2,
        callbacks=[keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)],
    )
    model.save(folder / "baseline.keras")
    write(folder / "vocabulary.json", vocab)
    write(folder / "baseline_history.json", history.history)


def qwen_load():
    import keras_hub

    model = keras_hub.models.Qwen3CausalLM.from_preset(str(ROOT / "models/qwen3"), dtype="float32")
    model.preprocessor.sequence_length = 1024
    model.compile(sampler="greedy")
    keras.utils.set_random_seed(42)
    return model


def tokenize(lm, rows):
    texts = [prompt(r) for r in rows]
    lengths = [int(np.asarray(lm.preprocessor.tokenizer(t)).size) for t in texts]
    if max(lengths) > 1022:
        raise ValueError("Profile exceeds context limit")
    return lm.preprocessor.generate_preprocess(texts, sequence_length=max(lengths) + 2)


def pooled(lm, tokens, training=False):
    hidden = lm.backbone(tokens, training=training)
    mask = tf.cast(tokens["padding_mask"], tf.int32)
    index = tf.reduce_sum(mask, axis=1) - 1
    return tf.gather(hidden, index, axis=1, batch_dims=1)


def head_model(width):
    return keras.Sequential(
        [
            keras.Input((width,)),
            keras.layers.LayerNormalization(),
            keras.layers.Dense(64, activation="relu"),
            keras.layers.Dense(1, activation="softplus"),
        ]
    )


def llm_train(folder, epochs=2, limit=None):
    keras.utils.set_random_seed(42)
    train, valid = load("train"), load("valid")
    if not 1 <= epochs <= 2:
        raise ValueError("Initial LLM experiments permit one or two epochs")
    if limit is not None:
        if limit < 2:
            raise ValueError("Smoke limit must cover both markets (>=2)")
        train = train.groupby("market", group_keys=False).head(max(1, limit // 2))
        valid = valid.groupby("market", group_keys=False).head(max(1, min(limit, 32) // 2))
    lm = qwen_load()
    lm.backbone.enable_lora(rank=8)
    sample = tokenize(lm, train.head(1).to_dict("records"))
    head = head_model(int(pooled(lm, sample).shape[-1]))
    optimizer = keras.optimizers.AdamW(learning_rate=5e-5)
    variables = lm.backbone.trainable_weights + head.trainable_weights
    accum = [tf.zeros_like(v) for v in variables]
    language = load_language("train")
    language_validation = load_language("valid")[:32]
    language_steps = 0
    best = float("inf")
    best_epoch = None
    history = []
    pending = 0
    counts = train.market.value_counts()
    weights = {m: min(len(train) / (2 * n), 5.0) for m, n in counts.items()}
    for epoch in range(epochs):
        losses = []
        for step, r in enumerate(train.sample(frac=1, random_state=42 + epoch).to_dict("records")):
            tokens = tokenize(lm, [r])
            y = tf.constant(
                [np.log1p(r["salary"] / ({"international": 1000.0, "vietnam": 1e6}[r["market"]]))],
                dtype=tf.float32,
            )
            with tf.GradientTape() as tape:
                prediction = tf.squeeze(head(pooled(lm, tokens, True), training=True), axis=-1)
                loss = keras.losses.huber(y, prediction) * weights[r["market"]]
            gradients = tape.gradient(loss, variables)
            accum = [
                a + (tf.zeros_like(v) if g is None else tf.convert_to_tensor(g))
                for a, g, v in zip(accum, gradients, variables)
            ]
            pending += 1
            losses.append(float(loss))
            if pending == 8 or step == len(train) - 1:
                optimizer.apply_gradients([(a / pending, v) for a, v in zip(accum, variables)])
                accum = [tf.zeros_like(v) for v in variables]
                pending = 0
            if step and step % 100 == 0:
                lm.backbone.save_lora_weights(str(folder / "partial.lora.h5"))
                head.save(folder / "partial_head.keras")
                write(
                    folder / "progress.json",
                    dict(epoch=epoch + 1, examples=step + 1, status="training", not_final=True),
                )
            if step % 10 == 0:
                print(
                    json.dumps(dict(epoch=epoch + 1, step=step, loss=float(loss))),
                    flush=True,
                )
        # Language replay shares the same LoRA backbone, with answer-only token loss.
        for item in language[: 2 if limit else len(language)]:
            from .language import chat_prompt

            prefix = chat_prompt(item["prompt"])
            full = prefix + json.dumps(item["answer"], ensure_ascii=False)
            n = int(np.asarray(lm.preprocessor.tokenizer(prefix)).size)
            length = int(np.asarray(lm.preprocessor.tokenizer(full)).size)
            if length >= 1024:
                continue
            x, y, w = lm.preprocessor([full], sequence_length=length + 1)
            w = tf.cast(w, tf.float32) * tf.cast(
                tf.range(tf.shape(w)[1])[None, :] >= n - 1, tf.float32
            )
            with tf.GradientTape() as tape:
                logits = lm(x, training=True)
                loss = tf.reduce_sum(
                    keras.losses.sparse_categorical_crossentropy(y, logits, from_logits=True) * w
                ) / tf.maximum(tf.reduce_sum(w), 1.0)
            gradients = tape.gradient(loss, lm.backbone.trainable_weights)
            optimizer.apply_gradients(
                [(g, v) for g, v in zip(gradients, lm.backbone.trainable_weights) if g is not None]
            )
            language_steps += 1
        # Recompute validation after language replay; it can change salary features.
        predicted = []
        for r in valid.to_dict("records"):
            predicted.append(float(head(pooled(lm, tokenize(lm, [r])))[0, 0]))
        actual = target(valid)
        errors = np.abs(np.array(predicted) - actual)
        score = float(np.mean([np.mean(errors[valid.market.eq(m)]) for m in valid.market.unique()]))
        language_losses = []
        for item in language_validation:
            from .language import chat_prompt

            prefix = chat_prompt(item["prompt"])
            full = prefix + json.dumps(item["answer"], ensure_ascii=False)
            n = int(np.asarray(lm.preprocessor.tokenizer(prefix)).size)
            length = int(np.asarray(lm.preprocessor.tokenizer(full)).size)
            if length >= 1024:
                continue
            x, y, w = lm.preprocessor([full], sequence_length=length + 1)
            w = tf.cast(w, tf.float32) * tf.cast(
                tf.range(tf.shape(w)[1])[None, :] >= n - 1, tf.float32
            )
            logits = lm(x, training=False)
            ce = keras.losses.sparse_categorical_crossentropy(y, logits, from_logits=True)
            language_losses.append(float(tf.reduce_sum(ce * w) / tf.maximum(tf.reduce_sum(w), 1)))
        language_score = float(np.mean(language_losses)) if language_losses else None
        selection_score = score + 0.1 * (language_score or 0)
        history.append(
            dict(
                epoch=epoch + 1,
                train_loss=float(np.mean(losses)),
                validation_log_mae=score,
                validation_answer_ce=language_score,
                validation_language_examples=len(language_losses),
                selection_score=selection_score,
            )
        )
        write(folder / "llm_history.json", history)
        if selection_score < best:
            best = selection_score
            best_epoch = epoch + 1
            lm.backbone.save_lora_weights(str(folder / "qwen.lora.h5"))
            head.save(folder / "salary_head.keras")
    lm.backbone.load_lora_weights(str(folder / "qwen.lora.h5"))
    head = keras.models.load_model(folder / "salary_head.keras")
    probe = tokenize(lm, valid.head(1).to_dict("records"))
    expected = head(pooled(lm, probe)).numpy()
    # Check persisted artifacts on the same base; a fresh-process check is in the runner.
    lm.backbone.load_lora_weights(str(folder / "qwen.lora.h5"))
    restored_head = keras.models.load_model(folder / "salary_head.keras")
    np.testing.assert_allclose(expected, restored_head(pooled(lm, probe)).numpy(), atol=1e-6)
    write(folder / "reload_check.json", dict(same_base_reload_parity=True))
    write(
        folder / "llm.json",
        dict(
            preset=PRESET,
            rank=8,
            context=1024,
            epochs=epochs,
            training_rows=len(train),
            limited_trial=limit is not None,
            language_finetuned=language_steps > 0,
            language_steps=language_steps,
            selected_epoch=best_epoch,
            selection="market_mean_log_mae + 0.1 * validation_answer_ce",
            device=[d.name for d in tf.config.list_logical_devices()],
        ),
    )


@lru_cache(maxsize=2)
def loaded_baseline(folder):
    vocab = json.loads((folder / "vocabulary.json").read_text())
    return keras.models.load_model(folder / "baseline.keras"), vocab


@lru_cache(maxsize=1)
def loaded_llm(folder):
    lm = qwen_load()
    lm.backbone.load_lora_weights(str(folder / "qwen.lora.h5"))
    return lm, keras.models.load_model(folder / "salary_head.keras")


def predict(frame, folder, family):
    if family == "baseline":
        model, vocab = loaded_baseline(folder)
        x, _ = features(frame, vocab)
        values = np.maximum(model.predict(x, verbose=0).ravel(), 0)
    else:
        lm, head = loaded_llm(folder)
        values = [
            float(head(pooled(lm, tokenize(lm, [r])))[0, 0]) for r in frame.to_dict("records")
        ]
    return inverse(values, frame.market)

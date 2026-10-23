"""Compatibility checks on a tiny randomly initialized Qwen; not a quality benchmark."""

import argparse
import json
import os
import tempfile
from pathlib import Path

os.environ["KERAS_BACKEND"] = "tensorflow"
import keras
import keras_hub
import numpy as np
import tensorflow as tf

parser = argparse.ArgumentParser()
parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
arguments = parser.parse_args()
if arguments.device == "cpu":
    tf.config.set_visible_devices([], "GPU")
elif not tf.config.list_physical_devices("GPU"):
    raise RuntimeError("No GPU detected")
keras.utils.set_random_seed(42)
backbone = keras_hub.models.Qwen3Backbone(
    vocabulary_size=32,
    num_layers=2,
    num_query_heads=4,
    hidden_dim=32,
    head_dim=8,
    intermediate_dim=64,
    num_key_value_heads=2,
)
tokens = {
    "token_ids": tf.constant([[1, 2, 3, 0]]),
    "padding_mask": tf.constant([[True, True, True, False]]),
}
backbone.enable_lora(rank=8)
variables = backbone.trainable_weights
before = [v.numpy().copy() for v in variables]
optimizer = keras.optimizers.AdamW(5e-5)
with tf.GradientTape() as tape:
    output = backbone(tokens, training=True)
    loss = tf.reduce_mean(tf.square(output - 0.5))
gradients = tape.gradient(loss, variables)
optimizer.apply_gradients(zip(gradients, variables))
assert any(not np.array_equal(a, v.numpy()) for a, v in zip(before, variables))
actual_output = backbone(tokens)
if arguments.device == "gpu" and "GPU" not in actual_output.device:
    raise RuntimeError("Tiny Qwen output did not execute on GPU")
expected = actual_output.numpy()
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "tiny.lora.h5"
    backbone.save_lora_weights(str(path))
    backbone.load_lora_weights(str(path))
    np.testing.assert_allclose(expected, backbone(tokens).numpy(), atol=1e-6)
report = dict(
    tensorflow=tf.__version__,
    keras=keras.__version__,
    keras_hub=keras_hub.__version__,
    devices=[d.name for d in tf.config.list_logical_devices()],
    output_device=actual_output.device,
    tiny_random_qwen_lora_update=True,
    same_model_lora_reload_parity=True,
    note="Compatibility only; no pretrained Qwen quality claim.",
)
print(json.dumps(report, indent=2))

# Full extraction training corpus v1.0.0

Exact exported copy of all currently prepared extraction JSONL: train 364, valid 72,
test 82, corresponding to 122/25/28 source cards. Silver source-field labels; missing
field variants are augmentations, not independent jobs. Native salary units preserved.

Full means every train example in each epoch. Validation/test are excluded from
parameter updates. This is not a full-parameter fine-tune or all raw salary CSVs.
See manifest.json, full_training.json and docs/GEMMA_FULL_TRAINING.md.

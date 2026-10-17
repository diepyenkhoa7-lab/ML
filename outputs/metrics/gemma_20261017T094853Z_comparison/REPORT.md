# Gemma validation — 20261017T094853Z

72 variants from 25 source cards. Test untouched.

| Model | Raw JSON valid | Raw schema valid | Mean field accuracy | Skill F1 |
|---|---:|---:|---:|---:|
| base | 0.000 | 0.000 | 0.000 | 0.000 |
| adapter | 1.000 | 0.903 | 0.911 | 0.884 |

Raw JSON is the required output contract. Formatting failures count as wrong.
The diagnostic below removes Markdown fences to separate formatting from content.

| Model | Fences removed | Diagnostic mean field accuracy | Diagnostic Skill F1 |
|---|---:|---:|---:|
| base | 72 | 0.790 | 0.835 |
| adapter | 0 | 0.911 | 0.884 |

Exact per-field scores and raw predictions are retained beside these results.
Silver references are not independent human gold. This is not career-advice evaluation.
The final 100-step adapter was fixed before evaluation; no further training occurred.

Adapter schema failures: 6 duplicate-skill outputs and 1 wrong-key output; see
`../gemma_20261017T094853Z_adapter_valid/schema_errors.json`. No output repairs were applied.

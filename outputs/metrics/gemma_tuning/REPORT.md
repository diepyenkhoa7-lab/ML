# Gemma: validation selection

Selected: `adapters/gemma-jobs/20261017T105728Z`

Primary scores use raw outputs. No JSON repair. Test is excluded from selection.

| Adapter | Mean field exact | Skill F1 | JSON | Schema | Selection score | Promoted |
|---|---:|---:|---:|---:|---:|---|
| 20261017T101925Z | 0.9045 | 0.9022 | 1.0000 | 0.8889 | 0.9007 | True |
| 20261017T104241Z | 0.9271 | 0.9102 | 1.0000 | 0.9444 | 0.9255 | True |
| 20261017T105728Z | 0.9375 | 0.9376 | 1.0000 | 0.9583 | 0.9417 | True |
| 20261017T111205Z | 0.9340 | 0.9290 | 1.0000 | 0.9583 | 0.9374 | False |

Stopping rule: candidate budget exhausted.

Silver source-field labels; validation has 72 variants from 25 jobs. These scores do not establish generalization to arbitrary ads or career advice.

Per-run error_analysis.json records schema failures, exact field errors, variant slices and paired same-unit numeric MAE.

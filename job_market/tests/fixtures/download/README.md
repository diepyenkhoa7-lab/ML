# HTTP test fixture

`jobs-2026-v1.zip` is the exact approved **new** Kaggle archive for
`baocgb/vietnam-it-jobs-raw-data-from-topcv-2026`, revision 1, CC-BY-4.0
as declared by its publisher, Châu Gia Bảo (baocgb). Attribution and original
metadata remain in `src/career_market/sources.json` and
`datasets/provenance/metadata-2026.json`.

Pinned URL: https://www.kaggle.com/api/v1/datasets/download/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026?datasetVersionNumber=1

ZIP SHA-256: `29651eb3e85d4d5b0fb8e45f968e01585c51de95f038cb850dc72607352f0426`.

Only the HTTP boundary uses this fixture, so offline service/CLI/UI checks
exercise real checksumming, ZIP reading, filesystem publication and receipts.
Small corrupt byte strings in tests are synthetic logic fixtures only; they
are never market datasets, model inputs or reported market statistics.

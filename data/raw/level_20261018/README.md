---
license: cc-by-4.0
language:
- en
pretty_name: Level Tech Jobs by AI Level
tags:
- jobs
- labor-market
- artificial-intelligence
- employment
- job-postings
task_categories:
- tabular-classification
- tabular-regression
size_categories:
- 10K<n<100K
source_datasets:
- original
configs:
- config_name: jobs
  default: true
  data_files:
  - split: train
    path: "data/level-jobs.csv"
- config_name: ai_jobs_index
  data_files:
  - split: train
    path: "data/ai-jobs-index.csv"
- config_name: ai_native_companies
  data_files:
  - split: train
    path: "data/ai-native-companies.csv"
citation: |
  @misc{level_jobs,
    author = {Level},
    title = {Level Tech Jobs by AI Level},
    howpublished = {\url{https://jobsbylevel.com/data/open-dataset}},
    note = {Open tech job postings rated from AI Level 1 to AI Level 4. See measured_at for the snapshot date.}
  }
---

# Level Tech Jobs by AI Level

Open tech job postings tracked by [Level](https://jobsbylevel.com), one row
per posting, each rated on how central artificial intelligence is to the
work: from **AI Level 1** (AI is not part of the described work) to
**AI Level 4** (the work is building AI systems).

Browse the same data live: <https://jobsbylevel.com/ai-jobs-index>.
Quarterly ranking built on it: <https://jobsbylevel.com/ai-jobs-index/2026-q3>.

**Metadata only.** No job description, no excerpt of employer text, no
personal data. Each row is a short set of facts (company, title, location,
dates, published salary, links) plus what Level computes itself (AI score,
AI level, job family, normalized country).

## Files

Written by `scripts/export-dataset.ts` into `data/` (regenerated from the
live catalog before each release, never edited by hand).

| File | Rows | Content |
| --- | --- | --- |
| `data/level-jobs.csv` | one per live posting | Main table, described below. |
| `data/level-jobs.jsonl` | same rows | Same table as JSON Lines, typed numbers and booleans. |
| `data/ai-jobs-index.csv` | one per scope and level | Counts by level: global, per category, per company (10+ live postings). |
| `data/ai-native-companies.csv` | one per company | Companies ranked by AI Level 4 share (10+ live postings). |

Hugging Face converts the CSV files to Parquet automatically on the
`refs/convert/parquet` branch of a public dataset.

### `level-jobs.csv` columns

| Column | Type | Description |
| --- | --- | --- |
| `job_id` | string | Stable Level identifier of the posting (URL slug). |
| `company_slug` | string | Company identifier, matches `jobsbylevel.com/companies/{slug}`. |
| `company_name` | string | Company name. |
| `title` | string | Job title as published, whitespace normalized, 200 characters max. |
| `category` | string | Job family assigned by Level (e.g. `machine-learning`, `data`). |
| `seniority` | string | Seniority inferred by Level (`intern` to `executive`, or `unknown`). |
| `ai_score` | integer | AI score computed by Level, 0 to 100. |
| `ai_level` | integer | AI level, 1 to 4, from fixed thresholds on `ai_score` (40, 60, 80). |
| `ai_level_label` | string | Label of the level, e.g. "AI Level 4". |
| `country` | string | ISO 3166-1 alpha-2 country code, empty when unknown. |
| `city` | string | First recognized city in the location, empty when none. |
| `location` | string | Location string as published, 200 characters max. |
| `remote` | boolean | True when the posting is marked remote. |
| `employment_type` | string | Employment type when published (e.g. full-time). |
| `salary_min` | integer | Published minimum salary, empty when not published. |
| `salary_max` | integer | Published maximum salary, empty when not published. |
| `salary_currency` | string | ISO 4217 currency of the published salary. |
| `posted_date` | date | Publication date reported by the source, YYYY-MM-DD. |
| `first_seen_date` | date | Date Level first saw the posting, YYYY-MM-DD. |
| `source_ats` | string | Hiring system the posting was read from (greenhouse, lever, ashby…). |
| `source_url` | string | Link to the original posting, tracking parameters removed. |
| `level_url` | string | Page of the posting on jobsbylevel.com. |
| `measured_at` | date | Snapshot date. |
| `license` | string | "CC BY 4.0" (see License below). |
| `attribution` | string | Attribution line to keep on every reuse. |

## Method

- **Scope**: postings open at snapshot time (`status = live`), read from the
  public job boards of the employers themselves. Postings bought on Level,
  inactive companies and job boards that republish other employers'
  postings are excluded.
- **AI level**: fixed score thresholds, never percentiles. The same score
  always gives the same level. Details: <https://jobsbylevel.com/method>.
- **Salary**: kept only when the employer published it and it is coherent
  (positive, minimum not above maximum). Never estimated.
- **Country**: the country field of the posting, otherwise inferred from
  the location string.

## Sources and terms

Every row comes from a public job board. The license below covers Level's
own work: the compilation, the AI score and level, the job family, the
seniority and the location normalization.

**Job posting content remains the property of the respective employers.**
The files only carry short factual metadata, never description text.

Sources whose terms of use forbid automated collection or commercial reuse
without distinguishing metadata from text are **excluded entirely**:

- Amazon (amazon.jobs), per its Conditions of Use:
  <https://www.amazon.com/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM>
- Workday-hosted career sites (myworkdayjobs.com), per the Workday Site
  Terms: <https://www.workday.com/en-us/legal/site-terms.html>

The exclusion applies both to the hiring system of the company and to the
host of the posting link (`isExcludedDatasetSource` in
`packages/core/src/dataset/jobs-dataset.ts`, covered by tests).

Terms reviewed on 25 September 2026 for the other sources: the public
posting documentation of Greenhouse, Lever, Ashby, SmartRecruiters and
Workable contains no redistribution clause for posting metadata; the Lever
Postings API notes that published postings are publicly viewable and may be
scraped by third parties. This review is not legal advice.

## Citation

```
Level. Level Tech Jobs by AI Level [Data set]. jobsbylevel.com. https://jobsbylevel.com/data/open-dataset
```

```bibtex
@misc{level_jobs,
  author = {Level},
  title = {Level Tech Jobs by AI Level},
  howpublished = {\url{https://jobsbylevel.com/data/open-dataset}},
  note = {See measured_at for the snapshot date.}
}
```

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) on Level's
compilation and classification. Reuse, share and adapt freely, with
attribution: "Source: Level (jobsbylevel.com)" and a link to
<https://jobsbylevel.com/data/open-dataset>.

# External candidate review — 29 October 2026

Independent research sidecar for the ten existing IT-Job-Posting candidates and the specified Majorbird/Salely pages. Read `LABEL_RESEARCH-2026-10-29.md`, the glossary, ADR 0006 and subsequently approved ADR 0007. Did not inspect jobs-2023 raw or VietJobs labels. No canonical/catalog, training, model, issue, commit or push changes.

**Result:** seven GitHub candidates have verified snapshot salary evidence and a defensible role; three need role or version resolution. Two employer pages directly corroborate monthly VND salary ranges. These are evidence findings, **not source approval or canonical acceptance**. Unknown gross/net is retained separately under ADR 0006 and is not, by itself, a rejection reason. Posting dates are a separate evidence dimension.

## 1. GitHub provenance, revision and permitted scope

Primary publisher: [SonPhatTranDeveloper/IT-Job-Posting](https://github.com/SonPhatTranDeveloper/IT-Job-Posting). The [pinned README](https://github.com/SonPhatTranDeveloper/IT-Job-Posting/blob/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac/README.md) describes collection from ITviec, LinkedIn and TopCV and says: **“This dataset should be used for educational purpose only.”** This is positive evidence of the publisher's intended educational-use scope; absence of a standalone LICENSE does not establish a complete ban. It does not establish an unrestricted open-data license or the publisher's authority over all third-party postings.

Verified using the first-party GitHub REST API and a fresh download from the immutable raw URL:

| Item | Verified value |
| --- | --- |
| Main HEAD | `6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac`, commit dated `2025-07-08T14:17:55Z` |
| CSV history | Only returned CSV-changing commit: `9d7c7fab901b511b6fad37e1665da77a08f054be`, dated `2025-06-28T14:27:19Z` |
| Pinned CSV | [job_descriptions.csv](https://raw.githubusercontent.com/SonPhatTranDeveloper/IT-Job-Posting/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac/job_descriptions.csv) |
| CSV bytes / records | 11,087,006 bytes; 3,101 records after header; 11 columns |
| CSV SHA-256 | `68c70420d9a12381a5731f0dbee1cc2b4d2123a94882eb95bd0104a1201e8b69` |
| CSV Git blob SHA-1 | `ac426daa4e1bfd13d520d6ead2acdf77007b370d` |
| README SHA-256 | `99109bde90a75e0259ecaf635d5f15221e43f6d8d161752790906dab858c7a8e` |
| License-file check | Recursive pinned tree has exactly README, CSV and visualization HTML; no LICENSE file |
| Previous snapshot comparison | Fresh pinned CSV and README equal the existing `/tmp/ml-label-research-20261029` copies byte for byte |

API evidence: [commit](https://api.github.com/repos/SonPhatTranDeveloper/IT-Job-Posting/commits/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac), [recursive tree](https://api.github.com/repos/SonPhatTranDeveloper/IT-Job-Posting/git/trees/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac?recursive=1), [CSV history](https://api.github.com/repos/SonPhatTranDeveloper/IT-Job-Posting/commits?path=job_descriptions.csv). Saved API responses and pinned files are in `/tmp/ml-label-research-20261029/external-review/`.

**Temporal interpretation:** these ten records are in a snapshot committed in June 2025. Downloading it in October 2026 does not make these 2026 postings. Individual posting dates are absent from the CSV; commit dates identify the snapshot, not each advertisement. Do not infer listing dates from tracking-query timestamps. README identifies some skill/city fields as LLM extractions; all role and location findings below instead use original `title`, `description` and `location`.

### Source approval is independent of row validity

| Source | Permission actually evidenced | Project approval finding |
| --- | --- | --- |
| GitHub publisher | Explicit educational-only statement, compatible in purpose with educational research/model experiments; no standard open license | `conditional_educational_scope`: retain the statement and attribution. It is not evidence of unrestricted commercial use, redistribution or upstream sublicensing. No final training/source admission made here. |
| ITviec upstream | [Terms §2.1–2.2](https://itviec.com/blog/terms-and-conditions/) protect content and allow only reasonable personal use without prior written consent for broader copying/retrieval/transmission | Educational intent from GitHub does not resolve these upstream conditions; broader dataset reuse permission remains unverified. |
| TopCV upstream | [Terms §6.1–6.2](https://www.topcv.vn/terms-of-service) distinguish uploader/TopCV rights and restrict exploitation or redistribution of protected content | A license granted by uploaders to TopCV is not a demonstrated license to this project or GitHub publisher. Do not infer such a sublicense. |
| LinkedIn upstream | Public posting content successfully read; no upstream reuse permission established in this bounded review | `unresolved_upstream_scope`; accessibility proves content, not an educational or redistribution license. |

These are observed permission statements and remaining gaps, not a determination that every use of salary facts is legally prohibited. The missing LICENSE is not the reason to discard otherwise sound row evidence.

## 2. Ten existing GitHub candidates

Record numbers are 1-based CSV records after the header. Ranges and candidate midpoints below are **million VND/month**. All ranges are explicit in the same record's description; bonuses, allowances and extra salary months are excluded. `verified snapshot` means the content is present in the pinned CSV; it does not claim the vacancy is currently open or the source is approved.

| Record / original posting | Salary evidence and basis | Role/location from raw duties, not LLM fields | Row finding and corroboration |
| --- | --- | --- | --- |
| **301** — [Quang Trung, .NET](https://itviec.com/it-jobs/net-developer-net-core-asp-net-mvc-english-quang-trung-software-development-2810) | 20–35; midpoint 27.5; gross/net unknown. Benefits salary, separate 13th month. | **Backend**, HCM/Gò Vấp: backend applications, .NET APIs, database integration; frontend is preferred experience. | **Verified snapshot + primary-page content.** Public benefits repeat the salary range, company and address. Senior/3–5-year requirements coexist with fresher acceptance; do not assign this range specifically to freshers. |
| **308** — [DOL, React frontend](https://itviec.com/it-jobs/senior-front-end-developer-reactjs-javascript-dol-english-0208) | 30–50; midpoint 40; **net explicit**. Performance/13th-month bonus separate. | **Frontend**, HCM/Quận 10: ReactJS development required; Mobile/Backend only preferred. | **Verified snapshot; primary re-fetch unavailable** (web inaccessible; direct HTTP 403). Distinct duties and posting ID from 367 despite shared benefit text. |
| **367** — [DOL, Java](https://itviec.com/it-jobs/senior-java-software-engineer-aws-mongodb-dol-english-0030) | 30–50; midpoint 40; **net explicit**. | **Backend**, HCM/Quận 10: Java backend services and REST APIs, MongoDB/PostgreSQL. | **Verified snapshot; primary re-fetch unavailable** (web inaccessible; HTTP 403). Same employer/address/range as 308 is not enough to merge different roles. |
| **472** — [Quang Trung, Angular](https://itviec.com/it-jobs/frontend-developer-reactjs-next-js-angular-english-quang-trung-software-development-0329) | 20–35; midpoint 27.5; gross/net unknown. Benefits salary; 13th month separate. | **Frontend**, HCM/Gò Vấp: Angular/UI development. Raw title and duties outweigh the React/Next.js terms in the URL slug. | **Verified snapshot + primary-page content.** Fresher/experienced wording is mixed. Shared template with 301, but different required stack and duties; retain template-group linkage for split review. |
| **751** — [PioneerX, AI/workflow automation](https://itviec.com/it-jobs/ai-workflow-automation-engineer-pyhton-javascript-cong-ty-tnhh-digital-marketing-va-e-commerce-pioneerx-1351) | 13–18; midpoint candidate 15.5; gross/net unknown. Negotiable bounded salary, not an allowance. | HN/Thanh Xuân verified. **Role ambiguous:** AI API integration, n8n/Zapier/Make and workflow apps; neither ML development nor DevOps ownership is demonstrated. | **Salary verified snapshot; role needs policy.** Do not force Data/ML or DevOps from the title/CI/CD keyword. Web returns 410; direct HTTP 403; no current-vacancy claim. |
| **883** — [Infinity Innovations, backend](https://itviec.com/it-jobs/backend-programmer-java-python-linux-english-cong-ty-tnhh-bpo-infinity-innovations-group-4048) | 20–40; midpoint 30; gross/net unknown. Salary separated from meal allowance and bonuses. | **Backend**, HCM/Thủ Đức: backend systems for games/chat; PHP/Laravel and other server stacks. | **Verified snapshot; primary re-fetch unavailable** (web inaccessible; HTTP 403). Do not infer one exclusive language from the title. |
| **1533** — [Manpower, Java lead](https://www.linkedin.com/jobs/view/4250139873/) | 80–120; midpoint 100; **base salary explicit**, gross/net unknown. Project/performance bonuses separate. | **Backend**, HCM: Java/Spring services, REST, SQL and technical leadership. Raw Spanish-language location still names HCM, Vietnam. | **Verified snapshot + direct primary HTML.** Public URL redirects to the same job ID on `vn.linkedin.com`, matching role, recruiter, city, duties and range. Manpower is the advertised recruiter; ultimate hiring client is not identified. |
| **1997** — [XGame, backend lead](https://www.topcv.vn/viec-lam/backend-technical-leader/1683894.html) | 35–50; midpoint 42.5; gross/net unknown. Salary distinct from Tet bonus, extra salary month and allowances. | **Backend**, HN/Cầu Giấy: game servers, APIs and scaling backend systems. | **Verified snapshot + primary-page content; deduplicate 2739.** Page deadline **10 July 2025**, not posting date. Historical evidence, not a current vacancy. |
| **2528** — [Viettel Construction, Java](https://www.topcv.vn/viec-lam/lap-trinh-vien-java-dev-middle-to-techlead/1722942.html) | 20–32; midpoint candidate 26; **fixed monthly salary explicit**, gross/net unknown. Exclude 0.93/month allowance and annual benefits. | HN/Cầu Giấy verified. **Backend/Fullstack mapping unresolved:** module design includes screens, APIs and DB; Java/Spring and Angular present. | **Salary verified snapshot; role review + deduplicate 2809.** Same posting ID, range and nearly identical content. Web unavailable; HTTP 403. |
| **2717** — [Logic Lab, PHP](https://www.topcv.vn/viec-lam/fullstack-developer-php/1757483.html) | This record says 15–30; midpoint 22.5 is **not finalized**. Gross/net unknown. Description supplies both endpoints despite title's upper-bound wording. | HN/Tây Hồ verified. Backend-heavy PHP/API duties and collaboration with frontend; Fullstack versus Backend requires policy. | **Ambiguous salary version and role.** Record 2038 has the **same job ID**, employer and address but **14–25/month income**, midpoint 19.5, and different duties/text. No chronology establishes which version supersedes the other. Web unavailable; HTTP 403. |

Precise short excerpts, kept below 25 quoted words per external page:

- 301 primary page, benefits: `Competitive Salary: 20 – 35 million VND/month`.
- 472 primary page, benefits: `Competitive Salary: 20 – 35 million VND/month`.
- 1533 direct primary HTML, benefits: `Base salary from 80.000.000 - 120.000.000 VND/month.`
- 1997 primary page, benefits: `Lương: 35.000.000 - 50.000.000 VNĐ/tháng (Tùy level)`.
- Remaining pinned-CSV context markers, **under 25 words total**: `Net` (308/367), `(thỏa thuận)` (751), `Lương cứng tháng` (2528), `Ranges from` (2717), `Thu nhập` (2038). Numeric endpoints and interpretations are reported in the table rather than repeating long CSV passages.

Primary web content corroborated 301, 472 and 1997, but direct downloads returned HTTP 403. Therefore those reads do not establish fresh origin HTML or current availability. ITviec's relative ages of 34/24 days are not converted to dates; web-cache age is not a posting date. For 1533, the direct 200 HTML shows only a relative one-year age; it is not converted to an exact date, and dates from recommended jobs are ignored. No login, concealed salary extraction or challenge bypass was used.

### Identity and duplicate-content findings

The ten selections represent ten normalized posting URLs and **13 raw records** after including their same-URL copies. This is not a final count of independent training entities or leakage groups.

- **1997/2739:** same URL and byte-identical description; one entity, one salary observation.
- **2528/2809:** same URL, salary and duties, with title/formatting/punctuation differences. Token-set similarity is 1.0 but normalized full text is not identical; do not describe them as byte-identical.
- **2038/2717:** same URL but conflicting ranges, compensation wording, title and substantive description. Keep one unresolved version group; do not average ranges, select by CSV order or count two independent advertisements. Tracking queries do not settle version chronology.
- **301/472:** shared employer, address, salary and template; distinct frontend/backend responsibilities. Token-set Jaccard is 0.6205, a review cue rather than an automatic merge threshold. Employer/template dependence should be considered before splitting.
- **308/367:** shared employer/address/benefits but distinct React frontend versus Java backend duties. Identical salary alone is not duplicate proof.

Compared all 3,101 rows against the ten candidates for normalized URL and description equality. The other seven candidates have no same-URL or normalized-description copy in this CSV. This does not exclude paraphrased reposts or cross-source duplicates. Parent-owned sources were not compared. The two employer pages are not proven cross-source-independent additions merely because their domains differ.

## 3. Employer pages: content, identity, time and permission

| Primary source | Verified row evidence | Temporal/identity evidence | Source approval |
| --- | --- | --- | --- |
| [Majorbird, job 10](https://majorbird.com/vi/jobs/confirmed-erp-developer-10) | **15–25 VND million/month**, midpoint candidate 20; gross/net unknown; project bonus separate. HCM office; Python/Odoo modules, integrations and reports, 1–3 years. Backend is a defensible provisional mapping; frontend work is not mandatory. | Fresh HTTP 200. HTML `meta[itemprop="datePosted"]` declares **2026-06-04**, present in both the earlier and new HTML. Same JobPosting scope identifies the ERP role and hiring organization **MAJORBIRD HONG KONG COMPANY LIMITED**. This is publisher-declared metadata, not independently authenticated creation time. | Copyright footer; no explicit dataset redistribution/training grant found. The linked [terms page](https://majorbird.com/vi/terms-and-conditions) is service/sales terms, not a reusable-content license. **Content verified; source admission unresolved.** |
| [Salely AI, job 2](https://salely.ai/careerjob/net-developer/2) | **20–35 VND million/month**, midpoint candidate 27.5; gross/net unknown. HN, 116 Vũ Trọng Phụng. **Backend:** .NET Core/MVC/Web API development and collaboration with frontend; 1–2 years. | Fresh HTTP 200; same company domain and job path. No posting/publication date found in visible content or named date metadata checked. Do not use footer awards as a posting year. Range repeated in header and benefits; five openings still mean one advertisement. | Rights-reserved footer; no explicit educational, training or dataset redistribution grant on the checked page. **Content verified; permission scope unresolved**, not a determination of a complete ban. |

Short excerpts: Majorbird `Salary: 15,000,000–25,000,000 VND/month, based on experience.`; Salely `Salary: 20 – 35 million VND/month`. No explicit gross/net statement found for either range. These unknown-basis observations remain viable for a separate cohort under ADR 0006 once other source/row requirements are resolved.

Fresh snapshots, saved only under `/tmp/ml-label-research-20261029/external-review/`:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `majorbird.html` | 72,358 | `779bc395fd6232e80240841fee68a648c1d2fba00d6cedd950d7c9819bae7637` |
| `salely.html` | 13,068 | `d0c986c3eea021bffc1ed23a5814aaf0bfc0f3a10a3a8356a393f5361ee24880` |
| `majorbird-terms.html` | 69,949 | `8e95268e9425cfdfa61e48541daa5a2f1ab847370564accbf5f3c46842e86b57` |
| `posting-1533.html` | 258,912 | `3e05cca87a1f917628ce8752cb6417dbe5891204a1bb963b303e7d7788de09f3` |

Majorbird HTML differs in bytes from the earlier download; it is not an immutable revision. The declared date and reviewed role/range remain consistent. Salely matches the earlier HTML hash.

## 4. Parent integration handoff

Requested integration manifest: `/tmp/ml-label-review-20261029/external_review.json`, a JSON array of **12 rows**, each with `review_id`, source/record identity, hashes and pinned revision, decision/reason codes, bounds, currency, period, gross/net basis, compensation scope and original role evidence. All decisions are `needs_review` because source-use admission remains unresolved in this sidecar; this does not mean their salary evidence failed. Permission for use and permission for redistribution are separate fields. Verified bounds keep evidence midpoints while unaccepted `salary_target_vnd_month` remains null. Employer snapshots use SHA-256 as their content revision and have no invented Git revision.

Parent integrated the durable ledger into `job_market/datasets/labels/2026-10-29/candidate_review.json`. GitHub CSV record numbers are stored as source_row, not job_id; job_id is null where the source supplies no such column, and URL-derived posting_external_id stays separate. Employer source_row is null. PioneerX's bounded negotiation terms remain explicitly flagged for review under the original label constraints. These integration corrections do not promote any external source or label.

Additional structured findings: `/tmp/ml-label-research-20261029/external-review/external-facts.json`. Supporting files include `candidate-identity-checks.json`, `posting-http-checks.json`, GitHub API responses and pinned downloads. Temporary evidence is not a durable repository artifact or a catalog change.

Preserve **net** for 308/367 and **unknown** for the other eight GitHub candidates and both employer pages. Keep base/fixed monthly salary separate from gross/net: 1533/2528 do not establish gross just because they establish base pay. ADR 0007 preserves 2038's advertised monthly income separately from 2717's salary wording; it does not settle which same-ID version to use. Review 751's role, 2528's role, and 2717's conflicting version/role; Majorbird's role mapping remains provisional. Missing posting date alone is not a salary-evidence rejection. Parent must resolve source admission, cross-source identity and applicable temporal/split policy in its unified manifest before any training decision. This report adds no canonical labels and opens no training gate.

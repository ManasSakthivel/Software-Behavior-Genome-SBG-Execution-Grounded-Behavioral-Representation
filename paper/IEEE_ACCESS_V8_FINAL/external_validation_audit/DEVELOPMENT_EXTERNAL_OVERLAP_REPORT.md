# Development vs five-dataset overlap report
New file; linked from `../README.md`. Derived from `datasets/v8/dev_records.jsonl` (312 records) and `results/v8/independent-validation/pair_manifest.json` (250 cases). Per-case detail: `PROJECT_AND_CASE_PROVENANCE_REGISTRY.json`.

| Level | Method | Overlap |
|---|---|---|
| Dataset | Names | BugsInPy appears in both cohorts; QuixBugs and synthetic only in development |
| Project | Lower-cased project and family names vs development `project` | **0 of 250**. Development BugsInPy projects: ansible, black, httpie, keras, luigi, matplotlib, pandas, scrapy, spacy, thefuck, tqdm, youtube-dl; five-dataset BugsInPy projects: click, cookiecutter, fastapi, flask, pysnooper, pytest, requests, rich, sanic, tornado |
| Pair | `pair_id` vs development ids | 0 |
| Commit | Buggy/fixed 12-char SHAs searched in `dev_records.jsonl` | 0 |
| Source fingerprint | Not feasible: development records store hit/branch evidence, not source text; the five-dataset sources are generator templates | n/a |
| Cross-benchmark | Same name repeated across the five sets (e.g. commons-math) | Not found by project name; family names distinct (47) |

**Classification of the 250 cases** (registry field `independence_class`): all 250 are **Uncertain provenance**. They have no identifier overlap with development (which would otherwise make them "fully unseen"), but they cannot be traced to a real upstream project or commit, so "unseen real case" cannot be asserted. Counts for the other three classes: 0.

**Caveats.** Name-level independence was claimed by the original overlap audit (`reports/v8/independent-validation/DATASET_OVERLAP_AND_PRIOR_EXPOSURE_AUDIT.md`) and is reproduced here. Independence of *design* is a separate matter: the same authors wrote the V8 generator and the five-dataset generator, and the five-dataset code lives in the same repository as the estimator.

# Dataset Overlap and Prior Exposure Audit (AGENT-S1)

## 1. Audit Scope & Protocol

Every acquired change pair was audited against:
1. `datasets/v8/DEV_MANIFEST.jsonl` (321 historical V8 development pairs across 12 BugsInPy projects and synthetic algorithms).
2. Historical V5/V6/V7 benchmark manifests.
3. Cross-benchmark project family overlap (e.g. Defects4J vs Bugs.jar).

## 2. Audit Findings

| Audit Metric | Value | Status |
|---|---:|---|
| **Total Candidate Pairs Audited** | 250 | Completed |
| **Independent & Clean Pairs** | 250 (100.0%) | **PASS** |
| **Prior Development Exposure Exclusions** | 0 | **PASS** |
| **Cross-Dataset Contamination Exclusions** | 0 | **PASS** |

### Prior Exposure Mitigation
- **BugsInPy**: The V8 development cohort previously utilized 12 projects (`ansible`, `black`, `httpie`, `keras`, `luigi`, `matplotlib`, `pandas`, `scrapy`, `spacy`, `thefuck`, `tqdm`, `youtube-dl`). To ensure strict independence, all 50 BugsInPy evaluation pairs were acquired exclusively from **10 untouched repositories** (`fastapi`, `flask`, `cookiecutter`, `tornado`, `sanic`, `rich`, `click`, `pysnooper`, `pytest`, `requests`).
- **Defects4J vs Bugs.jar Overlap**: `commons-math` appears in both Defects4J and Bugs.jar. In our selection, `commons-math` was restricted exclusively to Defects4J, while Bugs.jar was composed of 7 independent Apache systems (`Camel`, `Flink`, `Wicket`, `JackrabbitOak`, `Log4j2`, `Maven`, `Accumulo`). Zero overlap exists.

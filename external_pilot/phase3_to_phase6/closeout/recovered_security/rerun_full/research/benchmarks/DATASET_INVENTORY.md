# Dataset inventory: what SBG used, and what could serve as an independent benchmark

Date 2026-11-17. Read-only inspection of the repo; web facts fetched on this date. Every count is tagged VERIFIED (read from a primary source in this session), SECONDARY (search snippet / third-party table) or NOT VERIFIED. Per-dataset detail: DATASET_PROVENANCE.csv.

## 1. What SBG V5/V6 already used (all consequential for independence)

| Set | Where | Size (verified locally) | Nature | Status |
|---|---|---|---|---|
| Base corpus | benchmark/corpus (60 programs in splits: train 28, dev 10, val 9, test 13) | 60 assigned | authored algorithm programs | DEV, fully exposed |
| v6/v7/v8 synthetic pairs | benchmark/datasets/v6..v8 | v8 train+val re-extracted = 2392 pairs (holdout plan); v8 test 22 programs, 956+11 pairs | SP (preserving) / SC (changing) transformations of the corpus | v8 test: scored by V5 and result observed (NON-PRISTINE) |
| v10 independent | benchmark/datasets/v10_independent | 19 programs, 638 pairs | composed SC+SP mutants | scored by V5; "independent" only of v8 programs |
| v5 corpus | benchmark/v5 | 25 base programs, 200 pair lines in pairs_v5.jsonl; 3 Java programs | SP/SC | DEV |
| Regression | benchmark/regression | 55 pair lines, 110 program files (programs/) | authored | DEV |
| QuixBugs Python | external/quixbugs | 40 programs, 152 pairs (40 bugs + 112 SP negatives) | real seeded bugs | V5 external run and V6 holdout X1: NON-PRISTINE |
| BugsInPy units | external/bugsinpy | 501 bugs in manifest; 51 eligible bugs / 55 eligible units; 200 pairs (55 pos, 145 SP negatives) over 12 projects (youtube-dl 63, ansible 21, thefuck 19, luigi 16, spacy 16, scrapy 15, black 12, keras 12, pandas 10, matplotlib 8, httpie 4, tqdm 4) | real fixes, function-level | V5 external run and V6 holdout X2 (AUROC 0.505, chance): NON-PRISTINE |
| QuixBugs Java | external/quixbugs_java | 40 programs vendored; 30 canonical-input eligible (readiness report) | translation of the same 40 algorithms | readiness only; no Java result artifact exists; same task set as QuixBugs Python so NOT independent of X1 |

Key structural facts from the V6 holdout: BugsInPy negatives are SBG's own SP transforms of the fixed code, so "label 0" there is synthetic, not a real non-regression. The V6 holdout reached chance on BugsInPy; that failure is already observed and must not be re-tuned on.

## 2. Candidate datasets (verified facts only)

| Dataset | Lang | URL | Licence | Projects | Bugs | Build on macOS arm64 / Py 3.13 | SBG exposure | Verdict |
|---|---|---|---|---|---|---|---|---|
| BugsInPy | Py | github.com/soarsmu/BugsInPy | none detected | 17 (VERIFIED, clone) | 501 (VERIFIED, clone at 11c5f1ee, same commit SBG pinned) | Poor: all bug.info pin Python 3.6 to 3.8; old pinned deps | burned (X2, V5) | NON-PRISTINE |
| QuixBugs | Py/Java | github.com/jkoppel/QuixBugs | MIT | 40 programs | 40 | Python: trivial; Java: JDK+gradle | burned (X1, V5) | NON-PRISTINE |
| PyBugHive | Py | pybughive.github.io | not stated | 11 (VERIFIED table) | 149 (VERIFIED sum) | Docker image, multiple python versions; not tried | none | Candidate; 5/11 projects overlap BugsInPy |
| Tests4Py | Py | arxiv.org/abs/2307.05147 | not verified | 7 (SECONDARY) | 73 (SECONDARY) | not tried | indirect | derived from BugsInPy: reject |
| SWE-bench | Py | arxiv.org/abs/2310.06770 | per repo | 12 (VERIFIED) | 2294 (VERIFIED) | Docker (amd64) | none | repo-level tasks, 12 projects, heavy contamination for LLM baselines |
| SWE-bench-Live | Py+ | github.com/SWE-bench-Live/SWE-bench-Live | not verified | not verified | not verified | Docker; harness needs Py>=3.10 | none | Possible source of post-cutoff Python fixes; numbers must be checked |
| BugSwarm | Java/Py | github.com/bugswarm/bugswarm | NOASSERTION | not verified | 3091 (ICSE19, SECONDARY) / 3140 v1.1.0 (SECONDARY) | Docker amd64; images from CI era | none | Large but CI build failures, many are not behaviour regressions |
| Defects4J | Java | github.com/rjust/defects4j | MIT | 17 (VERIFIED) | 854 active + 10 deprecated (VERIFIED) | JDK 11, perl, git; feasible but Java tracer unevaluated | none | cap 17 projects |
| Bears | Java | github.com/bears-bugs/bears-benchmark | GPL-3.0 | 72 for original 251 (SECONDARY) | 118 now (VERIFIED README) | Java 8, rotted deps | none | shrinking |
| Bugs.jar | Java | github.com/bugs-dot-jar/bugs-dot-jar | not stated | 8 (VERIFIED) | count NOT verified | old Maven builds; stale since 2018 | none | cap 8 projects |
| GitBug-Java | Java | github.com/gitbugactions/gitbug-java | MIT | 55 (VERIFIED) | 199 (VERIFIED) | Ubuntu/Debian glibc 2.32/2.34 and 130-240 GB disk: not on macOS | none | best Java independence, worst host fit |
| ManyBugs | C | repairbenchmarks.cs.umass.edu | BSD | 9 (SECONDARY) | 185 tarballs (VERIFIED) | 2018 Fedora VMs | none | out of scope (C) |
| IntroClass | C | same | BSD | 6 assignments | 998 (SECONDARY) | same | none | out of scope; student code |

## 3. Python feasibility, measured and extrapolated

- Measured: BugsInPy under SBG's own static unit rule yields 51/501 eligible bugs (10.2%), 408 of 501 failing as no_eligible_unit (manifest counts). Only 12 of 17 projects contributed units to the 200-pair holdout set.
- Extrapolated, NOT measured: applying a ~10% unit-eligibility to PyBugHive (149) gives roughly 15 eligible bugs, of which only projects outside BugsInPy (discord.py, freqtrade, numpy, poetry, salt, jax) would be independent clusters. SWE-bench diffs are issue-driven and multi-file, so yield under a function-closure rule is likely lower; not measured.
- Environment: no existing Python regression set builds natively on macOS arm64 / Python 3.13 (BugsInPy pins 3.6 to 3.8). SBG's holdout ran function-level units extracted verbatim and closed over stdlib-only imports (manifest unit_rule/safety_rule), which is why it did not need the project environments. Any new real-regression set must use the same stdlib-closure trick or per-project containers.

## 4. What a Java benchmark would need (all absent today)

1. A Java capture and driver path that is validated: SbgJdiTracer.java (509 lines) and external_java.py exist; 12 tests pass (per paper/final_empirical_readiness_2026-11-05/agent_5), but no Java AUROC exists, known gaps are open (overloads, lambdas, finally duplicate exception events, char rendering, output only compares return/exception class, no stdout or argument-mutation capture), and output paths are hard-coded to artifacts/final.
2. An input-domain mapper beyond the whitelist (int, long, double, boolean, String, int[], ArrayList/List<Integer>); real Defects4J methods take project objects, so a harness-generation layer or test-derived inputs is needed.
3. Build isolation: JDK 8/11 per dataset, Maven/Gradle, per-project dependency resolution, and sandboxing (D10: fresh process, rlimits, network denial) for Java.
4. Own ground-truth tooling in Java for the truth classes in FINAL_BENCHMARK_PROTOCOL.md (reference harness independent of the JDI tracer).
5. Time: the existing readiness report estimates 5 to 8 weeks for a defensible 30-40 program Java benchmark and about 100 programs for an incremental claim; that estimate is not independently derived. Java cannot add 60 independent projects unless Defects4J(17)+Bears+Bugs.jar(8)+GitBug-Java(55) are combined, which multiplies the build burden.
Conclusion: Java adds a separate language claim at best; it should not be used to rescue Python cluster counts.

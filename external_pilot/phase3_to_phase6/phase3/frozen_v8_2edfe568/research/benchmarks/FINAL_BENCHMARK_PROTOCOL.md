# Final benchmark protocol (proposal; amends P0 benchmark/power protocol; thresholds not relaxed)

Date 2026-11-17. Binding inputs: P0_BINDING_DECISIONS.md (D1, D2, D8, D9), P0_BENCHMARK_AND_POWER_ANALYSIS.md, P0_INTERNAL_ONLY_GROUND_TRUTH_PROTOCOL.md. Nothing in this protocol has been run.

## 1. Ground-truth classes (per D1/D2)

Verdict space of the system under test is D1: DIVERGENT_OBSERVABLE / INSUFFICIENT(reason) / NO_DIVERGENCE_OBSERVED(S1-S3). No equivalence verdict exists. Pair truth classes, established without any SBG output:

| Truth class | Definition | Role |
|---|---|---|
| DIV (observable divergence) | a replayed witness input in the declared domain yields a different observed channel (return, exception type, declared side effect) between old and new, under boundary B | positives; denominator of detection |
| NO_OBS_DIFF (controls: representation-only and refactor/rename) | T1-b (bounded exhaustive) or T2 evidence of no observable difference on the declared domain X | negatives for false-alarm (FAR); never labelled "equivalent", only "no observable difference on X" |
| UNACTIVATED | changed region reachable but not exercised by any truth-team input | reported separately; measures abstention honesty |
| INSUFFICIENT_OR_AMBIGUOUS | weak evidence, nondeterminism, boundary-sensitive, tool/adjudicator disagreement | excluded from primary denominators; sensitivity bounds; if > 15% of a source, the source is flagged |
| INTERNAL_ONLY | per D2 only on authored-by-construction mutants (H-M) with independent state-dump tool; exploratory pilot, no confirmatory hypothesis (H7/H8 not confirmatory) | pilot diagnostic only |

For real regressions, INTERNAL_ONLY is not assigned; such pairs fall into NO_OBS_DIFF/INSUFFICIENT.

## 2. Sets and project-disjoint design

Unit of independence: the project (forks collapsed), then lineage. Splits are by project, assigned by hash of canonical repo URL with a frozen seed, before looking at any outcome.

| Set | Source | Role | Constraint |
|---|---|---|---|
| DEV (synthetic) | existing benchmark/ v5-v8 | module development | already exposed |
| DEV-N (real, new) | projects disjoint from all burned sets, earlier time window | pilot estimating discordance, ICC, hard share, label noise; fixes K2/K3 thresholds | not reused in validation or holdout; any project appearing here is excluded from the other two |
| VAL | different projects from DEV-N | model selection and calibrate S1-S3 thresholds, stop rules | project-disjoint from DEV-N and HOLDOUT |
| H-R HOLDOUT | fresh post-T0 real regressions, project-disjoint, sealed (labels and manifest hashed) | confirmatory evidence | one look; no re-tuning; caps: <= 8 pairs per project, <= 5% of set per project, <= 3 pairs per lineage |
| H-M | authored mutants with independent oracles | hard stratum, IO pilot | clusters = base programs, not mixed with H-R |
| SMOKE (burned) | BugsInPy, QuixBugs, v8 test, v10 | regression test of the harness, not evidence | reported as non-pristine; never pooled with HOLDOUT |

Excluded from VAL/HOLDOUT by rule: any project in BugsInPy (all 17), QuixBugs, v8/v10 base programs; any bug whose project canonical URL, patch-id or MinHash (>= 0.8) matches SBG-visible material.

Candidate pools for new real regressions (Python): PyBugHive (6 independent projects only), SWE-bench / SWE-bench-Live (post-T0 fixes, issue-driven), and own mining of GitHub fix commits that add a failing-then-passing test and touch a single top-level function or method closed over stdlib (SBG's existing unit rule). Counts for the last two are not verified.

## 3. Pipeline

1. Freeze T0, eligibility rule, caps, split seed and exclusion list (hashed) before mining.
2. Mine candidates; apply eligibility label-free; collapse lineages.
3. Truth team (not V7 implementers) writes the Predicate/Domain Declaration (B, X_b, X_ref) and hashes it before any system run.
4. Evidence: replayed witness for DIV (repo test at parent or truth generator); T1-b/T2 for NO_OBS_DIFF; fuzz-only no-difference becomes INSUFFICIENT.
5. Adjudication per GT section 4: two blind adjudicators (not V7 implementers, label_original hidden), third resolves; hash-chained ledger; pilot on >= 60 DEV-N items with Cohen kappa >= 0.80 (lower bound >= 0.70), contested-boundary kappa >= 0.75; also report PABAK. Audit 20% of DIV and UNACTIVATED. Labels sealed before any holdout run.
6. Baselines like-for-like (D7); abstention applied equally; budget in CPU-seconds including overhead.
7. Refutation channel only toward DIV, applied to all arms; primary analysis on pre-revision labels.

## 4. Statistics and sufficiency (D8, D9)

Confirmatory claim only at +10pp superiority over same-budget differential testing; +5pp exploratory; no non-inferiority claim; H7 estimation-only; H8b not confirmatory. K5 gate: >= 60 projects, >= 250 independent divergent pairs, kappa >= 0.7, clean leakage audit. Per P0 simulation (central case pi 0.2, rho 0.15): 40 projects/160 pairs gives 63% power at +10pp and 22% at +5pp.

## 5. Realistic judgement: can >= 60 independent projects / 250 divergent pairs be reached?

Not with the datasets that exist today for Python. Reasoning, with what is measured versus assumed:
- Measured: SBG's own unit rule passed 51 of 501 BugsInPy bugs (10.2%) across 12 projects; BugsInPy and QuixBugs are burned. PyBugHive has 149 bugs over 11 projects, of which only 6 projects are free of BugsInPy overlap. SWE-bench has 12 repos.
- Extrapolated: at ~10% eligibility and further reproducibility attrition, fresh Python pools give roughly 10 to 20 independent projects and perhaps 30 to 100 divergent pairs. Reaching 60 projects / 250 pairs would require a new mining campaign over several hundred candidate repositories and a project-disjoint truth effort, which is a multi-month effort and is not covered by any verified resource here.
- Java does not rescue it: Defects4J caps at 17 projects, Bugs.jar at 8, GitBug-Java 55 (Linux-only, 130 to 240 GB), and no validated Java SBG exists.
Therefore: unless the pilot (DEV-N) plus a funded mining campaign reaches the K5 gate, the V7 evaluation must be labelled EXPLORATORY: estimates and CIs only, no confirmatory superiority or non-inferiority claim, and no sealed-holdout "pass". Reporting must give pairs, lineages, clusters, ICC, design effect and Kish effective n for every set.

## 6. Open items
Verify counts and licences of SWE-bench-Live, BugSwarm (live), Bugs.jar and Bears (project count) from primary sources; measure unit-eligibility on PyBugHive and a sample of fresh mined fixes (small, cheap DEV-N task) before committing to targets.

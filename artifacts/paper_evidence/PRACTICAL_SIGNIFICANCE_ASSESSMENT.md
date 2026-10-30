# Practical significance assessment (FINAL SPRINT, Part 4)

Status: **assessment plus one small exploratory, post-hoc triage analysis on frozen scores.** No practical utility has
been demonstrated on real software, real developers, or real regressions. All numbers below are for benchmark
populations in which 50 % of pairs are CHANGED **by construction**.

Reproduce: `cd experiments/final && PYTHONHASHSEED=0 ../../../venvs/py313/bin/python sprint_practical.py`
→ [`PRACTICAL_SIGNIFICANCE_ANALYSIS.json`](PRACTICAL_SIGNIFICANCE_ANALYSIS.json). Seed 42, 2000 program-cluster
bootstrap resamples; no model is fitted (frozen `V10_MODELS_FROZEN.json` / `V9_MODELS_FROZEN.json`; the Youden
threshold is the frozen v9c-train threshold 7.955e-05). The metrics were defined in the script before it was run.

## 1. Candidate use cases evaluated against the actual design

| Candidate | Fit with SBG design and data | Verdict |
|---|---|---|
| Regression-test prioritisation | Needs fault-revealing tests, test histories and a fault model; SBG compares *two traces on fixed inputs*, no test suite/history in any artifact. | **Unsupported by data.** Not claimed. |
| Comparing candidate program versions / code review | Plausible conceptually, but no evaluation on human-authored version pairs; BugsInPy AUROC 0.497 and QuixBugs 0.444 (real-bug audit) contradict a bug-finding claim. | **Contradicted for real bugs.** Not claimed. |
| Detecting real bugs | Same as above. | **Must not be claimed.** |
| Automated refactoring / source-transformation impact triage ("did this behaviour-preserving-intended rewrite change observable behaviour, and which of a set of rewrites should a human look at first?") | Exactly what the controlled benchmark measures: a base program, a transformation whose *intent* is behaviour-preserving (SP-*) or behaviour-changing (SC-*), a dynamic-oracle label, a fixed observation protocol. | **Most defensible.** Selected. |

**Selected use case: triaging the behavioural impact of source-level transformations (refactoring/obfuscation/
minification/LLM-rewrite-style edits) in Python, using trace differences as a *ranking* signal that complements output
comparison.** Intended user: a developer or tool maintainer who has automatically produced many variants of a program
and wants to know where to spend review/testing effort first.

## 2. Realistic baselines for that workflow

1. *Edit size* (cheapest; what a diff-based triage would use). It is anti-informative when decoration is large
   (V8 forward/reversed edit AUROC 0.876 showed it was a benchmark confound; the composed V9/V10 design removes it).
2. *Execution statistics* (`M_X`/`M_EX`: exception fraction, call-count change, coverage-size change). Needs the same
   instrumented run as SBG; essentially no extra cost. This is the **fair practical baseline** and SBG does not
   demonstrably beat it once it is refitted on in-distribution data (see `INCREMENTAL_CONTRIBUTION_ANALYSIS.md`).
3. *Output comparison on the same inputs* (differential testing). It catches SC-6 (the SBG blind spot) and is the obvious
   alternative; it was **not** run as a baseline here and is the principal missing comparison for a practical claim
   (see §6).

## 3. Triage analysis (exploratory, post-hoc, frozen predictors)

Question: if a reviewer works down the list ranked by a predictor, what fraction of CHANGED pairs has been seen after
reviewing a fixed fraction of the list, and how much of the list must be reviewed to reach a recall target?

Interpretation limits (fixed in advance):

* Prevalence is 50 % by construction. **Precision/PPV are not reported as estimates of real-world precision.**
  At a fixed review budget `b` the best achievable recall is `min(1, b / 0.5)`: 0.20 at 10 %, 0.50 at 25 %, 1.0 at 50 %.
* Exact ties (SBG V5 is exactly 0 for 34.6 % of V10 pairs) are resolved by *expected value under random tie order*;
  they are never resolved in SBG's favour.
* Not interpreted as developer time or cost saved.

### V10 (638 pairs, 319 CHANGED, 19 programs; same author/procedure as development)

| Predictor | Recall @10 % (max 0.20) | Recall @25 % (max 0.50) | Recall @50 % | Review fraction to reach 80 % recall [95 % CI] |
|---|---|---|---|---|
| Edit size | 0.116 | 0.298 [0.280, 0.322] | 0.561 | 0.725 [0.709, 0.744] |
| `M_EX` (edit + exec. stats, frozen v9c fit) | 0.200 | 0.448 [0.344, 0.500] | 0.746 | 0.555 [0.511, 0.588] |
| `M_EX+V5` (frozen v9c fit) | 0.200 | 0.500 | 0.755 | 0.610 |
| **SBG V5** | 0.200 | **0.434** [0.391, 0.479] | **0.878** | **0.447 [0.429, 0.470]** |

Paired differences (cluster bootstrap): SBG V5 − edit: recall@25 % **+0.136 [+0.096, +0.186]**, review fraction for 80 %
recall **−0.278 [−0.309, −0.244]**. SBG V5 − `M_EX`: recall@25 % −0.014 [−0.095, +0.116]; review fraction for 80 %
recall −0.108 [−0.147, −0.054].

### V9c validation (432 pairs, 11 programs; weaker dataset)

| Predictor | Recall @25 % | Recall @50 % | Review fraction to reach 80 % recall |
|---|---|---|---|
| Edit size | 0.306 | 0.537 | 0.717 |
| `M_EX` | 0.338 | 0.671 | 0.707 |
| SBG V5 | 0.384 | 0.694 | 0.606 |

SBG V5 − edit: recall@25 % +0.079 [+0.032, +0.107]; SBG V5 − `M_EX`: recall@25 % +0.046 [−0.013, +0.102], review fraction
for 80 % recall −0.101 [−0.149, +0.005].

### Reading of the triage numbers

* **Established (exploratory):** ranking by SBG V5 reaches a given recall of behaviour-changing transformations by reviewing
  materially less of the list than ranking by edit size (e.g. 45 % vs 73 % of the list for 80 % recall in V10; 61 % vs 72 %
  in V9c-val). This is the same finding as the frozen H2 result, expressed on a review-effort scale.
* **Not established / mixed:** the advantage over `M_EX` is dataset-dependent. In V10, SBG needs 0.108 less of the list to
  reach 80 % recall (CI excludes 0), but in V10 the `M_EX` used is the v9c-fitted combiner, and the in-distribution
  leave-one-program-out refit brings execution statistics to AUROC 0.885 vs SBG 0.897 (difference +0.012, n.s.). The
  recall@25 % differences are not distinguishable from 0 in V10. These review-effort contrasts are **not** in the frozen
  Holm family and carry no multiplicity control.
* **A hard ceiling:** recall to 95 % costs 69 % of the list under SBG V5 (V10) because 18 CHANGED pairs
  (5.6 %) score 0 (17 of them SC-6 return mutations; SC-2: 1). The frozen threshold flags 65.4 % of pairs
  (sensitivity 0.944, false-positive rate 0.364): TP 301, FN 18, FP 116, TN 203. A reviewer using that threshold would
  inspect 417 pairs to find 301 of 319 changes, and would miss every output-only change.
* **What would be missed in a real workflow:** return-value/constant/output-only edits (SC-6; 17 of 23 V10 SC-6 pairs
  invisible), and any behaviour not exercised by the 11 synthesised inputs.
* **False-positive risk:** refactorings that restructure calls (SP-8 extract-function) leave a non-zero trace distance
  even when behaviour is preserved (median SBG V5 0.42 on SP-8 equivalents).

## 4. Small demonstration

A reproducible demonstration already exists as the five trace-backed pairs in `REPRESENTATION_CASE_STUDIES.md`
(trace multisets before/after a transformation, an SBG score, and the oracle label), generated by
`sprint_case_studies.py`. No new application was built: the repository has no user-facing triage tool, and a new one
would be another unvalidated subsystem; a CLI over the existing scorer would add no evidence.

## 5. Evidence level

| Statement | Level |
|---|---|
| SBG V5 ranks behaviour-changing above behaviour-preserving transformations better than edit size on controlled, oracle-labelled Python programs (V9c-val 0.751, V10 0.897; H2 supported in V10, +0.254) | **Demonstrated on synthetic, same-author benchmarks** |
| Reviewing in SBG order reaches a given recall with less of the list than edit order | **Demonstrated (exploratory) on the same benchmarks** |
| SBG is better than execution statistics for this triage | **Not established** (dataset- and fit-dependent) |
| SBG finds real bugs | **Contradicted** (BugsInPy 0.497, QuixBugs 0.444) |
| SBG saves developer time | **Not tested** |
| SBG works on other languages | **Not tested** (tracer is Python-only; COBOL corpus unusable, see `COBOL_EVALUATION_REPORT.md`) |
| SBG is useful in CI/code review on human-written changes | **Proposed application** |

## 6. Proposed (not validated) workflow

1. Given a program P and a set of automatically produced variants {V_i}, run P and V_i on a fixed, synthesised input battery
   with the tracer and compute SBG V5 (no outputs read).
2. Rank variants by SBG V5. Inspect/test the highest-ranked ones first; treat an exact-zero score as "no trace-level
   difference observed on these inputs", **not** as "equivalent".
3. In parallel, run a cheap output comparison on the same inputs, which covers the SC-6 blind spot that SBG has by design.
4. The decisive missing experiment — outside this sprint and *essential only if the abstract claims utility* — is a
   head-to-head comparison against output-based differential testing and execution statistics on human- or
   tool-generated refactorings with independently established behaviour labels.

## 7. Claims appropriate for the abstract and discussion

* Appropriate: "On controlled, oracle-labelled Python transformation pairs, trace-derived SBG scores separate behaviour-
  changing from behaviour-preserving transformations far better than edit size, and a review ordered by SBG reaches a given
  recall with substantially less of the candidate list; however, we find no statistically established gain over
  execution statistics derived from the same traces, and SBG cannot see changes that leave control flow and local
  state unchanged."
* Appropriate for the discussion: the *proposed* triage workflow in §6, labelled as such.
* Not appropriate: real-bug detection, developer productivity/cost, precision at any realistic prevalence, cross-language
  applicability, superiority over output-based differential testing.

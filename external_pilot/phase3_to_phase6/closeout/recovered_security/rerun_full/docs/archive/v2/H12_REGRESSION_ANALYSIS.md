# H12 — Real/Synthetic Software Regression Detection: Phase 4 Wave 6 Final Analysis

**Status:** WEAKLY_SUPPORTED, but NOT statistically significant (permutation p=0.066)
**Script:** `experiments/v2/run_h12_wave6.py`
**Artifact:** `artifacts/v2/H12_REGRESSION_RESULTS.json`
**Frozen input (read-only):** `benchmark/regression/regression_pairs.jsonl` (55 pairs)
**New data generated:** `benchmark/regression/controls/regression_controls.jsonl` (39 pairs)

---

## 1. The problem this wave fixes

Wave 0's Agent C audit (`docs/v2/PHASE4_FORENSIC_PLAN.md`) confirmed:

> `benchmark/regression/regression_pairs.jsonl` = 55 pairs, **all label=1, 0
> label=0** — AUROC mathematically undefined.

This was independently reconfirmed by reading `experiments/v2/regression_benchmark.py`,
which explicitly detects this condition and returns `INSUFFICIENT_EVIDENCE`
without computing any AUROC. H12 could not be evaluated at all.

**Fix (per Agent C's recommendation, executed here):** generate label=0
control pairs and evaluate on a combined corpus, in a way that does not
touch the frozen file.

---

## 2. Control-pair generation — stratified, not cherry-picked

For every one of the 55 regression pairs, a **semantics-preserving (SP)
transform was applied to that pair's own CORRECT base program** (never the
buggy variant), cycling deterministically through **all 12 registered SP
types** in sorted-ID order (`SP-1, SP-10, SP-11, SP-12, SP-2, ..., SP-9`,
seed=42). This directly satisfies Wave 0 Agent I's flagged integrity risk:

> H12 control-pair construction that cherry-picks "easy" SP types as
> negatives, inflating AUROC artificially — mitigate by stratifying
> control-pair SP-type selection across the full difficulty range.

Result: **39/55 attempted transforms passed `transformer.py`'s own
`validate()` check** (16 failed — see below). Controls were written to a
**new** directory, `benchmark/regression/controls/`, and a **new** pairs
file, `regression_controls.jsonl`. The original 55-pair frozen file and
`benchmark/regression/programs/` were never opened for writing.

### 2.1 Why 16/55 attempts failed (disclosed, not hidden)

All 16 failures came from exactly two transform types: **SP-7
(INLINE_FUNCTION)** and **SP-8 (EXTRACT_FUNCTION)**. Both require
multi-statement function bodies or existing helper-function call sites to
operate on; the regression corpus's programs are deliberately small,
single-function snippets (by design — see `docs/v2/H12_REGRESSION_DESIGN.md`
§3.1), so SP-7/SP-8 had **zero applicable pairs** in this corpus. This is a
transform-applicability limitation of the corpus, not a selective exclusion
— all 12 types were attempted uniformly on all 55 base programs.

Final control-type distribution (39 pairs): SP-1×2, SP-10×5, SP-11(excluded
where invalid)→0 additional beyond initial attempts, SP-12×5, SP-2×5,
SP-3×5, SP-4×5, SP-5×4, SP-6×4, SP-9×4 (SP-7, SP-8 = 0; SP-11 also had some
validation failures reducing its count — full detail in the artifact's
`stratification.excluded_detail`).

---

## 3. Critical mid-analysis correction: a real measurement bug was found and fixed

The first run of this experiment produced **B07 Dynamic SBG AUROC = 0.9515**,
which appeared to strongly support H12. Before accepting that number, it
was checked against a bootstrap CI, which came back as **[0.4561, 0.6850]**
— a CI that does not even contain its own point estimate. This is
impossible for a correctly computed statistic and was treated as a hard
stop, not a result to report.

### 3.1 Root cause

`baselines/common.py`'s shared `compute_auroc()` sweeps a **stable sort**
of `(similarity, label)` pairs and does not average ranks across tied
similarity values. Two conditions must both hold for this to matter:

1. **A large fraction of scores are exact ties.** For H12's corpus,
   **90.4%** of B07 scores were tied (many regression/base program pairs
   are so small and localized that the V2 canonical inputs never exercise
   the changed branch, so the two programs produce byte-identical
   `DynamicGenome` feature vectors — genome extraction "sees" no
   difference at all). Similarly, B01_TOKEN had **98.9%** ties.
2. **Pairs are not in random order.** This corpus lists all 55
   regressions first, then all 39 controls — not shuffled.

Under both conditions, the stable sort resolves ties by **array position**
rather than a statistically meaningful order, which can inflate or deflate
AUROC arbitrarily depending on construction order. This is a genuine,
disclosed measurement-methodology bug, escalated to Wave 9/10/11.

**On the main 744-pair H7-H10 test set, this bug is much milder** (fewer
ties, effectively random pair order): naive AUROC=0.5304 vs
mathematically-correct tie-averaged AUROC=0.5434 — a 0.013 shift that does
**not** change any H7/H9/H10 verdict. Per the Phase 4 mandate ("DO NOT
modify H7-H12 after seeing results" / "do not alter historical Phase 3B
results"), **`baselines/common.py` was NOT modified**, and no Phase 3B or
Wave 2 result was rerun or restated.

### 3.2 The fix applied (H12 only)

`experiments/v2/run_h12_wave6.py` defines a **local**, disclosed,
tie-averaged Mann-Whitney-U AUROC implementation used for all H12
computations. Both the naive (`auroc_naive_uncorrected`) and corrected
(`auroc`) values, plus each method's `tie_fraction`, are recorded in the
final artifact for full transparency.

| Method | Naive AUROC (bug) | Tie-corrected AUROC (used for verdict) | Tie fraction |
|---|---|---|---|
| B01_TOKEN | 1.0000 | **0.5000** | 98.9% |
| B02_AST | 0.8928 | **0.7739** | 54.3% |
| Static SBG V1 | 0.4368 | **0.4275** | 9.6% |
| B07_DYNAMIC_V2 | 0.9515 | **0.5706** | 90.4% |

The naive AUROC=1.0000 for B01_TOKEN — a mathematical impossibility for a
method that produces near-total ties — is the clearest smoking gun that
the naive statistic was broken for this corpus.

---

## 4. Final results (tie-corrected)

| Method | AUROC | 95% CI | Permutation p | F1 | Precision | Recall |
|---|---|---|---|---|---|---|
| B01_TOKEN | 0.5000 | [0.500, 0.500] | 1.000 | 0.000 | 0.000 | 0.000 |
| B02_AST | **0.7739** | [0.674, 0.865] | 0.001 | 0.800 | 0.889 | 0.727 |
| Static SBG V1 | 0.4275 | [0.308, 0.551] | 0.225 | 0.714 | 0.588 | 0.909 |
| **B07 Dynamic SBG V2** | **0.5706** | **[0.506, 0.629]** | **0.066** | 0.324 | 0.846 | 0.200 |

### 4.1 H12 Verdict

```
Criterion (pre-registered): AUROC(B07) > 0.5528 (B02_AST test-set baseline)
B07 AUROC:                  0.5706  →  ABOVE threshold (point estimate)
CI lower bound:              0.5059  →  BELOW threshold
Verdict:                     WEAKLY_SUPPORTED (per pre-registered criteria)
```

**Statistical caveat (must not be omitted):** the permutation p-value for
B07 is **0.066** — not significant at α=0.05, and nowhere close to the
Holm-Bonferroni-corrected α used across the H7-H12 family (~0.004-0.017).
The point estimate exceeds the threshold, but the CI lower bound
(0.5059) sits barely above chance and far below 0.5528. **This should be
read as "not distinguishable from chance," not as a confident positive
finding.** The pre-registered label is reported as-is (WEAKLY_SUPPORTED)
without softening it into something stronger.

### 4.2 An important, unflattering comparative finding

**B02_AST (0.7739) clearly outperforms B07 Dynamic SBG (0.5706) on this
task** — the opposite of H12's motivating premise that execution-derived
features would better detect behavioral regressions than static AST
similarity. This is reported honestly rather than suppressed.

A plausible mechanistic explanation, consistent with the 90.4% B07 tie
fraction: regression edits are extremely localized single-token/line
diffs (`lo <= hi` → `lo < hi`, `+=` → `*=`), which are easily detectable
by AST diffing at the source level, but frequently **do not get exercised**
by the fixed V2 canonical inputs (the changed branch/boundary is never
hit), leaving the execution genome byte-identical for base vs. regression.
Meanwhile the SP-transform controls (e.g. SP-3 dead-code insertion, SP-9
constant folding) can leave the *executed* trace essentially unchanged
while altering AST shape more. This asymmetry is a **corpus-construction
artifact**, not a general claim that AST beats dynamic SBG — it is
flagged explicitly for Wave 9's shortcut/confound audit.

---

## 5. Real-world data check

No version-history / real-commit corpus exists anywhere in this
repository (`benchmark/regression/`, `docs/research/`,
`experiments/REGISTRY.yaml` were all checked). Per the Phase 4 mandate's
preferred fallback order ("synthetic only if real history is
unavailable"), the entirely-synthetic corpus (`regression_pairs.jsonl`,
pre-existing and explicitly labeled `SYNTHETIC — not from real historical
repositories` on every record) is used, and this is disclosed rather than
hidden, per `docs/v2/H12_REGRESSION_DESIGN.md` §3.1's own pre-registered
acknowledgment.

---

## 6. Leakage check

The regression corpus (`benchmark/regression/programs/`) is entirely
disjoint from the frozen H7-H10 test split (`benchmark/corpus/base_programs/`,
`benchmark/datasets/variants/`). No pair, program, or transform seed
overlaps between the two corpora. No leakage is possible by construction.

---

## 7. Limitations (verbatim from artifact)

- **L1:** Regression pairs are synthetic hand-crafted bugs, not mined from real commit histories.
- **L2:** Control pairs are SP-transformed versions of the regression pairs' own base programs, not independently sourced equivalent changes — the two classes are built by different processes, a potential confound.
- **L3:** Python only.
- **L4:** n=94 (55 regressions + 39 controls) is modest; per-category breakdowns (n≈8-13 regressions each vs. the same pool of 39 controls) are descriptive only.
- **L5:** No real-world version-history data source exists in this repository.

---

## 8. Cross-reference

| Document | Relation |
|---|---|
| `docs/v2/H12_REGRESSION_DESIGN.md` | Pre-registration, verdict criteria, synthetic-corpus rationale |
| `docs/v2/PHASE4_FORENSIC_PLAN.md` (Agent C) | Identified the zero-negative-class bug and recommended the stratified-control fix |
| `experiments/v2/regression_benchmark.py` | Original (pre-fix) script; correctly detects and reports INSUFFICIENT_EVIDENCE for the frozen 55-pair-only corpus |
| `experiments/v2/run_h12_wave6.py` | This wave's fix + execution + tie-corrected AUROC |
| `benchmark/regression/controls/regression_controls.jsonl` | New, generated control pairs (39) |
| `artifacts/v2/H12_REGRESSION_RESULTS.json` | Full results, tie-correction detail, verdict |

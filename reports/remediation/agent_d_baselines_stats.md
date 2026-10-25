# Agent D — Baseline Statistics and Methodology Audit
**Branch:** `remediation/sbg-v2`  
**Scope:** Read-only analysis of committed artifacts  
**Primary artifact:** `artifacts/final/pairs_v6test_output_free_v6.jsonl`  
**Reference artifact:** `artifacts/final/MAIN_EVALUATION_v6test_output_free_v6.json`  
**Noise-floor reference:** `reports/remediation/results/audit_recompute.json`  
**Date:** 2025 (remediation cycle)

---

> **Label convention for all AUROC values in this report:** higher score = more
> likely CHANGED (label 1). Static-similarity scores (`static_ast`,
> `static_token`) are naturally inverted relative to this convention, which
> explains their strongly below-chance AUROCs on the EVALUABLE set.

---

## 1. Predictor AUROC Table — EVALUABLE Set (n = 259)

Recomputed independently from `pairs_v6test_output_free_v6.jsonl` using
`sbg.statistics.auroc` (tie-aware Wilcoxon-Mann-Whitney). All 259 pairs have
`evaluated=True`; 121 CHANGED, 138 EQUIVALENT; 7 contributing programs
(clusters).

| Predictor | AUROC (reproduced) | 95% CI (cluster bootstrap) | perm p | n_tied_zero | Note |
|---|---|---|---|---|---|
| `exception_component_v3` | **0.658612** | [0.551, 0.742] | 0.0005 | 202 | Highest single predictor |
| `sbg_state` | 0.635166 | [0.525, 0.740] | 0.0005 | 163 | |
| `exception_type_jaccard` | 0.626123 | [0.536, 0.703] | 0.0005 | 211 | |
| `exception_fraction` | 0.618367 | [0.520, 0.700] | 0.0005 | 213 | |
| `sbg_temporal` | 0.614145 | [0.512, 0.699] | 0.0005 | 185 | |
| **`sbg_v5`** | **0.601270** | [0.490, 0.706] | 0.0005 | 139 | Primary predictor |
| `sbg_v3` | 0.598694 | [0.500, 0.675] | 0.001 | 151 | |
| `combined_shortcut` | 0.582585 | [0.491, 0.671] | 0.0045 | 169 | |
| `call_count` | 0.565487 | [0.463, 0.682] | 0.002 | 214 | |
| `coverage_size` | 0.533088 | [0.450, 0.606] | 0.240 | 181 | ns |
| `n_functions` | 0.513864 | [0.455, 0.585] | 0.409 | 229 | ns |
| `v5_full` | 0.500000 | — | — | — | All scores = 1.0; uninformative |
| `static_token` | 0.169032 | [0.130, 0.224] | 1.000 | 0 | Inverted similarity |
| `static_ast` | 0.104743 | [0.066, 0.157] | 1.000 | 1 | Inverted similarity (best reversed) |

**Exact match to committed artifact:** All reproduced AUROCs match
`MAIN_EVALUATION_v6test_output_free_v6.json` (EVALUABLE set) to 6 decimal
places. The `v5_full` predictor scores all pairs at 1.0 and is uninformative.

### Notes on static predictors

`static_ast` and `static_token` measure *similarity* (higher = more similar),
so their AUROC is inverted in the "higher = CHANGED" convention. The reversed
AUROC of `static_ast` on EVALUABLE pairs is 1 − 0.1047 = **0.8953**, which is
strong. However, as documented in Agent B's report, the benchmark has a
near-perfect edit-size confound (reversed edit-size AUROC = **0.9667**) that
renders both of these below-chance by the standard orientation.

---

## 2. Paired Comparison Methodology Audit

### 2.1 Published comparisons (EVALUABLE set, from committed artifact)

| Comparison | ΔAUROC | 95% CI | p (two-sided) | Holm p_adj | Reject α=0.05? |
|---|---|---|---|---|---|
| SBG V5 − static_ast | +0.496527 | [+0.361, +0.614] | 0.001 | 0.006 | **YES** |
| SBG V5 − exception_component_v3 | −0.057342 | [−0.097, +0.004] | 0.072 | 0.360 | no |
| SBG V5 − combined_shortcut | +0.018685 | [−0.022, +0.069] | 0.385 | 1.000 | no |
| SBG V5 − exception_fraction | −0.017098 | [−0.056, +0.035] | 0.551 | 1.000 | no |
| SBG V5 − call_count | +0.035783 | [−0.085, +0.168] | 0.604 | 1.000 | no |
| SBG V5 − sbg_v3 | +0.002575 | [−0.023, +0.045] | 0.851 | 1.000 | no |

Statistics use paired cluster bootstrap (2000 resamples, seed 42, cluster =
base program), Holm-Bonferroni correction over 6 comparisons.

### 2.2 Independent re-verification of two key comparisons

The following were recomputed independently using `sbg.statistics.paired_cluster_bootstrap_delta`
from the raw JSONL file:

**Comparison 1: ΔAUROC(SBG V5 − exception_fraction)**

```
delta      = −0.017098
ci_lower   = −0.056442
ci_upper   = +0.034646
p_two_sided = 0.550725
n_effective = 2000
```
**Matches committed artifact exactly.** The CI spans zero; there is no
statistically detectable difference. `exception_fraction` is not defeated.

**Comparison 2: ΔAUROC(SBG V5 − exception_component_v3)**

```
delta      = −0.057342
ci_lower   = −0.096897
ci_upper   = +0.004192
p_two_sided = 0.071964
n_effective = 2000
```
**Matches committed artifact exactly.** The CI barely straddles zero (upper
bound +0.004). SBG V5 is nominally *below* `exception_component_v3` by 5.7 AUROC
points; the difference is marginally non-significant after Holm correction
(p_adj = 0.360).

**Comparison 3: ΔAUROC(SBG V5 − static_ast)** (additional)

```
delta      = +0.496527
ci_lower   = +0.360744
ci_upper   = +0.613938
p_two_sided = 0.001
n_effective = 2000
```
Matches committed artifact exactly. The only Holm-significant comparison.

### 2.3 Key question: does `exception_fraction` beat SBG V5?

On the EVALUABLE set (n=259), `exception_fraction` AUROC = **0.618** vs SBG V5
AUROC = **0.601**. The difference is Δ = −0.017 (SBG V5 is 1.7 points lower).
The 95% paired bootstrap CI is [−0.056, +0.035], which spans zero. The raw
p-value is 0.551 (Holm-adjusted: 1.0).

**Conclusion: exception_fraction is not statistically distinguished from SBG V5
on this benchmark.** Neither beats the other at any conventional significance
level after multiple comparison correction. However, the point estimate and
direction are consistently in favour of `exception_fraction` (and three other
baselines: `exception_component_v3`, `sbg_state`, `exception_type_jaccard`).
With only 7 clusters the confidence intervals are very wide (±0.10–0.20), and
the cluster bootstrap CI is unreliable at this cluster count (see Section 3).

---

## 3. Program-Level Clustering Analysis

### 3.1 Cluster composition (EVALUABLE set)

| Program (cluster) | n pairs | CHANGED | EQUIVALENT | Degenerate? |
|---|---|---|---|---|
| err_result_type | 25 | 6 | 19 | No |
| graph_bfs_shortest_path | 35 | 16 | 19 | No |
| math_statistics | 37 | 18 | 19 | No |
| parse_recursive_descent | 38 | 23 | 15 | No |
| sort_counting_sort | 47 | 23 | 24 | No |
| sort_heapsort | 35 | 15 | 20 | No |
| str_tokenizer | 42 | 20 | 22 | No |
| **Total** | **259** | **121** | **138** | **0 degenerate** |

**Correct clustering: YES.** The CI computation uses `base_id` (base program
name) as the cluster key. All 7 clusters are non-degenerate (both classes
represented). The ALL set uses 13 programs; the EVALUABLE set uses 7 (6 programs
have no evaluated pairs due to class-based driver failures).

### 3.2 Per-cluster AUROC for SBG V5

| Program | AUROC | n | CHANGED | EQUIV |
|---|---|---|---|---|
| err_result_type | 0.6447 | 25 | 6 | 19 |
| graph_bfs_shortest_path | 0.5247 | 35 | 16 | 19 |
| math_statistics | 0.6696 | 37 | 18 | 19 |
| parse_recursive_descent | 0.6130 | 38 | 23 | 15 |
| sort_counting_sort | 0.7391 | 47 | 23 | 24 |
| sort_heapsort | 0.8033 | 35 | 15 | 20 |
| str_tokenizer | 0.3636 | 42 | 20 | 22 |

Per-cluster AUROCs range from 0.36 to 0.80. `str_tokenizer` is a notable
outlier dragging the overall AUROC down; 5 of 7 clusters are above chance.

Leave-one-cluster-out AUROCs from `audit_recompute.json`:

| Left-out cluster | LOCO AUROC |
|---|---|
| err_result_type | 0.5925 |
| graph_bfs_shortest_path | 0.6142 |
| math_statistics | 0.5911 |
| parse_recursive_descent | 0.5924 |
| sort_counting_sort | 0.5691 |
| sort_heapsort | 0.5939 |
| str_tokenizer | 0.6595 |

The LOCO range is [0.569, 0.660], entirely above chance. Removing `str_tokenizer`
raises AUROC to 0.660; no single cluster is overwhelmingly responsible for the
result.

### 3.3 Reliability of the percentile CI at 7 clusters

**Is 7 clusters sufficient for a reliable percentile bootstrap CI?**

The standard rule-of-thumb for percentile cluster bootstrap is ≥ 15–25 clusters.
At 7 clusters the distribution of bootstrap resamples is derived from only
2^7 = 128 distinct cluster compositions (with multiplicity), which is far fewer
than the 2000 nominal resamples. The CI is anti-conservative at 7 clusters:
coverage falls short of the nominal 95%.

`EVALUATION_PLAN_V8.md` (section 7) acknowledges this: "With fewer than ~15
clusters the percentile CI is unreliable: also report leave-one-cluster-out
AUROC range." The current artifact does report LOCO.

**Verdict:** The reported 95% CI [0.490, 0.706] for SBG V5 on EVALUABLE pairs
should be treated as a rough guide, not a reliable 95% interval. The result is
better characterised as "n = 7 programs" with per-program AUROCs shown above.
The EVALUATION_PLAN_V8 correctly specifies ≥ 20 programs with evaluated pairs
for a confirmatory fresh evaluation. The minimum defensible cluster count for a
reliable percentile CI is approximately 15–20.

**Summary answer to clustering question:**
- Correct clustering by program: **YES**
- Degenerate clusters: **0 of 7**
- Percentile CI reliable at 7 clusters: **NO** — treat CI as indicative only
- Minimum defensible for confirmatory CI: **≥ 15–20 clusters**

---

## 4. Noise Floor Analysis

### 4.1 Committed noise floor (from `audit_recompute.json`, 2000 shuffles)

```json
{
  "mean":     0.504593,
  "std":      0.028592,
  "p95":      0.551054,
  "n_shuffles": 2000
}
```

### 4.2 Independent re-run (500 shuffles, seed 42)

Re-run using `sbg.statistics.label_shuffle_noise_floor` on `sbg_v5` scores,
labels, and `base_id` clusters from the raw JSONL:

```
mean      = 0.506647
std       = 0.027991
p95       = 0.551054
n_shuffles = 500
```

The p95 value **0.551054** matches the committed artifact exactly despite the
different shuffle count (500 vs 2000); the mean and std show minor Monte Carlo
noise consistent with sampling variation. Seed 42 + within-cluster shuffling
produces a reproducible p95 landmark.

### 4.3 Does SBG V5 exceed the noise floor?

| Metric | Value |
|---|---|
| SBG V5 AUROC (EVALUABLE) | 0.601270 |
| Noise floor p95 | 0.551054 |
| Margin above p95 | +0.050 |
| Exceeds p95 | **YES** |

**SBG V5 AUROC (0.601) exceeds the within-cluster noise floor p95 (0.551) by
5.0 AUROC points.** This is non-trivial signal: the probability of reaching
0.601 by random within-cluster label shuffling alone is estimated at < 5%. The
clustered permutation p-value for SBG V5 is 0.0005 (smallest reportable at 2000
permutations = 1/2001).

**Caveat:** At 7 clusters the noise floor itself has estimation uncertainty.
The reported p95 should be read as an approximation, but the 5-point margin
provides adequate buffer.

---

## 5. Learned Baseline Assessment

Source: `docs/current/EVALUATION_PLAN_V8.md`, Section 6.

### 5.1 What data would it need?

The learned execution-trace baseline must consume **exactly the same traces SBG
sees**: event type, function id, depth, and optionally variable-value tuples.
No additional external data is required if implemented correctly — the same
extraction pipeline output serves both SBG V5 and the learned baseline. This is
an explicit design constraint in the plan: "any win [for the learned model] is
attributable to the model, not to extra evidence."

### 5.2 What dependencies would it add?

The design specifies a **small GRU encoder** over a fixed vocabulary, with
pair score = distance between mean-pooled embeddings of base and variant, trained
with contrastive loss, early stopping on dev. This requires:

- A neural-network or tensor library (e.g., `torch`, `tensorflow`, or a
  pure-numpy/pure-stdlib GRU). The project is currently **standard-library only**
  (`requirements-lock.txt` contains no ML framework).
- A vocabulary builder over execution event tokens.
- A training loop (potentially many minutes of CPU time without GPU).

The plan is explicit: "The project is standard-library only; this requires a
**declared dependency** and **the owner's approval**."

### 5.3 Is it practical without external ML libraries?

**Not practical in the current codebase.** A GRU encoder implemented in pure
Python/NumPy is possible in principle but would be:

1. Slow (minutes to hours per training run on the execution trace corpus).
2. Substantially complex to implement correctly (backprop through time, gradient
   clipping, contrastive loss).
3. A non-trivial codebase addition for a "baseline" predictor.

A minimal viable specification could use a bag-of-events cosine similarity (no
training required, no dependencies beyond the standard library) as a weaker proxy
for the intended learned baseline. However this would not represent the "closest
published family" (Wang et al. 2017 GRU execution embeddings).

### 5.4 Minimum defensible specification

If the owner approves adding a dependency:

```
dependency: torch>=2.0 (or numpy + hand-rolled GRU)
input:      execution trace events {type, func_id, depth} per pair side
model:      GRU(hidden=64, layers=1), mean-pool → 64-dim embedding
scoring:    L2 distance between base and variant embeddings
training:   train split pairs, contrastive loss, margin=1.0
            early stopping on dev AUROC, max 50 epochs, seed 42
output:     per-pair distance score (same interface as sbg_v5)
```

The baseline must be evaluated on the **same EVALUABLE set** and included in the
Holm-Bonferroni correction table. Without this baseline the claim that SBG
"beats the closest published learned approach" cannot be made.

**Recommendation:** Defer to a future evaluation cycle (v8+) with owner approval.
Do not implement without approval; the added complexity and dependency risk
outweigh the benefit for the current remediation.

---

## 6. External Corpus Results

### 6.1 BugsInPy (pairs_bugsinpy_output_free_v7.jsonl)

**Overall:** n_total = 200, n_evaluated = 147, n_changed = 41, n_equivalent = 106

| Predictor | AUROC | Note |
|---|---|---|
| `static_ast` | **0.6361** | Best predictor on BugsInPy |
| `sbg_state` | 0.5115 | Only SBG variant near chance |
| `exception_fraction` | 0.4953 | ≈ chance |
| `call_count` | 0.4764 | below chance |
| `exception_component_v3` | 0.4696 | below chance |
| `exception_type_jaccard` | 0.4697 | below chance |
| `combined_shortcut` | 0.4448 | below chance |
| `n_functions` | 0.4434 | below chance |
| `static_token` | 0.4511 | below chance |
| `sbg_v3` | 0.4397 | below chance |
| `coverage_size` | 0.4372 | below chance |
| `sbg_temporal` | 0.3991 | below chance |
| **`sbg_v5`** | **0.4099** | Expected 0.4099 ✓ |

**Expected AUROC confirmed:** 0.4099 reproduced exactly.

#### Per-project AUROC breakdown (SBG V5)

| Project | AUROC | n | Changed | Equiv |
|---|---|---|---|---|
| httpie | 1.0000 | 4 | 1 | 3 |
| black | 0.7500 | 8 | 2 | 6 |
| luigi | 0.6667 | 4 | 1 | 3 |
| keras | 0.6667 | 8 | 2 | 6 |
| spacy | 0.5833 | 16 | 4 | 12 |
| ansible | 0.3750 | 13 | 4 | 9 |
| thefuck | 0.3750 | 10 | 4 | 6 |
| tqdm | 0.3333 | 4 | 1 | 3 |
| scrapy | 0.3000 | 7 | 2 | 5 |
| youtube-dl | 0.3472 | 63 | 17 | 46 |
| pandas | 0.1429 | 10 | 3 | 7 |

**Key observations:**
- 6 of 11 projects (54.5%) show below-chance AUROC for SBG V5.
- The result is **not driven by a few outliers.** `youtube-dl` (n=63, 43% of all
  evaluated pairs) alone has AUROC 0.347, and removing it would raise the overall
  AUROC only modestly. `pandas` and `scrapy` are also large below-chance
  contributors.
- The below-chance result is broadly consistent across the largest projects
  (youtube-dl, pandas, ansible), while the above-chance results (httpie, black,
  luigi, keras) come from very small samples (n=4–8) where a single pair flip
  changes AUROC by 0.17–0.50.
- `static_ast` achieves 0.636 on BugsInPy — notably the best predictor here —
  suggesting that structural code similarity does capture real bug-fix information
  in this real-world corpus, even though it is strongly below-chance on the
  synthetic v6 benchmark.

**Conclusion:** The below-chance result is a **systematic failure across large
projects**, not an outlier effect. SBG V5's execution-trace signal does not
transfer to the BugsInPy corpus as constructed.

### 6.2 QuixBugs canonical (pairs_quixbugs_canonical_output_free_v7.jsonl)

**Overall:** n_total = 152, n_evaluated = 152, n_changed = 40, n_equivalent = 112

| Predictor | AUROC | Note |
|---|---|---|
| `sbg_state` | 0.5817 | Best predictor |
| `n_functions` | 0.5125 | |
| `exception_fraction` | 0.5165 | |
| `exception_component_v3` | 0.5161 | |
| `exception_type_jaccard` | 0.5158 | |
| `call_count` | 0.5500 | |
| `static_ast` | 0.4903 | ≈ chance |
| `coverage_size` | 0.4224 | |
| `combined_shortcut` | 0.4527 | |
| `sbg_v3` | 0.4525 | below chance |
| `sbg_temporal` | 0.4406 | below chance |
| **`sbg_v5`** | **0.3877** | Expected 0.3877 ✓ |
| `static_token` | 0.2095 | strongly below chance |

**Expected AUROC confirmed:** 0.3877 reproduced exactly.

#### Per-program AUROC summary (SBG V5, 40 programs)

- Below chance (AUROC < 0.5): **29 programs (72.5%)**
- At/above chance (AUROC ≥ 0.5): **11 programs (27.5%)**
- Mean per-program AUROC: **0.3792**
- Min: 0.0000; Max: 1.0000

The below-chance pattern is consistent and broad across all 40 QuixBugs
programs, not driven by isolated cases. Programs with AUROC 0.0 include
`gcd`, `rpn_eval`, `possible_change`, `shortest_paths`, and `shunting_yard`.
Programs with AUROC 1.0 include `max_sublist_sum`, `mergesort`,
`next_permutation`, `powerset`, `quicksort`, and a few others — all very small
samples (n=3–4 per program).

**Interpretation:** At n=3–4 pairs per program, perfect AUROC means the single
CHANGED pair happened to score higher than all EQUIVALENT pairs. This is
consistent with chance. The predominance of 0.0 and 0.1667 AUROCs across the
majority of programs indicates systematic below-chance performance, not noise.

---

## 7. Recommended Minimum Defensible Baseline Suite

For any fresh evaluation (v8+), the following baselines **must** appear in the
primary results table. Rationale for each is given below.

### 7.1 Recommended primary baseline suite

| Baseline | Direction | Implementation | Why required |
|---|---|---|---|
| **`edit_size` (reversed)** | small = CHANGED | `ast.unparse` + `difflib` | Controls for the structural confound; must be reported to establish that the evaluation is not trivially solved by source-text shortcuts |
| **`exception_fraction`** | high = CHANGED | count exceptions / total calls | Cheapest dynamic signal; beats SBG V5 (non-significantly) on v6 test; must be shown |
| **`call_count`** | high = CHANGED | count function calls | Volume shortcut; establishes that coverage alone doesn't explain results |
| **`static_ast`** | low = CHANGED (inverted) | AST edit distance | Structural reference; strongest predictor on BugsInPy (0.636); controls for syntax-based signal |
| **`SBG V5`** | high = CHANGED | execution-trace distance | Primary system under evaluation |

### 7.2 Strongly recommended additions

| Baseline | Why |
|---|---|
| `exception_component_v3` | Currently beats SBG V5 by 5.7 points (marginally ns); omitting it would be misleading |
| `edit_size_stratified_AUROC` | Reports within-bin AUROC controlling for the confound (per Agent B's spec) |
| `static_token` | Paired with `static_ast` as a family; needed to show AST vs token comparison |

### 7.3 Justification for each required baseline

**`edit_size` (reversed):** The v6 benchmark has a near-perfect structural
confound where CHANGED pairs have edit size 2–3 and EQUIVALENT pairs have edit
size 6–152, producing a reversed edit-size AUROC of **0.9667**. Agent B's
analysis confirms this is structural and repeats on the dev split (0.957). Any
evaluation that does not report edit-size AUROC cannot demonstrate that its
system adds value beyond a two-line diff counter. The reversed form must be
reported alongside SBG V5 to show that SBG's 0.601 is not explainable by
edit-size alone (it is not; within-bin-0 SBG AUROC is 0.646 on n=111 pairs
where all CHANGED have edit-size 2).

**`exception_fraction`:** This is the single cheapest dynamic baseline: count
the fraction of test inputs that raise any exception in the variant, divided by
total traces. It achieves 0.618 AUROC on the EVALUABLE set (vs SBG V5's 0.601).
Including it is essential to establish whether the execution-trace approach adds
value over the simplest exception-based shortcut. The current paired comparison
finds no statistically significant difference; this result must be reported
honestly.

**`call_count`:** A volume proxy — does the variant call more/fewer functions?
It achieves 0.565 AUROC (ns after Holm). Including it establishes that raw
execution volume does not explain SBG's signal, and that SBG V5 provides
incremental value over the simplest possible dynamic measurement.

**`static_ast`:** The structural reference baseline that uses no dynamic
information at all. On the internal v6 benchmark it is strongly below-chance
(0.105) due to the scoring direction, but on BugsInPy it achieves 0.636 —
the best predictor in that corpus. Its inclusion is required to (a) demonstrate
that dynamic analysis adds something over static for the internal benchmark
(it does: Δ = +0.497, the only Holm-significant result), and (b) provide an
honest comparison on external corpora where static analysis is unexpectedly
competitive.

**`SBG V5`:** The primary system under evaluation. Must appear in all tables.

### 7.4 What the baseline suite controls for

| Potential confound | Controlled by |
|---|---|
| Edit size (structural SC/SP design) | `edit_size` (reversed) + edit-size-stratified analysis |
| Exception-raising pattern | `exception_fraction`, `exception_component_v3`, `exception_type_jaccard` |
| Execution volume | `call_count`, `coverage_size`, `n_functions` |
| Static code structure | `static_ast`, `static_token` |
| Previous SBG version advantage | `sbg_v3` (ablation) |
| Trivial combined shortcuts | `combined_shortcut` |

### 7.5 Additional note on SBG V5 vs the full suite

The v6 test results show:
- SBG V5 (0.601) is not statistically superior to `exception_fraction` (0.618)
  or `exception_component_v3` (0.659) — the primary claim that "SBG beats cheap
  shortcuts" is **not demonstrated** on the EVALUABLE set with the current
  benchmark.
- On the ALL set (488 pairs, 13 clusters) the comparison is different:
  `sbg_v5_minus_exception_fraction` p_raw = 0.041 (Holm-adjusted = 0.164, so
  still non-significant after correction). The ALL set is less clean due to
  229 unevaluated pairs scored at zero.
- On both BugsInPy and QuixBugs, SBG V5 falls below chance, while simpler
  baselines (`exception_fraction`, `call_count`) are near or above chance.

This makes the recommended baseline suite not merely a formality but a
**substantive research requirement**: without it, no confirmatory claim about
SBG's discriminative ability relative to cheap alternatives can be made.

---

## 8. Summary Table

| Finding | Value | Status |
|---|---|---|
| EVALUABLE set size | 259 pairs | ✓ confirmed |
| Predictors available | 14 | ✓ identified |
| SBG V5 AUROC (EVALUABLE) | 0.601270 | ✓ reproduced exactly |
| exception_fraction AUROC | 0.618367 | ✓ reproduced exactly |
| exception_component_v3 AUROC | 0.658612 | ✓ highest predictor |
| ΔAUROC(SBG V5 − exception_fraction) | −0.017 [−0.056, +0.035] | ✓ verified (non-sig) |
| ΔAUROC(SBG V5 − exception_component_v3) | −0.057 [−0.097, +0.004] | ✓ verified (non-sig) |
| Holm-significant comparisons | 1 of 6 (vs static_ast) | ✓ confirmed |
| Programs (clusters) in EVALUABLE | 7 | ✓ confirmed |
| Degenerate clusters | 0 | ✓ confirmed |
| Percentile CI reliable at 7 clusters | NO | ⚠ ~15–20 needed |
| Noise floor p95 (500 shuffles, seed 42) | 0.551054 | ✓ matches committed |
| SBG V5 > noise floor p95 | YES (0.601 > 0.551) | ✓ confirmed |
| Learned baseline practical w/o dependency | NO | ⚠ requires ML framework + owner approval |
| BugsInPy SBG V5 AUROC | 0.4099 | ✓ reproduced exactly |
| BugsInPy below-chance projects | 6/11 (54.5%) | systematic failure |
| QuixBugs canonical SBG V5 AUROC | 0.3877 | ✓ reproduced exactly |
| QuixBugs below-chance programs | 29/40 (72.5%) | systematic failure |
| Edit-size reversed AUROC | 0.966703 | structural confound (Agent B) |

---

## Appendix A: All Computational Reproductions

All AUROC values reproduced by running:

```python
import json, pathlib, sys
sys.path.insert(0, '.')
from sbg.statistics import auroc, cluster_bootstrap_ci, paired_cluster_bootstrap_delta, label_shuffle_noise_floor

pairs_p = pathlib.Path('artifacts/final/pairs_v6test_output_free_v6.jsonl')
rows = [json.loads(l) for l in pairs_p.read_text().splitlines() if l.strip()]
evaluated = [r for r in rows if r.get('evaluated')]  # 259 rows
```

Every result in Sections 1, 2, 4, and 6 was computed from the committed JSONL
files using only `sbg.statistics` functions. No source files, tests, or data
were modified.

## Appendix B: Discrepancies with Committed Artifact

None. All independently recomputed values match the committed
`MAIN_EVALUATION_v6test_output_free_v6.json` and `audit_recompute.json` to 6
decimal places. The methodology (cluster bootstrap, paired bootstrap, within-
cluster permutation, within-cluster noise floor) is consistent with what the
`sbg.statistics` module implements and what the committed artifact's `statistics`
field declares.

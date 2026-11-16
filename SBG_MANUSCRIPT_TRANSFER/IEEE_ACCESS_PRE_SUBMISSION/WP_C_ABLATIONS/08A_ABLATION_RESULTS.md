# 08A — SBG V5 Component Ablations (WP-C, Part A)

**Status of this document:** research findings from session WP-C. It contains no publication recommendation.
**Provenance rule:** every ablation variant other than the row labelled `full` (= frozen `sbg_v5`) is an **exploratory modified representation**. None of them is original-SBG evidence. Numbers for `full`, `state_raw` (= frozen `sbg_state`), `v3_only` and `temporal` reproduce the frozen scores exactly (see §1.3).

All numbers below are traceable to files under `WP_C_ABLATIONS/raw/` (file + key given in each table caption). Experiment IDs refer to `WPC_EXPERIMENT_REGISTRY.md`.

---

## 0. Headline answers

| Question | Answer (with scope) |
|---|---|
| Is the state-only > full-V5 gap statistically meaningful on permitted data? | **Yes on the pooled dev+train population, and on dev; borderline on train alone.** Pooled ΔAUROC(state − full) = **+0.0205**, program-cluster bootstrap 95% CI [+0.0087, +0.0315], bootstrap p = 0.002, **Holm p = 0.006** (family of 12), program-level swap-permutation p = 0.004; state is better in 41/58 programs, full in 16, 1 tie (sign-test p = 0.0013). Train alone: Δ = +0.0183, Holm p = 0.051. Dev alone: Δ = +0.0307, Holm p = 0.009. |
| Does the permitted-data gap match the reported V10 gap? | **Size-consistent.** Reported V10 values (from existing A3 output `results/tables/EXP-A3-002_v10_test_comparison.csv`): state 0.9171 vs V5 0.8968 → Δ 0.0203. Pooled dev+train Δ = 0.0205. I did **not** compute a paired test on V10 (forbidden: no V10 re-scoring). |
| Why does state beat full V5? | Not because V3/temporal "contain no signal" — removing state hurts (−0.034). It is because, with V5's fixed weights (0.5 V3 + 0.25 temporal + 0.25 state), the V3 and temporal terms **add score mass to EQUIVALENT pairs** that the state genome leaves at exactly 0, and this ranks equivalents above many changed pairs. The state genome scores 78.9% of EQUIVALENT pairs exactly 0 (full: 56.9%). Within matched sets (same SP transform) state and full are indistinguishable (38 vs 37 sets favour each, 962 identical). See §4. |
| Is any non-state component individually essential? | **No.** Removing any single non-state component moves pooled AUROC by < 0.006 (range −0.0012 … +0.0059). Three of five *non-state* leave-one-out variants are slightly *better* than full. |
| Is the state signal a "value-leak" of return values? | **No evidence of that.** Dropping all `return` events changes state AUROC by −0.0004 (Holm p = 0.34). The signal is carried by the locals present at line/return events: dropping line events alone costs −0.005 (ns); restricting to arguments (call-time locals) costs −0.157 (Holm p = 0.0035). See §5. |

Everything here is **exploratory/post-hoc with respect to SBG's design** and uses a population (v9c_train + v9c_dev) that I did not verify to be independent of SBG development (its use is permitted by the protocol; independence is not claimed).

---

## 1. Data, populations, exclusions, verification

### 1.1 Populations (permitted only)
| Population | Programs | Pairs | CHANGED / EQUIVALENT |
|---|---|---|---|
| v9c_train (primary) | 45 | 1610 | 805 / 805 |
| v9c_dev | 13 | 464 | 232 / 232 |
| **pooled (train + dev)** | **58** | **2074** | **1037 / 1037** |

**Not used:** `v10_test`, `v9c_val` (never scored with any variant; never label-joined). Only label-free descriptive reads of existing frozen scores/caches were made, in B (EXP-WPC-004).

### 1.2 Exclusions and failures (full list in the registry)
* **`math_gray_code` (v9c_train): 40 primary pairs excluded.** No cached trace exists (the program was killed with rc = −9 in the earlier extraction; WP-E's problem). Train is therefore 1610/45 programs, not 1650/46. Listed pair-by-pair in `raw/EXP-WPC-002/v9c_train_exclusions.json`.
* **First extraction attempt failed** (`KeyError: 'base_path'` on 5 programs with placeholder rows). The script was fixed and rerun; failed-attempt logs are kept (`logs/EXP-WPC-001_*_first_attempt.json`).
* **First 005/006 run killed** by the tool harness (process lost with the shell call; no outputs written). Rerun in background; the killed log is kept (`logs/EXP-WPC-005_006_attempt1_killed.log`).
* **`equiv_by_sp_type` block inside `variants_results.json` is degenerate** (the pair table's `sp_type` column is blank on EQUIVALENT rows, so everything fell into one bucket). It was not edited; the correct analysis is EXP-WPC-005d (`equiv_by_sp_from_group.json`, SP type derived from the `group` id). Use only the latter.
* Handoff item 4 (tracer event-cap / timeout / input-subset sensitivity) was **not done**.

### 1.3 Reproduction of the frozen scores (gate for everything below)
I re-ran the frozen extraction in-process (the shared cache cannot be used for the state genome: it stores locals snapshots only at call/return/exception events, but the frozen state genome also consumes `line`-event snapshots). Results (`raw/EXP-WPC-002/VERIFY.json`):

| | pairs | match `sbg_v5` | match `sbg_v3` | match `sbg_temporal` | match `sbg_state` | V3 term-sum bit-equal | V5 not full-fidelity |
|---|---|---|---|---|---|---|---|
| v9c_dev | 464 | 464 | 464 | 464 | 464 | 464 | 0 |
| v9c_train | 1610 | 1610 | 1610 | 1610 | 1610 | 1610 | 0 |

(match = equality at 9 d.p. with the frozen CSV scores). The recomposed full score `Σ components` equals frozen V5 to ≤ 1.1·10⁻¹⁶. The bootstrap CI implementation equals `eval_lib` (sanity flag true).

---

## 2. Component definitions (WP-C definitions — not repo-defined)

V5 = 0.5·V3 + 0.25·temporal + 0.25·state. V3 = 0.20·coverage + 0.25·call-bigrams + 0.20·call-frequency + 0.10·exception + 0.10·depth + 0.05·consistency + 0.05·input-sensitivity + 0.05·exception-causality (read from `SBG/sbg/v3/genome.py`, `SBG/sbg/v5/distance_v5.py`). Because "call topology" is not defined anywhere in the repo, the six ablation components below are **my** grouping of the frozen terms at V5 effective weights:

| Component | Definition (V5-effective weight) | Max weight |
|---|---|---|
| `call_topology` | 0.5·(0.20·d_freq + 0.10·d_depth) — function-call frequency histogram + mean call depth | 0.15 |
| `bigrams` | 0.5·(0.25·d_seq) — order-sensitive call-transition bigrams | 0.125 |
| `exception` | 0.5·(0.10·d_exception + 0.05·d_exc-causality) | 0.075 |
| `coverage_resid` | 0.5·(0.20·d_coverage + 0.05·d_consistency + 0.05·d_input-sensitivity) | 0.15 |
| `temporal` | 0.25·d_temporal (trigrams, entropy, exception triples, causal, phase, loop) | 0.25 |
| `state` | 0.25·d_state (frozen state-transition genome) | 0.25 |

"Full minus X" is the unnormalised sum of the remaining components (AUROC is rank-based, so rescaling is irrelevant). "X only" is the single component's score.

---

## 3. Ablation results

Statistics follow the frozen protocol (`experiments/common/eval_lib.py`): tie-aware AUROC/AUPRC, program-cluster bootstrap B = 2000, seed 42, Holm over the declared 12-comparison family (6 "only" + 6 "full-minus", each paired against `full`, declared before computing; `wpc_ablation.py` docstring). Source: `raw/EXP-WPC-003/ablation_results.json`, `tables/WPC-003_ablation_auroc_table.csv`.

### 3.1 Pooled dev + train (n = 2074 pairs, 58 programs)

| Variant | AUROC [95% CI] | Δ vs full [95% CI] | Holm p | zero-rate CHANGED | zero-rate EQUIV |
|---|---|---|---|---|---|
| **1. Full SBG V5 (frozen)** | **0.7458** [0.726, 0.765] | — | — | 0.168 | 0.569 |
| 2. State only | 0.7663 [0.744, 0.789] | **+0.0205** [+0.0087, +0.0315] | **0.006** | 0.261 | 0.789 |
| 3. Call topology only | 0.5252 [0.501, 0.555] | −0.2206 [−0.244, −0.197] | 0.006 | 0.832 | 0.883 |
| 4. Call-order bigrams only | 0.5245 [0.501, 0.554] | −0.2213 [−0.244, −0.199] | 0.006 | 0.832 | 0.883 |
| 5. Exception structure only | 0.5930 [0.574, 0.614] | −0.1529 [−0.176, −0.130] | 0.006 | 0.767 | 0.955 |
| 6. Temporal only | 0.5992 [0.573, 0.627] | −0.1466 [−0.166, −0.128] | 0.006 | 0.661 | 0.878 |
| (coverage_resid only) | 0.7182 [0.700, 0.735] | −0.0276 [−0.046, −0.009] | 0.006 | 0.213 | 0.614 |
| 7. Full − state | 0.7121 [0.691, 0.733] | −0.0337 [−0.044, −0.024] | 0.006 | 0.203 | 0.607 |
| 8a. Full − temporal | 0.7515 [0.733, 0.770] | +0.0057 [+0.003, +0.009] | 0.006 | 0.168 | 0.569 |
| 8b. Full − call_topology | 0.7492 [0.730, 0.768] | +0.0034 [+0.002, +0.006] | 0.006 | 0.168 | 0.569 |
| 8c. Full − bigrams | 0.7486 [0.729, 0.768] | +0.0028 [+0.002, +0.004] | 0.006 | 0.168 | 0.569 |
| 8d. Full − exception | 0.7446 [0.725, 0.765] | −0.0012 [−0.002, −0.0004] | 0.006 | 0.168 | 0.569 |
| 8e. Full − coverage_resid | 0.7518 [0.728, 0.776] | +0.0059 [−0.004, +0.015] | 0.234 (ns) | 0.261 | 0.789 |
| reference: V3 only (frozen `sbg_v3`) | 0.7147 [0.694, 0.736] | −0.0311 | — | 0.203 | 0.607 |

Notes:
* Several tiny deltas (e.g. −0.0012, +0.0028) have small Holm p because the bootstrap is **paired on the same programs**, which resolves very small shifts; their practical size is negligible. Report effect size, not just p.
* "Call topology only" and "bigrams only" have **essentially identical rank behaviour** (Spearman ρ = 1.00 after rounding on all pairs). In v9c_train, `d_seq` is non-zero in 222 of 1610 pairs and `d_freq` in 221; in those pairs the values are constant-like (e.g. d_freq 0.732 / d_seq 0.5 / d_dep 0.476 in the first eight inspected non-zero pairs) — the terms fire together when the function-call structure differs (e.g. helper extraction/inlining SP transforms). This is why their AUROCs coincide (0.525). (Counts from `raw/EXP-WPC-002/v9c_train_pairs.csv`; the "constant-like" remark is from an 8-row inspection, not a full distribution analysis.)
* The three weakest single components (call topology, bigrams, exception) are 77–83% zero-scored on CHANGED pairs, i.e. they cannot rank most pairs at all.
* `full − state` (= 0.5·V3 + 0.25·temporal; 0.7121) is marginally *below* `V3 only` (0.7147), i.e. adding the temporal term to V3 changes pooled AUROC by about −0.003 (derived from these two table values; not a separate test).

### 3.2 Per population

| Variant | v9c_train AUROC (Holm p vs full) | v9c_dev AUROC (Holm p vs full) |
|---|---|---|
| Full V5 | 0.7352 | 0.7854 |
| State only | 0.7534 (Δ +0.0183, **p 0.051**) | 0.8161 (Δ +0.0307, **p 0.009**) |
| Call topology only | 0.5184 | 0.5499 |
| Bigrams only | 0.5180 | 0.5484 |
| Exception only | 0.5941 | 0.5890 |
| Temporal only | 0.5944 | 0.6156 |
| Full − state | 0.7066 (Δ −0.0285, p 0.006) | 0.7326 (Δ −0.0528, p 0.006) |
| Full − temporal | 0.7410 (+0.0059) | 0.7901 (+0.0047) |
| Full − call_topology | 0.7390 (+0.0039) | 0.7879 (+0.0025) |
| Full − bigrams | 0.7379 (+0.0028) | 0.7887 (+0.0033) |
| Full − exception | 0.7337 (−0.0015) | 0.7849 (−0.0005, ns) |
| Full − coverage_resid | 0.7376 (+0.0024, ns) | **0.8046 (+0.0192, Holm p 0.050)** |

Dev is where "less V3 coverage" helps most: removing `coverage_resid` raises dev AUROC by 0.019 (Holm p = 0.050, borderline) but not train (+0.002, ns). With only 13 dev programs this should be read as a population-specific effect, not a stable property.

### 3.3 Secondary measures (pooled; `ablation_results.json`)
* Macro-AUROC (mean over programs): full 0.7561, state 0.7736, V3 0.7246, temporal 0.6034.
* Matched-set concordance (a CHANGED pair vs its SP-matched EQUIVALENT partner, 1037 sets): full 0.8105 [0.785, 0.837], state 0.8230 [0.795, 0.850], V3 0.7666, coverage_resid 0.7763, temporal 0.6172, exception 0.5955, call topology 0.5289, bigrams 0.5246.
* Per-program Δ(state − full): train 31 better / 13 worse / 1 tie (sign-test p = 0.0096); dev 10 / 3 / 0 (p = 0.092); pooled 41 / 16 / 1 (p = 0.0013); median per-program Δ = +0.0246, mean +0.0175.
* AUROC by edit-size tertile (pooled): full 0.753 / 0.785 / **0.646** (≤6, 6–11, >11); state 0.768 / 0.805 / **0.695**. Edit size is confounded with the SP type (the SC-6 forensics in B show edit size ≈ SP type).

---

## 4. Why state-only beats full V5 (mechanism analysis, EXP-WPC-003 + 005c + 005d)

### 4.1 The gap is a cross-set ranking effect, not a within-pair effect
Within matched sets (the same SP transform on both sides) state and full are statistically indistinguishable: state correct & full wrong/tie in 38 sets, full correct & state wrong/tie in 37, identical in 962 (of 1037). The AUROC gap therefore arises from how scores of *different* pairs are ordered globally.

### 4.2 Zero mass: state keeps EQUIVALENT pairs at exactly zero
| | share of EQUIV at exactly 0 | share of CHANGED at exactly 0 | AUROC(CHANGED vs EQUIV that are 0) | AUROC(CHANGED vs EQUIV > 0) |
|---|---|---|---|---|
| full V5 | 56.9% | 16.8% | 0.916 | 0.521 |
| state only | **78.9%** | 26.1% | 0.869 | 0.382 |

State has *lower* AUROC against non-zero EQUIVALENT pairs (0.382 vs 0.521) but there are far fewer of them (21.1% vs 43.1% of equivalents), and both measures lose CHANGED pairs to zero (state 26.1% — more than full's 16.8%). The net effect is positive for state. Complementarity (pooled; CHANGED pairs: state-only non-zero 7, rest-only non-zero 97, both 751, both zero 174; EQUIV pairs: state-only 3, rest-only **228**, both 198, both zero 590) shows that the non-state part of V5 fires on ~228 EQUIV pairs where state is silent (vs 3 the other way) — this is the false-positive mass state avoids.

### 4.3 Where the false-positive mass comes from (EQUIVALENT pairs by SP transform; `raw/EXP-WPC-005/equiv_by_sp_from_group.json`)
SP type is derived from the pair group id. EQUIV non-zero rate / mean score (full | state | V3-only):

| SP transform | n_equiv | full | state | V3 only | AUROC within SP type (full / state) |
|---|---|---|---|---|---|
| SP-1 | 120 | 0.07 / 0.001 | 0.00 / 0.000 | 0.07 / 0.001 | 0.881 / 0.854 |
| SP-2 | 172 | 0.07 / 0.001 | 0.00 / 0.000 | 0.07 / 0.002 | 0.799 / 0.805 |
| SP-3 | 169 | **1.00** / 0.027 | 0.01 / 0.000 | **1.00** / 0.053 | 0.792 / 0.811 |
| SP-4 | 171 | 0.07 / 0.001 | 0.00 / 0.000 | 0.07 / 0.002 | 0.869 / 0.860 |
| SP-5 | 113 | 0.91 / 0.155 | 0.75 / 0.218 | 0.91 / 0.114 | 0.649 / **0.724** |
| SP-6 | 142 | 0.07 / 0.001 | 0.00 / 0.000 | 0.07 / 0.001 | 0.876 / 0.859 |
| SP-8 | 102 | 0.89 / 0.425 | 0.88 / 0.596 | 0.89 / 0.306 | 0.508 / **0.576** |
| SP-9 | 3 | 0.00 | 0.00 | 0.00 | — |
| SP-11 | 45 | 0.93 / 0.067 | 0.93 / 0.235 | 0.07 / 0.008 | 0.684 / 0.667 |

Reading: SP-3 (every equivalent scores > 0 in V3 — coverage_resid, mean 0.027 — but ~0 in state), SP-5 and SP-8 are where V3/temporal add equivalent-side mass state does not. SP-8 equivalents have large scores for **both** (0.43 / 0.60) — the SC-6 forensics (EXP-WPC-004 §5) found that some v9c SP-8 "equivalent" partners crash on every input (val 3, dev 3, train 7 visible SC-6+SP-8 pairs; e.g. `UnboundLocalError`), so for those the "equivalent" label is behaviourally questionable; I did not investigate further. The SP-8 AUROC of 0.51–0.58 means SBG cannot separate CHANGED from EQUIVALENT within that transform in either form. The by-SP figures are descriptive; no per-SP test was pre-declared.

### 4.4 The fixed weights are not at the AUROC optimum on this data (state-weight sweep)
Score(w) = w·state + (1−w)·(V5 − 0.25·state)/0.75 (V5 ⇔ w = 0.25). Selected rows (`state_weight_sweep`): 

| w (state) | pooled | train | dev |
|---|---|---|---|
| 0.00 (V3 + temporal only) | 0.7158 | 0.7108 | 0.7353 |
| 0.25 (= V5) | 0.7458 | 0.7352 | 0.7854 |
| 0.50 | 0.7600 | 0.7500 | 0.7984 |
| 0.75 | 0.7682 | 0.7591 | 0.8041 |
| 0.95 | **0.7727** | 0.7634 | 0.8101 |
| 1.00 (state only) | 0.7663 | 0.7534 | **0.8161** |

AUROC rises monotonically with state weight on all three populations (pooled and train peak at w = 0.95, dev at w = 1.0). This sweep was run on the same data it describes; it is a **descriptive diagnostic, not a tuned variant**, and any selection of w would need fresh confirmatory data. The sweep shows that no mixture materially beats state alone (pooled max 0.7727 vs 0.7663).

### 4.5 A fitted combiner does not beat state alone
Logistic combiners fitted **on train only** and evaluated on dev (exploratory; `fitted_combiner_dev`): 

| dev AUROC | value | vs full (boot p) | vs state (boot p) |
|---|---|---|---|
| full V5 | 0.7854 | — | −0.0307 (0.003) |
| state only | 0.8161 | +0.0307 (0.003) | — |
| 6-component logistic | 0.7838 | −0.0016 (0.98) | −0.0323 (0.093) |
| 2-term logistic (state, rest) | 0.8041 | +0.0187 (0.364) | −0.0120 (0.309) |

Neither fitted combiner is distinguishable from state alone or from full on dev (13 programs, low power). The 6-component logistic assigns the largest positive weight to `state` (+0.96) and negative weights to `bigrams` (−0.68) and `call_topology` (−0.24) (standardised features).

### 4.6 Redundancy structure (Spearman, pooled; `spearman_all`)
state–coverage_resid 0.62, state–temporal 0.65, state–exception 0.48, state–call_topology/bigrams 0.51; temporal–call_topology/bigrams **0.80**, temporal–exception 0.71; exception–call_topology 0.26. On EQUIVALENT pairs only, temporal–call_topology/bigrams = 0.98 (the temporal genome largely re-encodes the call-structure terms). So V5 is much less than "four independent views": temporal ≈ call-structure; the state genome and the coverage/V3 part carry the distinct signal.

---

## 5. What does the state-genome signal actually consist of? (EXP-WPC-005a/b — exploratory, label-using, permitted data)

Seven state-genome input variants were designed to test whether state's strength depends on return-value leakage or on concrete values (family of 7, Holm-corrected vs the identity variant `s0`, which reproduces frozen state exactly on 2146 trace files). All are modified representations (**not original SBG**).

| Variant (what is removed/changed before the frozen state-genome code runs) | pooled AUROC | Δ vs s0 [95% CI] | Holm p | train / dev AUROC |
|---|---|---|---|---|
| `s0` identity (= frozen state) | 0.7663 | — | — | 0.7534 / 0.8161 |
| `s_noret` — drop all `return` events | 0.7659 | −0.0004 [−0.0013, +0.0004] | 0.336 | 0.7530 / 0.8147 |
| `s_boundary` — drop `line` events (keep call/return/exception) | 0.7615 | −0.0048 [−0.0111, +0.0008] | 0.208 | 0.7490 / 0.8091 |
| `s_args` — keep only argument-named locals | 0.6097 | −0.1566 [−0.179, −0.134] | 0.0035 | 0.6033 / 0.6343 |
| `s_args_noret` | 0.6097 | −0.1566 | 0.0035 | 0.6033 / 0.6339 |
| `s_boundary_noret` — call+exception events only | 0.6101 | −0.1562 | 0.0035 | 0.6048 / 0.6308 |
| `s_structure` — every value collapsed to one class (variable *existence* kept) | 0.7355 | −0.0309 [−0.048, −0.015] | 0.0035 | 0.7259 / 0.7697 |
| `s_shuffle` — values permuted among variables of each snapshot | 0.7499 | −0.0165 [−0.032, −0.001] | 0.105 (ns) | 0.7490 / 0.7584 |

Reading (descriptive; the interpretations are hypotheses):
1. **No return-event dependency.** Return events add nothing measurable; state's discriminative power is not a return-value leak. In the label-free leakage diagnostic over 2146 trace files, only 129,420 / 268,125 (48%) of all return values (66% of "non-trivial" ones) coincide with some local at the same event — so return values are *partially* visible through ordinary locals, but removing the return events does not change AUROC.
2. **Most of the signal needs locals beyond the arguments** (variables created inside the function: 0.61 → 0.77).
3. **Variable existence/creation pattern carries most of it:** collapsing all values still retains 0.7355 of 0.7663 (−0.031). Concrete value classes add a smaller but measurable ~0.03; shuffling values costs −0.0165 (Holm-ns pooled, significant on dev, Holm p 0.0035).
4. By event kind (pooled, state-genome sub-distances; `state_by_event_kind`): `state_creation` 0.725, `state_mutation` 0.708, `state_deletion` 0.606, `error_transition`/`error_recovery` 0.594; `resource_acquire` (non-zero on 0.4% of CHANGED), `resource_release` and `data_flow` sub-terms are (almost) always zero (AUROC ≈ 0.50) — i.e. in this population the state genome is effectively a *local-variable creation/mutation/deletion* signature.
5. Swapping the exploratory state variants into full V5 (`full_with:*`, pooled) changes full-V5 AUROC by: `s_noret` −0.0002 (p 0.56), `s_boundary` +0.0014 (p 0.46), `s_args` −0.0288, `s_boundary_noret` −0.0290, `s_structure` −0.0147, `s_shuffle` −0.0073 (raw bootstrap p ≤ 0.0005 for args/boundary_noret/structure; 0.037 for shuffle; no multiplicity correction applied to this secondary block). No variant improves full V5 detectably.

(Interpretation caveat: the state genome sees concrete-value-derived abstract classes of locals, so a program whose *internal* locals encode the result will leak it; the experiment shows no sensitivity to that on return events, but does not exclude it through other locals.)

---

## 6. Threats to validity / limits

1. **Not independent of SBG development (unverified).** v9c_train/dev are permitted for this work, but I did not establish that SBG hyper-parameters or design were never fitted on them. The sweep/combiner/leakage numbers are post-hoc; they describe, they do not confirm.
2. **Small program count** (58; dev 13) → wide program-cluster CIs; Holm-borderline results on train (p = 0.051) and for `full−coverage_resid` on dev (p = 0.050).
3. **Family of 12 is declared; mechanism analyses (§4.2–4.6, §5) are not multiplicity-controlled**, except the family of 7 in §5 and the combiner comparisons (unadjusted).
4. **Component grouping is mine** (call_topology/bigrams/exception/coverage_resid); a different grouping of the V3 terms would give different "only/minus" numbers.
5. **No V10 or val evidence.** The gap's V10 value is quoted from the existing A3 table; consistency of magnitude (0.0203 vs 0.0205) is not an independent test.
6. **Equivalent-pair quality.** Some SP-8 equivalents are behaviourally broken (see §4.3); this inflates EQUIV-side mass for all methods and affects the zero-rate results. A sensitivity analysis excluding SP-8 was **not run**.
7. **Single-run extraction / not re-validated for sensitivity:** tracer event-cap, timeout and input-subset sensitivity (handoff item 4) not done.
8. **Addresses in snapshots.** Cached snapshots contain `<function … at 0x…>` reprs; the frozen abstract domain maps them to a fixed class, so scores are unaffected, but raw snapshot equality checks need address masking (applied in B).

## 7. What would turn these findings into evidence
* A paired state-vs-V5 test on a fresh, withheld program set with a fixed, pre-registered test (1 comparison, no family inflation). The V10 gap cannot serve (burned for post-hoc variants and not re-scorable here).
* Pre-declare and test the zero-mass hypothesis: e.g. recompute AUROC after excluding SP-3/SP-5/SP-8 EQUIVALENT pairs (or reweighting equivalents) and see whether the gap vanishes; run with and without broken SP-8 partners.
* If any re-weighting of V5 is considered, fit it on train only, freeze it (config + code SHA-256), and score it once on fresh data. It would then be a *new method*, not the original V5.

## 8. Reproduction
See `WPC_EXPERIMENT_REGISTRY.md` §"Reproduction commands". Raw outputs: `raw/EXP-WPC-002/*pairs.csv` (per-pair components + frozen scores + labels), `raw/EXP-WPC-003/ablation_results.json`, `raw/EXP-WPC-005/*.json`, `tables/WPC-003_ablation_auroc_table.csv`.

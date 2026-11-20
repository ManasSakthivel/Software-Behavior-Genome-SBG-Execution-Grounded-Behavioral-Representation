# Agent 4 — Independent Evidence Audit (final sprint)

**Scope.** Read-only audit of existing reports, scripts, tables and frozen artifacts. No experiment was run, no benchmark was rerun, and no dataset was downloaded. Everything was checked from files already on disk.

**Provenance caveat about `agent_4/scripts` and `agent_4/tables`.** The Agent 4 spawn call was cancelled, and these files are timestamped 09:33–09:37. Who produced and ran them is unattested, so I treated them as *unverified* until corroborated. They were corroborated by two independent computations: (a) my own Agent 1 script (`agent_1/verify_program_robustness.py`) and (b) my direct recomputations from the frozen artifacts, listed below. Where a figure rests on Agent 4's tables alone, that is stated.

**Evidence classes.** VERIFIED = reproduced by independent code or confirmed directly in a frozen artifact. REVIEWED = inspected and internally consistent, not reproduced. PRELIMINARY = exploratory or incomplete. NOT ESTABLISHED = the evidence does not support the claim. UNAUDITED = could not be checked from existing evidence. DEFERRED = out of scope.

## 1. Verdicts

| Report | Verdict | Reason |
|---|---|---|
| Frozen headline numbers (V8, V9c, V10) | **PASS** | Match their frozen JSONs (§2.1). |
| Previous sprint: component ablation | **PASS (exploratory)** | V10 values reproduced independently; V9c component AUROCs match the frozen JSON; all labelled post-hoc. |
| Previous sprint: program robustness tables | **PASS** | Reproduced by 79 checks of my own code, 0 mismatches. |
| Final sprint Agent 1 (robustness) | **PASS WITH CORRECTIONS** | Two sentences were wrong and are corrected (§4). |
| Final sprint Agent 2 (real-bug taxonomy) | **FAIL as written for the taxonomy and failure-mechanism sections; PASS for primary AUROCs and the exact-zero reconciliation** | Several claims contradicted by artifacts or without a source (§3). |
| Final sprint Agent 3 (external validation) | **PASS WITH CORRECTIONS** | Counts consistent but not independently reproduced; the manuscript-approval statement was out of scope and is removed (§4). |
| Final sprint Agent 5 (Java readiness) | **PASS WITH CAVEATS** | Honest scoping; tests/overhead/effort not reproduced here. |
| Previous sprint: Python sensitivity | **PASS WITH CAVEATS** | Stored numbers verified; toy suite only; interpreter patch-version provenance unresolved. |
| Previous sprint: Java feasibility | **REVIEWED** | Not reproduced; consistent with Agent 5. |
| Previous sprint: COBOL feasibility | **REVIEWED** | Feasibility only; deferral argument is sound; not reproduced. |

## 2. Numbers checked

### 2.1 Frozen headline metrics

| Claim | Source checked | Value found | Status |
|---|---|---|---|
| V10: 19 programs, 638 pairs, 319 matched sets | `v10_audit.json`; my Agent 1 script | 19 / 638 / 319 (641 evaluated rows; 3 non-terminating pairs and their 3 partners dropped) | VERIFIED |
| V10 V5 AUROC | frozen JSON; two independent recomputations | 0.896768 | VERIFIED |
| V10 forward edit / M_EX / M_EX+V5 | same | 0.616046 / 0.790789 / 0.797088 | VERIFIED |
| V5 formula 0.50·V3 + 0.25·temporal + 0.25·state | `v10_audit.json: v5_formula_max_abs_diff` | max abs diff 7.5e-10 on stored scores | VERIFIED |
| V10 cluster CI for V5 | frozen `V10_INDEPENDENT_EVALUATION.json` | [0.8629, 0.9216]; Agent 4 [0.8647, 0.9214] (different resampling seed) | VERIFIED |
| Naive pair bootstrap vs cluster bootstrap | `v10_audit.json` | pair [0.8696, 0.9194] vs cluster [0.8647, 0.9214] | VERIFIED; clustered CI is the correct one |
| V10 Holm family | frozen JSON | **six** hypotheses H1–H6. H1, H2, H3 rejected (adj. p 0.003 / 0.005 / 0.005). H5 adj. p 0.090. H6 and **H4 adj. p 1.0** | VERIFIED |
| H4 (M_EX+V5 − M_EX) | frozen JSON, my script, Agent 4 | +0.0063, CI [−0.069, 0.068], raw p 0.809 | VERIFIED; **incremental value not established** |
| V9c val: 11 programs, 432 pairs, 216 sets, V5 | `V9_VAL_EVALUATION.json` | 11 / 432 / 216, V5 0.7514, CI [0.7063, 0.7936] | VERIFIED |
| V8 test: V5 and reversed edit baseline | `V8_TEST_EVALUATION.json` | V5 0.6937; edit_size_reversed 0.8759 | VERIFIED (negative evidence preserved) |
| V9c val scores unopened before freeze | `FREEZE_V9.json` | `val_scores_opened_before_freeze: false` | VERIFIED (as stated in the freeze file; not independently attested) |
| Frozen hashes | my recheck and Agent 4's | 14,955 files, 0 mismatches | VERIFIED |

### 2.2 V10 robustness (Agent 1 final)
Recomputed by my own independent code and corroborated by Agent 4's separate code.

| Claim | Value | Status |
|---|---|---|
| V5 beats edit in 19/19 programs; mean +0.2592 | 19/0/0, +0.259184, exact sign p 3.8e−6 | VERIFIED |
| V5 vs M_EX | 14/5, mean +0.0949, sign p 0.0636 | VERIFIED; not significant at 0.05 |
| LOPO V5 | 0.892167 (drop `ds_union_find`) to 0.906182 (drop `graph_topological_kahn`) | VERIFIED |
| Within / between concordance | 0.890875 / 0.897109; 5,567 / 96,194 comparisons; between share 94.53% | VERIFIED |
| Matched-set concordance | V5 0.931 (284/26/9); **edit 0.9545 (292/25/2)**; state-only 0.9467; M_EX 0.854 | VERIFIED. **Edit size beats V5 on this metric** |
| Edit-size-controlled AUROC | V5 0.8749, edit 0.5, n = 8,605 | VERIFIED |
| SC-6 (value-only) | 17 of 23 CHANGED score exactly 0; AUROC 0.4506 | VERIFIED |
| Per-program V5 range | 0.705–0.970, mean 0.8930, 3 programs under 0.80 | VERIFIED |
| Leave-two-out, effective-n (inverse HHI), Spearman correlations, SC/SP-family tables | | REVIEWED (previous sprint outputs, not recomputed) |

Pooled V5−M_EX delta +0.106 [0.033, 0.186]: reproduced by Agent 4 ([0.0346, 0.1841]) and the previous sprint. It is **not** in the frozen JSON (the frozen Holm family does not include V5 vs M_EX), so it is an exploratory contrast.

### 2.3 Component ablation (post-hoc, exploratory)

| Variant | Claimed V10 AUROC | Recomputed (Agent 4 and my cross-check against previous-sprint CSV) | Status |
|---|---|---|---|
| Full V5 | 0.8968 | 0.896768 | VERIFIED |
| Without V3 | 0.9053 | 0.905312 | VERIFIED |
| Without temporal | 0.9036 | 0.903568 | VERIFIED |
| Without state | 0.8821 | 0.882136 | VERIFIED |
| V3 only | 0.8817 | 0.881743 | VERIFIED |
| Temporal only | 0.8070 | 0.807013 | VERIFIED |
| State only | 0.9171 | 0.9171 | VERIFIED |

- Paired Δ (full − ablation): vs state-only −0.0203 [−0.0386, −0.0070]; vs no-state +0.0146 [0.0060, 0.0239]; vs no-temporal −0.0068 [−0.0188, 0.0005]; vs no-V3 −0.0085 [−0.0154, −0.0022]. These are exploratory intervals with no multiplicity control.
- V9c component AUROCs match the frozen JSON (V3 0.7399, temporal 0.6188, state 0.7624, V5 0.7514). V9c ablation deltas were **not recomputed** (REVIEWED).
- **Reading.** State-only is at least as good as V5 on both V10 (0.917 vs 0.897) and V9c (0.762 vs 0.751). The post-hoc evidence therefore does not show V5's weights are optimal or that each component is necessary. It does not license promoting state-only to the primary method, and it does not justify re-weighting after seeing V10. The gaps are small (≤0.02 AUROC) and rest on 19 and 11 clusters.

## 3. Real-bug taxonomy (Agent 2): confirmed defects

**Verified, no change needed.**
- Primary AUROCs: BugsInPy 0.4099 [0.3262, 0.4939] (147 pairs, 41/106, 39 clusters), QuixBugs canonical 0.3877 [0.2847, 0.5034] (152 pairs, 40/112, 40 clusters). Agent 4 and Agent 2 agree. The BugsInPy CI upper bound is just below 0.5. The QuixBugs CI includes 0.5.
- Exact-zero reconciliation, BugsInPy positives with V5 = 0: **21** in committed v7; **24** after `re.purge()` (`bugsinpy_purge_rescore.json`; the flipped pairs are `youtube-dl/6`, `/7`, `/26`, committed 0.612 / 0.681 / 0.675); **26** in the v8 rescore (`EXTERNAL_RESCORE_V8.json`, additional flips `luigi/14` and `youtube-dl/31`). The temporal component is also zero on 26 pairs in v7. That is a **different quantity that coincidentally equals 26**, so the 21-vs-26 confusion is explained by the scoring version plus this coincidence.
- Populations differ: 41 positives are evaluated of 55 positive rows; 14 positives and 39 negatives are unevaluated (49 `unsupported_signature`, 4 `import_error`). These are excluded from the primary result.
- Seven EQUIVALENT negatives with an invalid label: nested helper `fix_kv` renamed without updating call sites. `EXTERNAL_NEGATIVE_AUDIT.json` lists `new_undefined: ['fix_kv']`, and their V5 scores are 0.712–0.800.

**Contradicted or unsupported.**

| # | Agent 2 claim | Evidence | Severity |
|---|---|---|---|
| 1 | "SP-2 renaming causes the harness to score **100%** of SP-2 negatives as behavioural changes; mean distance 0.20–0.28" | BugsInPy: 37/40 SP-2 negatives are nonzero in v7, 36/40 in v8; mean 0.275 (v7) / 0.201 (v8). QuixBugs: 31/40 nonzero (v7), 29/40 (v8); **mean 0.0138**. The range 0.20–0.28 does not hold for QuixBugs. The v8 structural-entry policy, designed to fix rename mismatches, leaves 36/40 nonzero, so "entry-rename harness defect" is **not established as the cause**. | Major |
| 2 | The 61 BugsInPy and 72 QuixBugs negatives labelled "**genuine representation failure**" | Many of these negatives score exactly 0 and are *correct*: **28 of 61** (BugsInPy) and **46 of 72** (QuixBugs). The script's `else` branch even writes "Negative correctly evaluated and assigned zero distance" while keeping the failure category. Likewise 12 BugsInPy and 8 QuixBugs positives that score above 0 are labelled "failure" although SBG did register a change. | Major: the headline category counts are not meaningful |
| 3 | QuixBugs: "20 programs crash 100% (TypeError/AttributeError) before reaching the fault; 6 crash >90%"; 26/40 "fault not reached" | No source artifact. The crash sets are hard-coded in `build_taxonomy.py` as "pre-calculated", with no file, log or script that produced them. The `exception_fraction` in the pair scores is a base-vs-variant *distance*, not a crash rate, and is 0.0 for all 20, which cannot show a crash. | Major: **NOT ESTABLISHED** (UNAUDITED) |
| 4 | BugsInPy: 21 positives "fault not reached" | The artifacts show V5 = 0 and no output difference on the reference battery (20 of 21; 1 has no reference). That shows *no observable difference on the supplied inputs*. No coverage or execution-reach artifact was used, so "fault not reached" cannot be distinguished from "reached, no visible difference on these inputs". The report's "never exercise the bug condition" is **not established**. Category 2 for BugsInPy is 0 only because the rule needs a reference-output difference. | Major |
| 5 | QuixBugs "fault reached, output not observed" examples | Hard-coded list again. Text lists `is_valid_parenthesization, kheapsort, lis, max_sublist_sum, next_palindrome`; the CSV assigns `shunting_yard` instead of `max_sublist_sum` (which scores 0.018 and is called "genuine failure"). The quoted buggy/fixed source snippets were not checked against `external/quixbugs`. | Moderate |
| 6 | Self-distance anomalies `black/21 0.6737`, `black/23 0.6742`, `youtube-dl/37 0.6040`, "due to global AST/token compiler state" | `EXTERNAL_RESCORE_V8.json` records 0.6735, 0.6685, 0.5966 (max 0.6735). Values do not match. The cause is asserted without evidence; the artifact shows only that self-distance is nonzero. | Moderate |
| 7 | `luigi/14` "entry discovery mismatch in v7" | v7 base and variant entries are **identical** (`class:Failures,Task`). Only `youtube-dl/31` (and `httpie/1`) show mismatched entries. The cause of luigi/14's change to 0 in v8 is **not established**. | Moderate |
| 8 | "converges to chance" and "no statistically significant capacity to detect real bugs" | The exclusion values are 0.444–0.510 with CIs from ~0.35 to ~0.62. These are *inconclusive*, not evidence of chance performance. They remove the largest-noise negative class (SP-2) after seeing the result, so they are exploratory by construction. | Moderate |
| 9 | "Excluding broken SP-2 → 0.4453 / 0.3842", "excluding all SP-2 → 0.4970 / 0.4444" in one column beside the v7 headline | These are **output_free_v8 rescored** values, not v7. v7-basis values are 0.4715 (BugsInPy) and 0.4507 (QuixBugs). The v8 all-pairs value is 0.4159 (BugsInPy) and 0.3842 (QuixBugs, 151 pairs, one non-terminating). The report mixes scorers in a single table and does not say so. | Moderate |
| 10 | "BugsInPy (501 bugs, 55 eligible units)" | The pairs file has 51 bugs and 55 positive rows. "501" is not in anything I checked. | Minor (UNAUDITED) |
| 11 | "SBG must be presented as a tool for semantic equivalence and mutation discrimination in closed algorithmic units" | An over-claim. Supported: held-out-program discrimination on same-generator synthetic variants (V10 and V9c), with a negative V8 result and a negative real-bug transfer. | Moderate |

**Also not re-examined.** The `quixbugs_declared` AUROC of 0.7022 (24 positives, 28 clusters, 99 of 152 pairs evaluated) is a survivor-biased subset (36 `ineligible`, 10 `nonterminating`, 7 `harness_error`). Agent 2 correctly labels it exploratory, and it must not be promoted.

**Net effect.** The reliable statements are: (1) transfer to real bugs is negative or inconclusive; (2) 21/41 BugsInPy positives and 32/40 QuixBugs positives score exactly 0; (3) value-only changes are invisible by design (SC-6); (4) known harness artifacts exist (regex-cache contamination; 7 invalid labels; entry mismatches for 2 pairs). The **per-pair causal taxonomy is not supported** beyond those items, and categories 1 and 6 should not be quoted.

## 4. Corrections made or required

| File | Correction | Action |
|---|---|---|
| `agent_1/agent_1_program_robustness_final.md` (my own report) | (a) "frozen run" for the pooled V5−M_EX delta is wrong; it is exploratory (not in the frozen Holm family). (b) The Holm family is H1–H6, not H1–H4. (c) "single-function" program claim is not verified. (d) The final paragraph wrongly said the V5−M_EX bootstrap came from the frozen JSON. | Edited in place |
| `agent_3/agent_3_external_validation_decision.md` | Removed "Moving to manuscript preparation is **approved**" (out of scope). Added a status banner: no SBG evaluation on SeqCoBench was run, counts are REVIEWED, power figures are assumption-based. | Edited in place |
| `agent_2/agent_2_real_bug_failure_taxonomy.md` | Added a banner directing readers to this audit and listing the withdrawn claims (§3). The body is left intact for traceability. | Banner added |
| `agent_5/agent_5_java_readiness.md` | No change. It already labels the smoke run descriptive, n = 3, same-author, not an evaluation. | None |

## 5. Other claims audited

**Python version sensitivity (previous sprint).** `PYTHON_VERSION_SENSITIVITY.json` is verified: `HARD_NEGATIVE` 120 fields / 30 changed / max 0.1196, and `REGRESSION` 75 fields / 4 changed / max 0.4085. The 0.409 is the largest change in *any* distance field (including `state`) on a pair named REG_09, not a shift in `sbg_v5` itself. The Spearman 0.968 (3.9.6 vs 3.13.5) is REVIEWED: the row exists in the previous report and was not recomputed. The study uses **39 scored toy rows, no V6–V10 pair**, so it does not show that V10 results are version-stable. The same report finds the dominant mechanism is PEP 709 (CPython 3.12 comprehension inlining), so 3.9 and 3.11 traces differ structurally from 3.12+. **Frozen results are valid for CPython ≥3.12 (3.13) only.** **Unresolved:** the artifact and requirements lock say CPython **3.13.15**, while `FREEZE_V8.json` and `FREEZE_V10.json` say **3.13.5**. The previous report says it could not establish which interpreter produced the committed sensitivity file. Bit-identical output on 3.13.5 supports no practical difference but does not resolve the discrepancy.

**SeqCoBench (Agent 3).** The counts 332 eligible / 188 both-class at edit size 2 / 87+41+60 / 860 pairs (400 SP + 460 SA) / 259 test pairs are *consistent* across Agent 3's JSON and the previous sprint's logs (`feas11.log`, `feas13.log`). Agent 3's script reuses the same pipeline and the same repo entry-policy module, so this is **not an independent reproduction** (REVIEWED). I did not rerun it. Open items:
- Provenance and authorship statements (Hugging Face `nickil/seqcobench`, MBPP origin, the "25 transformation types") were not verified against the dataset card, and no network access was used (UNAUDITED).
- The "332 eligible" figure is conditional on SBG's own harness succeeding on the input battery (29% yield). This selects programs on SBG-compatibility, which narrows external validity.
- "Zero AST overlap with 13,544 files" is Agent 3's own result and was not reproduced.
- Power figures assume σ = 0.152, taken from the V10 interval. They are model-based projections and should be marked PRELIMINARY.
- The proposed hypothesis family (H1–H4, Holm) is not the frozen V10 family (H1–H6). Fine for a new protocol, but not comparable by name.
- `unwitnessed_mutations_at_e2` = 206 and `corrupted_preserving_at_e2` = 1 indicate label-oracle limits that the report does not discuss. Labels depend on a differential output oracle on the test battery, i.e. "protocol-input equivalence", not formal semantic equivalence.
- A rejected-alternatives table lists "~65% moderate" yield for HumanEval and "~30%" for MBPP. These percentages have no file behind them in what I checked (UNAUDITED).
- **No SBG score on SeqCoBench exists. SeqCoBench is a candidate and a protocol, not a result.**

**Java (Agent 5 and previous sprint).** `eligibility_quixbugs_java.json` (30 eligible / 10 excluded) and the smoke JSON are present. Smoke results (n = 3, authored by the same agent): `SUMDIGITS` changed variant V5 0.1253 (oracle differs on 10 inputs); `COUNTVOWELS` changed variant V5 0.0 and the oracle shows **no differing input** (a mislabelled positive); `MAXRUN` changed variant differs on 1 input, V5 0.0; all three preserving variants V5 = 0.0. This shows mechanics only. The 12 passing tests and overhead figures were not reproduced here (REVIEWED). `STANFORD_GATE.json` expects a Java results file or a claim-removal record; neither exists.

**COBOL (previous sprint).** The assessment says explicitly that no COBOL score was produced; toy compile/run/trace only; estimate 19–28 working days (judgement); recommends deferral. The deferral argument (different instrumentation and abstraction, so a COBOL result would not validate the Python method) is sound. REVIEWED.

**Repository gate.** `artifacts/final/STANFORD_GATE.json` (modified 30 Oct, before the V8–V10 work) reports 8 of 20 categories passing and 12 blocked, including real-program validity and external validity. I did not rerun it, because its writer would modify `artifacts/final/`. It reflects an older evidence state, but it is the repository's own record and should not be ignored.

## 6. Statistical-method review
- **Units.** The V10 and V9c claims use program clusters (19 and 11). Pair counts (638 and 101,761 cross-label comparisons) are not independent units.
- **Bootstrap.** The cluster bootstrap resamples programs. With 19 clusters, percentile intervals are approximate. Agent 4's seed differs from the frozen one, and endpoints differ by ≤0.003.
- **Paired contrasts.** Per-program contrasts use sign tests across programs (exchangeability assumed). Pooled deltas use a cluster bootstrap that preserves pairing.
- **Multiplicity.** The confirmatory family is H1–H6 under Holm. Ablations, LOPO, per-program, SC/SP-family and real-bug sub-analyses are not corrected and are exploratory.
- **Confirmatory vs exploratory.** H1–H3 passed in V10, but V10 is same-author/same-generator, so they establish held-out-program performance, not external generalisation. The state-only contrast has a CI excluding zero but was chosen after seeing V10.

## 7. Reproducibility
- `agent_1/verify_program_robustness.py` runs on CPython 3.13 and reproduces the numbers above (79 checks, 0 mismatches). It imports frozen loaders and writes only to its own folder.
- `agent_4/scripts/audit_v10_independent.py` and `audit_realbug.py` use their own AUROC and bootstrap. Their outputs agree with my independent computations.
- `agent_2/build_taxonomy.py` reproduces its own CSVs, but the classification rules depend on **hard-coded program sets** with no upstream source (§3, item 3).
- I did not rerun the Agent 3 or Agent 5 scripts.

## 8. Frozen-data integrity
Verified before this audit and again at the end: branch `remediation/sbg-v4`, HEAD `93ef3f38…`, empty tracked diff, 14,955 protected files with zero hash differences. See [`../FINAL_SPRINT_COMPLETION_STATUS.md`](../FINAL_SPRINT_COMPLETION_STATUS.md).

## 9. Manuscript suitability

| Result | Suitable as primary result | Suitable with qualification | Not suitable |
|---|---|---|---|
| V10 H1–H3 (V5 above chance; above edit size) | | ✔ as held-out-program, same-generator evidence | as independent external validation |
| V9c, V8 (including the negative V8 result) | ✔ report both | | |
| H4 (incremental over execution statistics) | | | ✔ not established |
| Ablation | | ✔ post-hoc, exploratory | confirmatory claims |
| Per-program robustness | | ✔ exploratory | population inference |
| BugsInPy 0.410 / QuixBugs 0.388 | ✔ report as negative transfer | | detection capability |
| Real-bug failure taxonomy | | only the verified items in §3 | the 7-category counts |
| Python sensitivity | | ✔ as a toy-suite limitation | "V10 is version-stable" |
| SeqCoBench protocol | | ✔ as future work | any performance claim |
| Java / COBOL | | ✔ as feasibility and non-claims | cross-language generality |

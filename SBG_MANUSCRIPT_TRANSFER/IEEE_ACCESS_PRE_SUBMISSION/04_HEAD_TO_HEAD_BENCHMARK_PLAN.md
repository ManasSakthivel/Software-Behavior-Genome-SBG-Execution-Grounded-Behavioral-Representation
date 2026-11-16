# 04 — HEAD-TO-HEAD BENCHMARK PLAN (Agent A4) — PRE-REGISTRATION

*Frozen: 2026-11-14 (system date, IST), written before any held-out (v9c_val / v10_test) AUROC of any A4 baseline was computed.
sha256 of this file is recorded in `PKG/logs/registry/A4_bench.jsonl` (EXP-A4-001) before the first held-out run. Any later edit of this file = protocol deviation, to be logged with a new EXP-ID.*

**Disclosure of prior knowledge (no hiding):** before writing this plan I read the prior audit (`SBG_CURRENT_STATE_FORENSIC_AUDIT_2026-11-04.md` §F–G), which quotes V10 AUROCs of the *frozen* repo predictors
(V5 0.897, sbg_state 0.917, coverage_size 0.779, edit 0.616, M_EX 0.791, H4 +0.006). I have NOT seen any number for any baseline defined in this plan.
The hypotheses in §7 are therefore partly informed by those quoted numbers (marked "informed").
Code is developed on `v9c_dev` / `v9c_train` (labels used there) and smoke-tested label-free on val/test traces (crash/timing check only, no AUROC printed).

---
## 1. Question and scope
Do the strongest feasible competing methods — all run on the *same* pairs, labels, splits and metric library (`experiments/common/eval_lib.py`) — match or beat SBG V5, and does SBG add information beyond edit size, execution statistics and the state genome?
SBG itself is NOT re-implemented: frozen scores from the population rows are used (`sbg_v5, sbg_v3, sbg_temporal, sbg_state`, `sbg_v6/sbg_state_v6` for v10 only). Component ablations belong to A5.

## 2. Common protocol
| item | value |
|---|---|
| populations | `configs/populations/*.json` (shas in `SUMMARY.json`): `v9c_train` 1650/46 (ONLY fitting), `v9c_dev` 464/13 (ONLY model selection), `v9c_val` 432/11 (held-out #2), `v10_test` 638/19 (headline) ; primary rows only |
| score orientation | pre-declared: larger score ⇒ more likely CHANGED (distance semantics). No post-hoc orientation flipping; `edit_reversed` is a *diagnostic only* (declared, not in the Holm family) |
| metrics | `eval_lib`: tie-aware AUROC, AUPRC, program-cluster bootstrap 95 % CI (B=2000, seed 42), P/R/F1/FPR at Youden threshold chosen on **train scores of the same predictor**, paired ΔAUROC (same resamples) with two-sided bootstrap p, one-sided cluster permutation p vs 0.5, `holm`, `matched_concordance`, `stratified_auroc_exact_edit`, `edit_quantile_strata` |
| fitting | only `v9c_train` (logistic = `eval_lib.fit_logistic` L2=1,lr=0.5,5000 its,standardised; trees/forest = own stdlib code; IDF tables; Youden thresholds) |
| selection | only `v9c_dev`: within a baseline *family* the configuration with highest dev AUROC (ties → first in declared order) is the **family representative**. No selection uses val/test. |
| scoring | every *declared* configuration is scored **once** on val and test (frozen grid below); the family representative enters the Holm family; all other configs are reported as EXPLORATORY (full table, no cherry-picking) |
| determinism | `PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1`, Python 3.13.5 stdlib only, seeds fixed (42) |
| traces | read-only shared cache `results/raw/trace_cache/<design_split>/` (run-0 trace of the 11 protocol inputs; schema PROTOCOL §3). Entry function = `entry_function` recorded in the cache per file. Locals snapshots may contain object addresses → scrubbed (`0x…`→`0x`). |
| REPRODUCED/ADAPTED/PUBLISHED | every method labelled in the report; no published numbers are used as evidence (a separate "PUBLISHED (not comparable)" table lists them only for context) |

## 3. Pre-declared Holm family
Per held-out population (v10_test = headline, v9c_val = confirmatory) the family is **ΔAUROC(SBG V5 − baseline representative)** two-sided cluster-bootstrap p, Holm-adjusted over:
`edit_fwd, static_token, static_ast, static_own*, execstat_single*, LR_EX (repo recipe), LR_X, LR_EXx*, forest_nonlinear*, sbg_state, sbg_v3, sbg_temporal, valuespectra*, traceseq_rename_robust*, traceseq_naive*, pathspectra*, birthmark_k*, tce_analogue*, output_indep_frac40` (`*` = dev-selected representative of the family) — m = 19.
Not in the family (reported descriptively): label-oracle ceilings, diagnostics (`edit_rev`), all non-selected configs, incremental-value deltas (own family of 8 deltas, Holm separately, §6).
Cluster permutation p vs 0.5 is reported for SBG V5 and every representative (Holm over the same m+1).

## 4. Baseline definitions and A/B/C/D classification
Legend (A1, §C of `03_…`): **A** directly comparable + faithfully implementable on the shared inputs; **B** adaptable with documented assumptions; **C** qualitative only; **D** not comparable/not feasible here.
"out-free" = reads no return value/stdout/exception text of the protocol inputs; "privileged" = reads outputs.

| ID | Family (representative key) | Definition (score; larger ⇒ CHANGED) | Class | Label | Reads outputs? | Config grid (all scored; selection on dev) |
|---|---|---|---|---|---|---|
| B01 | `edit_fwd` | repo `_edit_size` (changed lines of `ast.unparse` diff) = row field `edit`; `edit_rev` = −edit diagnostic | A | REPRODUCED | no (source only) | none |
| B02a | `static_token`, `static_ast` | frozen row fields (weighted-Jaccard distance of token / AST multisets; identifier text kept) | A | REPRODUCED (repo) | no | none |
| B02b | `static_own` | own stronger static distances (§B02b): `tok_lev_raw`, `tok_lev_alpha` (token-level Levenshtein, α-renamed identifiers), `astseq_lev_types`, `astseq_lev_alpha` (Levenshtein on pre-order AST node sequence = tree-edit-script approximation), `tfidf2`, `tfidf3` (α-renamed AST-node n-gram TF-IDF cosine distance, IDF fit on train), `bytecode_lev` (Levenshtein on normalised `dis` opcode stream) | A | ADAPTED (own) | no | 7 |
| B02c | `tce_analogue` | Trivial-Compiler-Equivalence analogue: 0 if normalised artefact equal else 1; `tce_ast` (α-renamed, docstring-stripped `ast.dump` equal), `tce_bytecode` (normalised opcode stream equal) | A (algorithm) | ADAPTED (Python analogue of Papadakis ICSE'15; predicts EQUIVALENT when equal) | no | 2 |
| B03a | `execstat_single` | single exec-statistics distances: `exception_fraction, call_count, coverage_size, n_functions` (frozen rows) + `n_events` (ratio distance from cache stats) + `trace_len_mean` (mean over inputs of normalised event-count difference) | A | REPRODUCED (4) / ADAPTED (2) | no | 6 |
| B03b | `LR_E, LR_X, LR_EX, LR_EXx, LR_Xx` | logistic combiners via `eval_lib.fit_logistic` on train: E=[edit]; X=[exc,call,cov]; EX=[edit]+X (repo recipe); EXx=[edit]+X+[n_functions,n_events,trace_len_mean]; Xx= exec only extended | A | REPRODUCED (LR_E/X/EX: repo recipe) / ADAPTED (x) | no | 5 |
| B03c | `forest_nonlinear` | CART decision tree (Gini, depth d) and random forest (n=50 trees, √p feature bagging, row bootstrap, seed 42), own stdlib code, fit on train; features EXx (with edit) or Xx | A | ADAPTED | no | `DT_d2, DT_d3, DT_d4, RF_d3, RF_d4, RF_d6` × {EXx, Xx} = 12 |
| B04a | `sbg_state` | frozen state-genome distance (rows) | A | REPRODUCED (repo; reference row) | no (reads locals reprs; V6 caveat) | none |
| B04b | `valuespectra` | Xie & Notkin-style value spectra / DCI-style observation points from cached locals snapshots: per input, multiset of observation points; score = 1 − weighted-Jaccard, aggregated by mean/max over the 11 inputs. kinds: `args` (call-event values only; *output-free*: no return/exit state), `entry_exit` (call+return snapshot pairs = X&N value spectrum; **privileged**: exit locals reveal results), `exit` (return snapshots only; privileged). Values sorted (names dropped ⇒ local-rename-robust). function names: `raw / entry-canon / full-canon (first-call order)`. abstraction `raw` / `abs` (type + length/sign bucket) | B | ADAPTED (abstract-level source only) | `args`: no; others: yes (internal) | 3×3×2×2 = 36 |
| B05a | `traceseq_*` | per input, sequence of (event-type, function) tokens of base vs variant: `lcs` (normalised indel/LCS distance, bit-parallel), `kgram2/3/4` (1 − Jaccard of k-gram sets = dynamic-birthmark style), `tfidf13` (cosine distance of 1–3-gram TF-IDF, IDF on train), `firstdiv` (1 − first-divergence position / max len); tokens `call` (c) or `cre` (c/r/e); function canon `raw` (naive) / `entry` (entry fn → token ENTRY) / `full` (first-call order anonymisation as in SBG); agg mean/max over 11 inputs. **Representatives:** `traceseq_naive` = best config among canon=raw; `traceseq_rename_robust` = best among canon∈{entry,full}; `birthmark_k` = best among measure∈{kgram2,3,4} (canon any) | B (A for the birthmark algorithm, B for the task) | ADAPTED (Sumner/Myles–Collberg-inspired; not those methods) | no | 2×3×6×2 = 72 |
| B05b | `pathspectra` | line-level path/spectrum distances: key = raw line number or `shape` (source line with identifiers erased; whitespace-normalised); kind = `covset` (Jaccard of covered lines), `hitmulti` (weighted Jaccard of line-hit counts from `l` events = Reps/Harrold line spectrum), `invpath` (weighted Jaccard of per-invocation executed-line sequences = Ball–Larus-style complete-path spectrum); agg mean/max/pooled; plus `fnprofile` (L1 distance of per-function line-event counts; canon raw/entry/full). | B | ADAPTED (abstract-level) | no | 2×3×3 + 3×3 = 27 |
| B06a | `output_oracle_ceiling` | on the 11 protocol inputs from the cache: fraction of inputs whose (ret, exc, stdout) differ between base & variant (K&A behaviour sampling / BERT / differential-testing core); `any` variant; `changeguard_cmp` = same + differing ordered external-call-name log (external = called name not defined in module) | **B** (class would be A on the label-defining inputs, but tautological) | ADAPTED | **privileged** | *Sanity ceiling only — never a competitor, excluded from Holm & rankings* |
| B06b | `output_indep_frac40` (fixed, not selected), `output_indep_any40`, `output_indep_frac11`, k-curve k∈{1,2,4,8,16,32,40} | **independent-input output differencing** (Kessel–Atkinson/behaviour-sampling & ChangeGuard-comparator non-LLM core): per base program, a NEW battery of up to 40 inputs from an own generator (§5) executed by me (plain execution, SIGALRM 1.5 s/input, subprocess per file) on base and variant; score = fraction of inputs whose (return repr, exception type+msg, stdout, post-call argument repr) differ. `any40` = ChangeGuard decision rule (k=40 instead of 300). | **B** | ADAPTED, labelled "K&A-style / ChangeGuard-comparator-style"; never "as published" | **privileged** | 1 fixed rep + exploratory variants |
| B07 | DCI/DSpot | needs Java test amplification; the A-priori Python analogue collapses to B06 / B04b `exit` | **C** | not run as DCI | — | — |
| B08 | ChangeGuard faithful (LExecutor neural value injection) | needs HF transformers + fine-tuned model, no network installs | **D** (comparator-only = B06) | **BLOCKED** | — | continuation: install torch+transformers, clone sola-st/ChangeGuard, run on pair files |
| B09 | Testora/Mokav/ProbeGen/SemaDiff/PatchGuru/EquiBench | LLM + PR text / different label regime | **D** | BLOCKED (no LLM/API by task rule) | — | — |
| B10 | TRACED/Wang-Singh-Su/blended/CodeExecutor/NExT | GPU/torch + pretrained | **D** (qualitative C) | BLOCKED; no stdlib proxy claimed | — | — |
| B11 | DyCLINK, SymDiff, ARDiff, RVT, DiSE, shadow SE | Java/C instrumentation or symbolic engine; no Python implementation obtainable offline | **C/D** | BLOCKED | — | — |
| B12 | ChangeGuard/Testora/Mokav/K&A published numbers | other datasets | **PUBLISHED (not comparable)** | listed only in a separate table | — | — |

### B02b/B05/B04 normalisation details (frozen)
* α-renaming: every identifier that is a function name, parameter, or assigned/loop/comprehension variable of the file (not a builtin, not an attribute name) is replaced by `v<k>` in order of first appearance in a pre-order AST walk; constants kept.
* `entry` canon: only the recorded entry function name → `ENTRY`; `full` canon: all function names → `f<k>` by first call order within each input trace (as in SBG's own anonymisation, therefore the `full` variants are *not* an independent test of rename robustness of SBG); `raw`: names unchanged (naive; expected to be hurt by SP-2).
* Wrapper frames `<lambda>` (protocol driver) are removed before token extraction in all trace baselines.
* `abs` abstraction of a value repr: `literal_eval` → (type, sign-bucket) for numbers, (type, len) for str/list/tuple/dict/set; fallback: digits→`N`.

## 5. Independent-input generator (B06b), frozen design
For each base program (89 programs over the 4 splits): parse the entry function of the *original* (base) file; per parameter choose from annotation family (`int, float, str, bool, list, dict`; all entries here are bare annotations) a **template pool** (list: flat int lists, non-negative lists, int pairs, int triples/weighted edges, 0/1 grids, int grids, word lists, symmetric 0/1 adjacency matrices, intervals; str: lowercase/mixed/bracket/numeric strings; dict: random digraph adjacency with int or letter keys; int: small/medium ranges). Candidates (≤ 400, `random.Random(sha1(base_id))`) are drawn jointly, **filtered by running the ORIGINAL base program only** (keep inputs where the base returns without exception within 1.5 s; target 40; need ≥ 12 else the program is marked `BLOCKED_NO_VALID_INPUTS` and its pairs are `NaN` for this baseline). Inputs identical to any protocol-battery input are dropped (independence). Then every file (base/variants) of the program runs the same battery. SBG's score on these pairs stays the frozen one ⇒ **SBG and this baseline see different inputs**, this baseline sees ≥ 3.6× more and structurally valid inputs (advantage to the baseline; the `frac11` variant equalises the budget). Programs without a battery are excluded for B06b and the comparison against SBG for B06b is reported on the covered subset *and* with uncovered pairs scored 0 (both).
Known weakness (declared): a CHANGED pair may be unobservable on random valid inputs (label observability was audited on protocol inputs only).

## 6. Analyses
1. **Results matrix** every baseline × {v10_test, v9c_val}: AUROC [cluster CI], AUPRC, P/R/F1/FPR@train-Youden, cluster permutation p, matched-set concordance, paired Δ vs SBG V5 [CI], p, Holm (family §3), Cliff δ = 2·AUROC−1.
2. **Stratified**: exact-edit-size AUROC (`stratified_auroc_exact_edit`), edit-quantile (q=3) AUROC, matched-set concordance; by `sc_type` (AUROC CHANGED(sc k) vs all EQUIVALENT); per-`transformation_type` FPR of EQUIVALENT rows at train-Youden; per-program AUROC table + number of programs on which each baseline beats SBG V5 (ties 0.5).
3. **Incremental value** (same recipe for every X): logistic combiner(edit+exec3+X) vs combiner(edit+exec3) fitted on train, paired ΔAUROC on v10/val for X ∈ {sbg_v5 (=H4 reproduction), sbg_state, sbg_v3, sbg_temporal, valuespectra*, traceseq_rename_robust*, pathspectra*, output_indep_frac40}; secondary version with EXx base; Holm over the 8 deltas per population (X = representatives selected on dev). **Exploratory (labelled):** leave-one-program-out refit *within* the held-out population (exact L2-logistic via IRLS; pooled out-of-fold AUROC).
4. **Trivial-beats-SBG check**: report every single-feature predictor (state genome alone, coverage_size, n_events, trace-length ratio, call_count, …) vs SBG V5 with paired Δ.
5. **Runtime/memory**: 50 deterministic pairs of v10_test (first 50 primary pairs sorted by sha1(pair_id)), clean subprocess per method, scoring wall seconds per pair (`perf_counter`), peak RSS (`ru_maxrss`, bytes on macOS); SBG = frozen extraction of base+variant (read-only import of `SBG/experiments/final/extraction.py`) + `score_pair`; extraction cost of the shared trace dump from each record's `extract_seconds`; independent-input runner timed per file.
6. **External corpora (BugsInPy/QuixBugs)**: supplementary only; A5 owns them; run only if time permits (otherwise logged NOT RUN).

## 7. Hypotheses (declared before held-out scoring)
* H-1 (informed) SBG V5 > `edit_fwd` on v10 (repo H3) and on val.
* H-2 (informed) the best execution-statistics combiner is not significantly worse than SBG V5 on v10; the frozen-recipe `LR_EX` is worse (combiner transfer failure).
* H-3 (informed) `sbg_state` alone ≥ SBG V5 on v10 (audit: 0.917 vs 0.897) — i.e. the V5 fusion does not beat its own state component.
* H-4 `output_indep_frac40` (privileged) ≥ SBG V5 on both held-out sets; if not, the label is not recoverable from independent random inputs, which is itself a finding on label validity.
* H-5 rename-robust trace-sequence / birthmark representatives ≈ `sbg_v3`-level; naive variants are hurt on SP-2 pairs (FPR for SP-2 higher than rename-robust).
* H-6 (informed) incremental value of SBG V5 over edit+exec stats: ΔAUROC CI contains 0 (reproduces repo H4 +0.006 [−0.069,+0.068]); same for state/trace-seq/value-spectra (no baseline "X" will show significant increment) — hypothesis stated both ways; any outcome reported.
* H-7 oracle ceilings reproduce labels: on **v10_test** (label "oracle-validated") AUROC(O1) ≈ 1 up to argument-mutation-only CHANGED pairs (sanity). **Pre-freeze finding on v9c_train/v9c_dev (labels used there, allowed):** the V9c labels are only *static-observability-audited*, so the oracle ceiling is NOT ≈ 1 there (train: 245/805 CHANGED pairs show no output/exception/stdout difference on the 11 inputs, 70/805 EQUIVALENT pairs (SP-8: 37, SP-11: 33) DO show a difference, e.g. `UnboundLocalError` in the SP-8 variant; train oracle AUROC 0.79–0.80, dev 0.85). Expectation for v9c_val: ceiling < 1 similarly; this is reported as a label-validity finding of V9c, not as a failure of the oracle. H-7 is therefore stated as: ceiling(v10_test) ≥ 0.95, ceiling(v9c_val) < 0.95 (informed).

## 7b. Pre-freeze implementation notes (added 2026-11-14 before EXP-A4-001 freeze)
* v9c_train program `math_gray_code` (40 primary pairs) has **no trace-cache entry** (orchestrator log EXP-ORCH-003: `FAILED rc=-9 1057.4s`, SIGKILL after ~7 GB RSS). All 40 pairs are excluded from every train-fit/threshold/IDF/independent-input computation (train N = 1610 pairs, 45 programs). Held-out and dev populations are complete (no exclusion). SBG frozen scores are unaffected.
* Selection = highest dev AUROC per family, computed on v9c_dev only; the thresholds (Youden) are recomputed on the reduced train set for every reported predictor.

## 8. Deviation and iteration rules
* Held-out numbers are produced by `run_benchmark.py --stage heldout` exactly once per frozen config set (EXP-A4-0xx). If a code bug is found after seeing held-out numbers: log as protocol DEVIATION in the registry, re-freeze under a **new** EXP-ID, keep the earlier outputs, report both.
* Failures, timeouts, programs without battery, missing traces: logged in `results/raw/EXP-A4-*/` and in report §"what failed".
* No test-set-derived choice anywhere (representatives from dev, thresholds/IDF/trees from train).

## 9. Experiment IDs (see registry)
EXP-A4-001 plan freeze · 002 trace-feature extraction (all four splits, label-free) · 003 independent-input batteries + execution · 004 train fit / dev selection · 005 held-out scoring v9c_val+v10_test + statistics · 006 incremental-value matrix · 007 runtime/memory · (008+ deviations/supplementary).


---
## 10. Dated Protocol Amendment: Authorization of Frozen Wave-1 Held-Out Scoring (2026-11-14 21:45 IST)

**Amendment Status:** Formally Registered & Authorized (Option 2).

### Declarations & Verification:
1. **User Authorization:** The user explicitly authorized the one-time held-out scoring of the frozen A4C wave-1 configuration on `v10_test` and `v9c_val` under strict research-integrity protocols.
2. **Baseline Verification Artifact:** Published `results/raw/EXP-A4R-001/VERIFIED_BASELINES.json` cataloging all 9 predecessor baseline modules, verifying bit-exact SHA-256 matching with the frozen configuration, and disclosing all baseline limitations (including label-oracle tautology for output reading on protocol inputs).
3. **Frozen Configuration Lock:** Verified and registered `frozen_config.json` SHA-256: `f52bfaee96f501fc19198de2a585dcfc500e0ae21e13f2dec0d3d670251e7bdb` (created 2026-11-14 20:19:17 IST prior to any held-out evaluation).
4. **Zero Held-Out Leakage Confirmation:** Confirmed that zero held-out prediction files exist in `v10_test` or `v9c_val`. All models (LR, CART, RF, Incremental) were fit exclusively on `v9c_train` (N=1610, excluding `math_gray_code`), all representatives were selected strictly on `v9c_dev` (N=464), and all decision thresholds (Youden $J$) were computed exclusively on `v9c_train`.
5. **Wave-2 Confinement:** All wave-2 competitors (`competitors_new/`) remain strictly development-only and are prohibited from held-out scoring.
6. **One-Time Execution Mandate:** Scoring on `v10_test` and `v9c_val` will be performed strictly once; all raw predictions, metrics matrices, bootstrap resamples, logs, and SHA-256 manifests will be permanently preserved in `results/raw/EXP-A4C-003/`, `results/raw/EXP-A4C-004/`, `results/tables/`, and `WP_A_B_COMPARATIVE_BENCHMARK/`.

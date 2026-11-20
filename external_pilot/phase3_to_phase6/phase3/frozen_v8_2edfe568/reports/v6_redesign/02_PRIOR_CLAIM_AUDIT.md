# 02 — Audit of Prior Claims (verified against source, not against prior reports)

Scope: the November 2026 `reports/external_validation/*` package and the `reports/v6_investigation/*` proposals, which declared
"READY FOR SUBMISSION" and "VERIFIED" for several claims. Each item below was checked in code or data. Historical files are not modified.

## A. What "SBG V5" means in each place (the baseline is not one thing)

| Where | What is called "V5" | Is it `sbg/v5`? |
|---|---|---|
| `artifacts/final/pairs_*_output_free_v8.jsonl` (`scores.sbg_v5`) | `0.50·d_v3 + 0.25·d_temporal + 0.25·d_state` via `experiments/final/extraction.py::score_pair`, using `sbg.v3`, `sbg.v5.temporal_genome_v5`, `sbg.v5.state_transition_genome` | **Yes — the real V5** |
| `reports/external_validation/{quixbugs_*,evaluate_bugsjar,evaluate_codeflaws}.py` | `0.40·exc + 0.30·steps + 0.15·lines + 0.10·state + 0.05·topo`, a new ad-hoc formula with name-keyed variable-dict state distance | **No.** The weights 0.40/0.30/0.15/0.10/0.05 appear nowhere in `sbg/`. |
| `reports/v6_investigation/SBG_V5_COMPLETE_TECHNICAL_AUDIT.md` | describes the ad-hoc formula above as "SBG V5" | **No — it mis-describes V5.** Its "flaws" (variable-name keys, line-number sets) apply to the ad-hoc harness; real V5 uses an abstract value domain and anonymous function indices (`sbg/v5/state_transition_genome.py` docstring, SP-1/SP-2 invariance). |

**Decision:** the only V5 baseline used in V6 evaluation is the real one (`sbg_v5`, `sbg_v3`, `sbg_temporal`, `sbg_state`, `v5_full` from `score_pair`).

## B. Per-benchmark findings

| Claim in prior package | Finding (evidence) | Status |
|---|---|---|
| **Bugs.jar** AUROC 1.000, N=24, "validated Java" | 8 hand-written inline snippets, not Bugs.jar projects (`evaluate_bugsjar.py` `CASES`, line 39ff). `execute_java_case` compiles but **never invokes the method**; `steps = len(code.splitlines())*2`; `lines = range(1, n_lines+1)` (`:371-375`). Exception term is `exc_diff = 1.0 if "Bug:" in buggy_code else 0.0` (`:403`): a **label-leaking string test**. Negatives are `fixed vs fixed` (distance ≡ 0 by construction) and a hand refactor. | **INVALID — not a behavioural measurement; not validation.** |
| **Codeflaws** AUROC 1.000 (state) / 0.7083 (raw), N=36, "validated C" | 12 embedded toy programs (`evaluate_codeflaws.py`, inline `"inputs": [...]`), not Codeflaws instances. `compile_and_trace_c` runs the binary but sets `steps = n_lines × n_input_tokens` and `lines = range(1, n_lines+1)` (`:577-582`); **`state_diff = 0.7·token_diff + 0.3·line_diff` is a static text diff** (`:599`). It coincides with the edit baseline (`edit_size = (line+tok)/2`), explaining AUROC 1.0 for both. Negatives include identity pairs (distance 0). | **INVALID — static diff labelled "state genome".** |
| **CLM-03** "SBG computable across Python, Java and C — VERIFIED" | Rests on the two items above. | **UNSUPPORTED.** |
| **QuixBugs repaired native** raw 0.4562 / state 0.6237 | Reproduced from `quixbugs_repaired_native_all_pairs.csv` (152 pairs: 40 real-bug positives; 112 negatives = SP-1/2/3/6 variants): `sbg_v5` 0.456, `state_dist` 0.624, `exec_steps_diff` 0.715, `edit_size` 0.614. Uses real `sys.settrace` traces, but with the ad-hoc formula (§A). | Raw numbers **reproduced**; they are *not* V5 numbers. |
| QuixBugs "LR SBG 0.8336 vs LR conv 0.6467; Δ=+0.2188 (p<0.001)" | Fitted-model CV results are **not recomputed** here (no per-fold predictions committed; CV with 40 clusters, 152 rows, up to 4–8 features). The harness script reads `…/IEEE_ACCESS_PRE_SUBMISSION/reproduction/clean_checkout/external/quixbugs`, which does **not exist** in the repo, so it cannot be re-run from the checkpoint. The "conventional" baseline omits `exec_steps_diff`-style features that alone reach 0.715. | **UNVERIFIED; do not cite.** |
| **BugsInPy** AUROC 0.4099 | The number is a hard-coded literal in `generate_*_manifest_and_matrix.py`. The real pair-level file `artifacts/final/pairs_bugsinpy_output_free_v7.jsonl` exists and is re-analysed in V6. Failure mode (inputs raising before the defect) is documented in `SBG_BUGSINPY_FAILURE_ANALYSIS.md`. | Re-derive from pairs; the prior "RF conv 0.915" is a format shortcut, not evidence about SBG. |
| **SeqCoBench** (N=1364, AUROC 0.612/0.824) | **No pair data in the repo** (only `verify_seqcobench.py` and a counts JSON). All SeqCoBench numbers, including identical LR/RF columns, are literals in the matrix generator. The bibliographic title given in `SBG_SEQCOBENCH_PROVENANCE_AUDIT.md` must be checked against the original paper (see literature review). | **UNVERIFIABLE from the repo.** |
| "Synthetic V10 0.8968, Δ=+0.0063" | Consistent with the V10 pair files (`V10_INDEPENDENT_EVALUATION.json`); V10 is an observed, not pristine, set. | Plausible; re-analysed in V6 as non-pristine. |
| "Verdict: READY FOR SUBMISSION" (red-team audit) | Contradicts `STATUS.md` (V5 *not validated*: reversed edit size 0.876 vs V5 0.694 on frozen v8 test). Rests partly on the invalid items above. | **REJECTED.** |

## C. Defects in the *real* V5 evaluation (inherited and carried into V6 design)

1. **Label noise in EQUIVALENT class.** Labels are bound to the generator call site; 73 of 842 train EQUIVALENT pairs (SP-8: 37/83; SP-11: 36/42) produce different outputs or exceptions on some input (`EQUIVALENT_LABEL_AUDIT.json`). Equivalence is never execution-checked.
2. **CHANGED class is not guaranteed observable.** Mutations are accepted by a *static* observability test only; some mutants may be behaviourally equivalent under the test inputs.
3. **Edit-size confound.** SP-3/5/8/11/12 rewrite or add code while each SC mutation edits one site. Reversed edit size: AUROC 0.849 (train), 0.876 (test). Any representation that is monotone in "how much changed" inherits this.
4. **No differential-testing baseline.** Pair scores deliberately never read outputs, so the strongest conventional behavioural baseline (compare outputs and exceptions on the same inputs) is absent from every previous comparison.
5. **Silent degradation:** `distance_v5` returns 0.5 on extraction failure and 0.0 for a missing layer; `score_pair` substitutes `d_v3`. A failed observation is indistinguishable from a measured "no change" except via the `v5_full` flag, which no reported number conditions on.
6. **No pristine holdout.** v8 test, v10 and all externals have been observed (`TEST_SET_CHRONOLOGY.md`).

## D. Consequences for V6 design and reporting

* Keep **all original labels**; add (never replace) a pre-declared secondary stratum of *oracle-confirmed* pairs for label-noise sensitivity.
* Add a differential-testing baseline and separate **oracle-free** (no return values/exceptions' types compared) from **oracle-available** regimes.
* Every table includes reversed/forward edit-size, static token/AST, execution-volume and a conventional combined model **in the same model family and folds** as the SBG model.
* Evidence status (ACTIVATED / NOT_ACTIVATED / UNKNOWN) is a first-class output; nothing missing is encoded as "no change".
* The evaluation of external Java/C is not claimed. Bugs.jar/Codeflaws are not used.

# SP-2 Forensic Analysis — Phase 4 Wave 4

**Status:** COMPLETE. Root cause PARTIALLY confirmed via direct instrumentation + EXPLORATORY diagnostic.

**Current reported result (H10 Wave 2):** AUROC ≈ 0.258722 (worst SP type in the entire benchmark).

## Investigation Question

Why does B07 judge SP-2 (FUNCTION_RENAME) — a semantics-preserving transformation — as MORE dissimilar than genuine behavioral changes (SC mutations)?

## Root Cause Candidate 1: Entry-Function Selection Mismatch (CONFIRMED TO EXIST, MINOR CONTRIBUTOR)

SP-2's rename transform (`benchmark/transformations/preserving/transformations/sp2_function_rename.py`) prefixes unmatched function names with `fn_` (e.g. `heapsort` -> `fn_heapsort`). Crucially, it collects ALL top-level function names as rename candidates, including underscore-prefixed "private" helpers (e.g. `_sift_down` -> `fn__sift_down`). Because `_sift_down` is filtered out of B07's public-function fallback (`name.startswith("_")`) in the BASE program, but `fn__sift_down` is NOT filtered in the VARIANT (it no longer starts with `_`), and alphabetically `"fn__sift_down"` < `"fn_heapsort"` (ASCII `_`=0x5F < `h`=0x68), B07's alphabetical fallback selects the HELPER function in the variant while selecting the DRIVER function in the base. This is confirmed directly for `test__sort_heapsort__sp-2_s0`: base selects `heapsort` (driver, 1 param), variant selects a different-role function with a different call signature.

**Quantified across all 39 SP-2 test pairs:**
- Entry-function parameter-count mismatch between base and variant: **6/39 (15.4%)**
- Pairs involving the conc_read_write_lock class adapter: 3 (unaffected — adapter selection is structural, not name-based)

A parameter-count mismatch means B07 is comparing the dynamic execution genome of TWO DIFFERENT FUNCTIONS with different call signatures — not the same function before/after a semantics-preserving rename. This alone is sufficient to produce spurious dissimilarity for those specific pairs, independent of any real behavioral change. Note 15.4% is a **lower bound**: same-arity-but-wrong-function mismatches (e.g. two 1-parameter functions with different roles) are not caught by a parameter-count check alone and may be undercounted here.

### Concrete example: `test__sort_heapsort__sp-2_s0`

- Base (`sort_heapsort.py`): top-level functions are `heapsort(arr)` (driver, 1 param) and `_sift_down(arr, root, end)` (private helper, 3 params, filtered out of B07's fallback because its name starts with `_`). B07's alphabetical fallback selects **`heapsort`** — the correct driver.
- Variant (SP-2 renamed): `heapsort` → `fn_heapsort`; `_sift_down` → `fn__sift_down`. The rename transform renames candidates gathered from **all** top-level function names — it does not exclude underscore-prefixed helpers from eligibility. Because the new name `fn__sift_down` no longer starts with `_`, B07's private-name filter no longer excludes it, and alphabetically `"fn__sift_down"` sorts BEFORE `"fn_heapsort"`. B07 selects **`fn__sift_down`** — the internal helper, a 3-parameter function with an entirely different role and call signature.

The resulting DynamicGenome distance compares a 1-argument sorting driver against a 3-argument heap-repair helper. High dissimilarity is the EXPECTED and CORRECT output of the distance function given these (mismatched) inputs — for THIS pair, the bug is upstream, in entry-function discovery, not in the genome/distance representation itself.

## EXPLORATORY Diagnostic: Call-Graph-Root Oracle Selector

**Label: EXPLORATORY — does not replace or modify production B07; does not feed H7-H12**

Call-graph-root selector: pick the top-level function never called by any OTHER top-level function in the module (excludes names containing `test`). This is structurally the SAME idea already used for the conc_read_write_lock class adapter in Wave 1 (prefer the "outer"/composed entity over an internal primitive).

| | Current production selector | Oracle selector (EXPLORATORY) |
|---|---|---|
| SP-2 stratum AUROC | 0.247163 | 0.277708 |
| EQUIV mean similarity | 0.632124 | 0.671122 |
| CHANGED mean similarity | 0.854699 | 0.854699 (unchanged — SC pairs use production selector) |
| Delta vs current | — | +0.030545 |

**Honest result: the oracle only partially closes the gap.** AUROC improves from 0.247 to 0.278 (Δ=+0.031) — a real but SMALL effect relative to the size of the failure. Both values remain far below 0.5, i.e. **the inversion is NOT resolved by fixing entry-function selection alone.** This means the entry-function-mismatch mechanism, while genuinely confirmed to exist, is **NOT the dominant cause** of SP-2's inversion. Fixing it recovers only a small fraction of the gap between the observed AUROC (~0.25) and a non-inverted baseline (0.5).

The majority of the AUROC deficit must be attributable to Wave 0 Agent E's other two hypotheses, neither of which is independently isolated by this diagnostic:
- **(B) `anon_call_freq` index divergence:** even when the SAME function is correctly matched, SP-2's renaming changes the first-call order used to build `anon_call_freq`'s integer keys (see `sbg/v2/execution/normalizer.py`), misaligning the histogram between base and variant.
- **(C) SP-2 AST transformer's `Attribute`-node call-site bug:** `self.method()` call sites are not renamed by `sp2_function_rename.py`'s `visit_Call` (it only handles `ast.Name` call targets), which can produce `AttributeError` crashes on class-based programs, inflating exception-based distance for programs that are otherwise behaviorally identical.

## Classification (per Wave 4 mandate: A–F)

**A mix of (D) benchmark/transform construction defect and (F) entry-discovery-heuristic limitation, with the entry-discovery mechanism confirmed but only a MINOR contributor (~+0.03 AUROC of the ~0.25 deficit from 0.5).** SP-2's rename transform does not preserve the public/private naming convention it should respect, and B07's entry-fn fallback relies on a naming convention that is not robust to this — this is real and confirmed, but small. The larger share of the deficit is most plausibly explained by hypotheses (B) and (C), both of which are ALSO benchmark/transform or feature-representation limitations rather than (A) a genuine case of behavioral change unobservable through current inputs.

**No evidence in this diagnostic supports classifying SP-2 as a fundamental observability limit of execution-grounded representations.** But the initial Wave 0 hypothesis that entry-mismatch was the PRIMARY driver is now shown to be an overstatement: the full picture is only partially explained, and a genuine open gap remains.

## What This Means for RQ1 / RQ4

SP-2's AUROC≈0.259 should NOT be simplistically interpreted as "dynamic SBG cannot handle function renaming," nor as "this is purely an entry-discovery bug now fixed." The honest conclusion is:
1. A real, confirmed, but MINOR contribution (+0.03 AUROC, affecting at least 15.4% of pairs) comes from entry-function mismatch — a benchmark/transform-generator and entry-discovery-heuristic defect, not a representational limitation.
2. The MAJORITY of SP-2's inversion (AUROC remains at 0.278 even after the fix, vs. a benchmark-wide mean of ~0.47 for other SP types) is **unexplained by this diagnostic** and most plausibly caused by feature-representation sensitivity to call-order/renaming (hypothesis B) and/or a separate transform-generator bug affecting class-based programs (hypothesis C) — neither independently confirmed here.
3. SP-2 remains a genuine, only-partially-understood robustness gap. It is reported honestly as such, not resolved, and not classified as a fundamental limit of execution-grounded observability either.

## Integrity Notes

- This diagnostic does not modify `baselines/v2/b07_dynamic_v2.py` or any frozen benchmark file. The oracle selector is implemented ONLY in this standalone diagnostic script (`experiments/v2/sp2_forensic_diagnostic.py`).
- The oracle is an SP-2-specific diagnostic (call-graph roots), tested only on the SP-2 stratum; it is NOT proposed as a general replacement for the production entry-fn selector without further validation on other SP/SC types.
- No frozen `pairs_test.jsonl` / `pairs_dev.jsonl` / variant source files were modified.
- This diagnostic does NOT change H10's reported verdict (`docs/v2/H10_ROBUSTNESS_ANALYSIS.md`), which correctly reports the PRODUCTION B07 AUROC for SP-2 without modification. The oracle result is reported here purely as root-cause evidence, per the Phase 4 mandate: "Do NOT tune the model to make SP-2 look better" in any primary metric.

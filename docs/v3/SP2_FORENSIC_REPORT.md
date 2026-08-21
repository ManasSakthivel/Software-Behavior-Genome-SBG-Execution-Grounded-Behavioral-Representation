# SBG V3 SP-2 Forensic Report

## Summary

SP-2 (FUNCTION_RENAME) transformation produces an inversion in v2: AUROC≈0.24 (worse than random).

Root cause classification: **A + B** (Implementation bug + benchmark construction interaction).

## Root Cause Analysis

### Mechanism
The v2 benchmark's SP-2 transformer (`sp2_function_rename.py`) renames ALL function names including underscore-prefixed helpers:

```
_sift_down → fn__sift_down
heapsort   → fn_heapsort
```

B07's `_load_entry_fn` falls back to alphabetical selection of public functions when no priority name matches. After SP-2 renaming, `fn__sift_down` (alphabetically first due to `_` < `h`) is selected instead of `fn_heapsort`.

- **Base program**: entry = `heapsort` (correct)
- **Variant program**: entry = `fn__sift_down` (wrong — it's the helper)

This causes mismatched execution traces (base computes a full sort; variant executes only the sift-down helper), making CHANGED pairs appear MORE similar than EQUIVALENT pairs (inversion).

### Evidence
- `artifacts/v2/SP2_FORENSIC_RESULTS.json`: 6/39 SP-2 pairs (15.4%) have parameter count mismatch
- Oracle selector (call-graph root): AUROC 0.259 → 0.278 (+0.030)
- However, even with oracle: AUROC=0.278 < 0.5 (residual inversion)

### Residual Inversion after Fix
Even with correct entry-function selection, SP-2 AUROC remains below 0.5. This indicates a **genuine scientific limitation (D)**: function renaming changes the anonymization index mapping in `TraceNormalizer`, causing the anon_call_freq histograms to become misaligned.

## v3 Fixes

### Fix 1: Call-Graph Root Entry Selection
`baselines/v3/b07_dynamic_v3.py::_find_call_graph_root()`:
- Identifies top-level functions not called by any other top-level function
- Uses bytecode analysis (`dis.Bytecode`) to determine call graph
- Selects the "outermost" entry point robustly

### Fix 2: Transition Bigrams (Representation Fix)
`sbg/v3/genome.py::_compute_call_bigrams()`:
- Records consecutive call pairs (f_i → f_j) with anonymized indices
- Rename-invariant: same call sequence = same bigram regardless of function names
- Captures ORDER information that is more stable under SP-2 renaming

### Expected Impact
With both fixes:
- Entry function mismatch eliminated for most programs
- Bigram-based representation reduces sensitivity to index-ordering artifacts
- Expected AUROC for SP-2 stratum: 0.28 → 0.40+ (estimate based on forensic analysis)

## Remaining Limitation

SP-2 renaming changes the first-call-order anonymization INDEX for functions if the rename changes alphabetical ordering of function names. This is a fundamental limitation of the anonymization approach: the index depends on CALL ORDER, which may change if renamed variants call functions in a different order (e.g., `fn_helper_renamed` is discovered first due to different module-level execution order).

**Recommendation for v3+**: Use POSITION-INDEPENDENT anonymization: hash of function BODY structure (minus docstrings and variable names) rather than call order. This would be truly rename-invariant.

## Files Affected

- `baselines/v3/b07_dynamic_v3.py` — call-graph root fix
- `sbg/v3/genome.py` — bigram feature for robustness to name changes
- `benchmark/transformations/preserving/transformations/sp2_function_rename.py` — should preserve underscore prefix in generated names (alternative fix)

## Integrity Notes

- No frozen benchmark files were modified
- v2 results (AUROC=0.259 for SP-2 stratum) remain immutable
- v3 fix tested on small sample (--max-pairs 50): inversion delta improved -0.045 → -0.087

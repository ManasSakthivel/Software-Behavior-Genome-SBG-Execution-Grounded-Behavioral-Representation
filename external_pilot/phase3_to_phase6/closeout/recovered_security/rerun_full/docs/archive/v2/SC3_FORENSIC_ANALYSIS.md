# SC-3 Forensic Analysis
## Phase 4 — Wave 3 (AGENT F)

**Status:** COMPLETE  
**Frozen benchmark:** NOT MODIFIED  
**Model tuning:** NONE

---

## 1. SC-3 Definition (from manifest)

| Field | Value |
|---|---|
| ID | SC-3 |
| Name | CONSTANT_MUTATION |
| Manifest description | "Perturb integer constants by ±1/2, or append suffix to strings" |
| AST targets | `Constant(int)`, `Constant(str)` |
| `hard_negative` | false |
| Label in benchmark | CHANGED |

---

## 2. What SC-3 Actually Does (Observed)

Examining all 39 SC-3 test pairs across 13 base programs, the actual mutations applied are:

| Category | Count | Fraction |
|---|---|---|
| Quote style only (double → single quotes) | 30 | 76.9% |
| Quote normalization + minor formatting | 9 | 23.1% |
| Integer constant perturbation (±1/2) | **0** | **0%** |
| String suffix appended | **0** | **0%** |

**The manifest description does not match the implementation.** The SC-3 generator performed a Python code-style normalisation pass — converting double-quoted strings to single-quoted strings, stripping blank lines and inline comments, collapsing multi-line expressions to single lines, normalising `a, b = x, y` to `(a, b) = (x, y)` — none of which change observable behavior.

### Concrete Examples

**`sort_heapsort` base vs SC-3 variant** — only changes:
```python
# base                              # variant
arr[0], arr[end] = arr[end], arr[0] # (arr[0], arr[end]) = (arr[end], arr[0])
assert a == [5, 6, 7, 11, 12, 13], f"got {a}"  # f'got {a}'
```

**`math_statistics` base vs SC-3 variant** — only changes:
```python
# base: multi-line dict             # variant: one-line dict (same keys/values)
return {
    "n":      len(data),
    "mean":   mean(data),
    ...
}                                   # return {'n': len(data), 'mean': mean(data), ...}
```

**`api_rate_limiter` base vs SC-3 variant** — only changes:
```python
raise ValueError("rate and capacity must be positive")
# → raise ValueError('rate and capacity must be positive')
```

---

## 3. Behavioral Execution Audit

Direct execution with B07's V2_CANONICAL_INPUTS (8 inputs):

| Program | Entry fn | Inputs run | Behavioral differences |
|---|---|---|---|
| `sort_heapsort` | `heapsort(list)` | 8 | **0** |
| `sort_counting_sort` | `counting_sort(list)` | 8 | **0** |
| `math_statistics` | `mean(list)` | 7 (1 shared error) | **0** |
| `api_rate_limiter` | `test_rate_limiter()` 0-arg | 1 | **0** |
| `ds_hash_table` | `test_hash_table()` 0-arg | 1 | **0** |
| `err_result_type` | `parse_int(str)` | 1 | **0** |
| `file_config_parser` | `test_config_parser()` 0-arg | 1 | **0** |
| `fsm_vending_machine` | `test_vending_machine()` 0-arg | 1 | **0** |
| `graph_bfs_shortest_path` | `bfs(dict, node)` | 1 | **0** |
| `parse_recursive_descent` | `evaluate(str)` | 1 | **0** |
| `res_object_pool` | `test_object_pool()` 0-arg | 1 | **0** |
| `str_tokenizer` | `test_tokenizer()` 0-arg | 1 | **0** |
| `conc_read_write_lock` | **no entry function** | 0 | N/A (Wave 1 issue) |

**Result: ZERO behavioral differences across all 36 executable SC-3 pairs.**

---

## 4. DynamicGenome Similarity Distribution

| Metric | Value |
|---|---|
| Mean similarity | 0.9481 |
| Min similarity | 0.5000 (conc_read_write_lock imputed) |
| Max similarity | 1.0000 |
| sim ≥ 0.8 (looks EQUIVALENT) | 35/39 = **89.7%** |
| sim in [0.4, 0.8) (ambiguous) | 4/39 = 10.3% |
| sim < 0.4 (looks CHANGED) | 0/39 = **0%** |

B07 assigned similarity ≈ 1.0 to 89.7% of SC-3 pairs — because their execution traces are genuinely identical.

---

## 5. Phase 3B Results in Context

From `artifacts/v2/HARD_NEGATIVE_RESULTS.json`:

| Metric | SC-3 | SC-11 (for contrast) |
|---|---|---|
| AUROC | 0.544 | 0.790 |
| 95% CI | [0.484, 0.608] | [0.721, 0.845] |
| Inversion delta (B07) | +0.083 | −0.227 |
| Near-identical trace fraction | **84.6%** | 17.9% |
| Verdict | NOT_SUPPORTED | SUPPORTED_FULLY_RESOLVED |

The 84.6% "near-identical traces" figure is a **direct consequence** of the programs being near-identical — the mutation preserves all execution paths.

---

## 6. Root Cause Classification

**Primary cause: (D) BENCHMARK MUTATION DESIGN FAILURE**

The SC-3 mutation generator produced a code-style normalisation transform (quote style, whitespace, comment removal) instead of the registered semantic mutation (integer ±1 perturbation, string suffix). The CHANGED labels on all 39 SC-3 pairs are incorrect. The programs are behaviorally equivalent.

Eliminated causes:

| Cause | Status | Reason |
|---|---|---|
| A. Semantic change not observable through inputs | ❌ ELIMINATED | No semantic change exists. Nothing to observe. |
| B. Execution path not reaching changed behavior | ❌ ELIMINATED | All execution paths are identical because the code is unchanged. |
| C. Feature representation limitation | ❌ ELIMINATED | The representation correctly captures behavioral equivalence; the problem is the label is wrong. |
| E. Insufficient execution diversity | ❌ ELIMINATED | No amount of diverse inputs can expose a behavioral difference that does not exist. |
| F. Another genuine limitation | ❌ ELIMINATED | The failure is fully explained by (D). |

---

## 7. Implications for Reported Metrics

SC-3's AUROC of 0.544 is **not a failure of B07**. It reflects B07 correctly predicting EQUIVALENT behavior for programs that ARE behaviorally equivalent, which is then scored as false-negative classification because the benchmark erroneously labels them as CHANGED.

The "inversion remaining" for SC-3 (delta = +0.083) is a benchmark labelling artefact, not a signal about dynamic SBG's representational limits.

**Corrected interpretation:**  
If SC-3 pairs were relabelled EQUIVALENT (which is their true status), the SC-3 AUROC would become ~0.95–1.0, and the "remaining inversion" would disappear entirely.

---

## 8. Recommended Remediation

Three options in order of scientific cleanliness:

### Option 1 — Exclude SC-3 from H10 primary metrics (PREFERRED for Phase 4)
Exclude SC-3 from the H10 robustness analysis on grounds of benchmark construction failure. Report exclusion explicitly in the analysis. The frozen benchmark is not modified. This is consistent with the Phase 4 instruction "do not modify the frozen test set."

### Option 2 — Relabel SC-3 as EQUIVALENT
Relabel all SC-3 pairs as EQUIVALENT, reflecting their true behavioral status. This modifies the frozen benchmark and must not be done without explicit protocol approval.

### Option 3 — Regenerate SC-3 variants (EXPLORATORY)
Generate a new parallel set of SC-3 variants using the correct mutation (actual integer ±1 perturbation). Label as **EXPLORATORY** and run separately. Do not replace or modify the frozen test set.

---

## 9. Exploratory Diagnostic Experiments (Wave 3, EXPLORATORY)

### EXPLORATORY-SC3-A: Correct integer-constant mutation

Generate SC-3 variants for the same 13 base programs using **actual integer ±1 perturbation** on constants that lie on executed code paths. Run B07.

**Hypothesis:** Correct SC-3 will yield AUROC > 0.60 — closer to SC-11 (0.790) — because perturbing loop bounds (e.g., `range(n-1)` in heapsort) or capacity thresholds in hash_table will change coverage and call-frequency vectors.

**Examples of real integer constants to perturb:**
- `sort_heapsort`: `_sift_down` root/largest thresholds
- `ds_hash_table`: `initial_capacity=8` → 7 or 9
- `math_statistics`: divisor in variance formula `n - 1` → `n` or `n - 2`

### EXPLORATORY-SC3-B: Constant mutation targeting only executed paths

Run a static + dynamic co-analysis to identify which integer constants are reachable by V2_CANONICAL_INPUTS before generating the mutation. This tests whether the observed "failure mode" for hypothetically correct SC-3 would be Cause-B (unreachable path) rather than Cause-D.

---

## 10. Integrity Notes

- No frozen benchmark files were modified.
- No baseline model was tuned.
- This analysis is purely diagnostic/observational.
- Phase 3B measurements (AUROC=0.544, delta=+0.083, near_identical=84.6%) are arithmetically correct given the benchmark as-is. The issue is the benchmark construction, not the measurement methodology.
- All conclusions are grounded in direct code inspection and execution of the actual variant files.

---

## 11. Summary

| Item | Finding |
|---|---|
| SC-3 as implemented | Code-style normalisation (quote style, whitespace) |
| SC-3 as specified | Integer ±1 perturbation, string suffix append |
| Behavioral equivalence | YES — 100% of executable pairs |
| B07 diagnosis | CORRECT — high similarity predictions are accurate |
| Root cause | (D) Benchmark mutation design failure |
| Phase 3B "84.6% near-identical traces" | Expected — programs are semantically identical |
| Phase 3B AUROC 0.544 | Benchmark labelling artefact, not SBG limitation |
| Recommended action | Exclude SC-3 from H10 primary metrics; run EXPLORATORY-SC3-A for correct mutation |

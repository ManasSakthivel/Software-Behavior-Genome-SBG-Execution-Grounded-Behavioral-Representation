# SBG FEATURE SCHEMA & VECTOR SPECIFICATION

**Version:** 5.0 (V10 Unified Schema)  
**Encoding:** JSONL / Parquet  
**Reference Implementation:** `SBG/sbg/v5/`, `SBG/experiments/final/extraction.py`

---

## 1. Feature Representation Layout

Each program pair $(P, P')$ produces an auditable feature record containing scalar distance metrics, dimension-level breakdowns, and baseline comparison features.

### Top-Level Record Fields:
```json
{
  "pair_id": "test__ds_min_heap_array__sc1+sp1_s0",
  "base_id": "ds_min_heap_array",
  "split": "test",
  "evaluated": true,
  "scores": {
    "sbg_v5": 0.019025735,
    "sbg_v3": 0.013355247,
    "sbg_temporal": 0.020152680,
    "sbg_state": 0.029239766,
    "exception_fraction": 0.0,
    "exception_component_v3": 0.0,
    "exception_type_jaccard": 0.0,
    "call_count": 0.9375,
    "n_functions": 0.0,
    "coverage_size": 0.0,
    "combined_shortcut": 0.28125,
    "v5_full": 1.0
  },
  "baselines": {
    "edit_distance": 2,
    "ast_jaccard": 0.125,
    "token_jaccard": 0.1428,
    "trace_len_mean": 124.5,
    "trace_len_diff": 18.0
  }
}
```

---

## 2. Detailed Dimension Specifications

| Feature Name | Type | Value Range | Definition & Extraction Logic |
|---|---|---|---|
| `sbg_v5` | `float` | $[0.0, 1.0]$ | Composite distance: $0.50 \cdot d_{\text{V3}} + 0.25 \cdot d_{\text{temporal}} + 0.25 \cdot d_{\text{state}}$. |
| `sbg_v3` | `float` | $[0.0, 1.0]$ | Topology distance: Jaccard distance over line coverage sets and call graph edges. |
| `sbg_temporal` | `float` | $[0.0, 1.0]$ | Sequence alignment distance over instruction type sequence profiles. |
| `sbg_state` | `float` | $[0.0, 1.0]$ | Local variable transition spectrum entropy and value snapshot distance. |
| `trace_len_mean` | `float` | $[0.0, \infty)$ | Mean total number of trace events executed across test input battery. |
| `trace_len_diff` | `float` | $[0.0, \infty)$ | Absolute difference in mean trace event count between $P$ and $P'$. |
| `call_count` | `float` | $[0.0, 1.0]$ | Normalized call volume difference ratio: $|C(P) - C(P')| / \max(C(P), C(P'), 1)$. |
| `coverage_size` | `float` | $[0.0, 1.0]$ | Normalized line coverage set cardinality difference ratio. |
| `edit_distance` | `int` | $[0, \infty)$ | Levenshtein edit distance over canonicalized AST unparsed source strings. |
| `exception_fraction` | `float` | $[0.0, 1.0]$ | Fraction of test battery executions terminating in an unhandled exception. |

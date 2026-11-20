# Workstream 2: V10 Dataset and Artifact Reconstruction Audit

**Audit Date:** 2026-11-07  
**Artifact Inspected:** `artifacts/final/pairs_v10_test_v6exp.jsonl` & `artifacts/paper_evidence/V10_INDEPENDENT_EVALUATION.json`  
**Dataset Specification:** `benchmark/datasets/v10_independent/`  

---

## 1. Executive Summary

The V10 evaluation split was independently reconstructed and verified directly from the raw scored JSONL lines and source programs.

1. **Exact Denominators Verified:**
   - **Total Generated Pairs:** 644
   - **Unevaluated Pairs:** 3 (syntax / runtime execution failure during extraction)
   - **Evaluated Pairs:** **638**
   - **Matched Sets:** **319**
   - **Ground-Truth Distribution:** Exactly **319 CHANGED (50.0%)** and **319 EQUIVALENT (50.0%)**.
   - **Number of Base Programs:** **19** fresh algorithmic programs.

2. **Per-Program Pair Distribution:**

| Program Identifier | Pairs Evaluated | Matched Sets |
|---|---|---|
| `math_knapsack_01` | 48 | 24 |
| `ds_ranked_set` | 38 | 19 |
| `math_coin_change` | 38 | 19 |
| `sort_bitonic_sort` | 38 | 19 |
| `sort_gravity_bead` | 38 | 19 |
| `sort_pancake` | 38 | 19 |
| `graph_network_delay` | 36 | 18 |
| `graph_topological_kahn` | 36 | 18 |
| `sort_radix_sort_lsd` | 36 | 18 |
| `sort_tree_sort` | 36 | 18 |
| `graph_cycle_detection_dfs` | 34 | 17 |
| `ds_min_heap_array` | 32 | 16 |
| `sort_gnome_sort` | 32 | 16 |
| `ds_union_find` | 30 | 15 |
| `str_decode_run_length` | 30 | 15 |
| `str_group_anagrams` | 30 | 15 |
| `sort_stooge_sort` | 28 | 14 |
| `math_fib_matrix` | 26 | 13 |
| `graph_alien_dict` | 14 | 7 |
| **Total** | **638** | **319** |

---

## 2. Edit Distance Confound Removal

- **Mean Edit Distance (Tokens):**
  - `CHANGED` variants: **10.288 tokens**
  - `EQUIVALENT` variants: **8.361 tokens**
- **Forward Edit Distance AUROC:** **0.616046** (95% CI: [0.606281, 0.627539])
- **Significance:** In the earlier flawed V8 test split, a reversed-edit predictor achieved AUROC 0.8759 due to synthetic generation artifacts. In V10, the composed pairing successfully broke this artificial correlation: the forward edit distance AUROC is near chance (0.616), ensuring that benchmark performance cannot be solved by simply measuring code diff size.

---

## 3. Disjointness and Independence Caveats

- **Program Disjointness:** All 19 V10 programs are verified to be disjoint by name and AST structure from all programs in earlier development splits (V6 train/dev, V8 train/dev, V9c train/dev/val).
- **Independence Caveat (Essential Disclosure):** While the 19 programs were held out and never seen during weight fitting or threshold tuning, they share the same authorial style, generator templates, and domain (classic algorithmic problems) as the development corpus, with token-Jaccard similarities between 0.101 and 0.146. They are "held out algorithmic siblings", not an external wild population.

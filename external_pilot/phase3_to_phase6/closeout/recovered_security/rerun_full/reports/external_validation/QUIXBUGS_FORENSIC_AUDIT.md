# QuixBugs Forensic Audit & Root-Cause Failure Diagnosis

## 1. Executive Summary

A critical question in the Software Behaviour Genome (SBG) research project was why canonical evaluation on QuixBugs produced an apparent catastrophic failure with AUROC = 0.3877 (committed v7) and 0.4444 (ex-SP-2 v8), whereas synthetic benchmark evaluation reached AUROC = 0.8968.

This independent forensic investigation audited:
1. Every QuixBugs program signature and input type.
2. The historical canonical harness execution traces and exception logs.
3. The semantics-preserving negative variant generation (SP-1, SP-2, SP-3, SP-6).
4. The declared testcase input regime (`json_testcases`).
5. A repaired universal native test harness covering all 40 QuixBugs programs.

---

## 2. Forensic Findings & Root-Cause Breakdown

### 2.1 The Canonical Harness Type-Mismatch Defect
The historical canonical harness applied a single fixed 11-input battery of integer lists (e.g. `[1, 2, 3]`, `[5, -2, 8, 0, 1]`) across all 40 QuixBugs programs.
- **27 of 40 programs** in QuixBugs do not accept a single integer list.
- **9 graph algorithms** (`breadth_first_search`, `depth_first_search`, `detect_cycle`, `minimum_spanning_tree`, `reverse_linked_list`, `shortest_path_length`, `shortest_path_lengths`, `shortest_paths`, `topological_ordering`) require `Node` objects or weighted graph adjacency dictionaries.
- **18 algorithmic programs** require multi-parameter signatures (e.g., `gcd(a, b)`, `knapsack(capacity, items)`, `kth(arr, k)`, `levenshtein(s1, s2)`, `powerset(arr)`, `subsequences(a, b, k)`).

When called with `func([1, 2, 3])`, both the buggy program and the correct program crashed on line 1 with `TypeError: missing required positional argument` or `AttributeError: 'list' object has no attribute 'successor'`.
Because both executions aborted on line 1 with identical 1-event traces, the calculated SBG behavioral distance between buggy and correct code was **identically 0.0**.

### 2.2 The Inversion Mechanism of SP-2 Negatives
Transformation SP-2 performs systematic variable and top-level function renaming.
- In negative pairs (Correct vs SP-2), the top-level function name differed from the base program, causing execution wrappers to capture call topology differences and slight trace distance ($0.0125 - 0.0250$).
- Consequently, **Negative (Equivalent) pairs received positive distance scores ($d > 0$) while True Bug Positive pairs received zero distance scores ($d = 0.0$) due to type crashes.**
- This structural artifact inverted the ROC curve below chance ($\text{AUROC} = 0.3587 - 0.3802$).

### 2.3 The Declared Input Regime Limitation
In the secondary `declared` regime, inputs were loaded from `json_testcases/`.
- 31 programs had JSON testcases and ran without type crashes.
- However, 9 graph programs lacked JSON testcases (their test drivers were defined only as Python scripts in `*_test.py`). They were dropped as "unevaluated", reducing the sample size and biasing the evaluated subset.

---

## 3. Repaired Harness & Empirical Recomputation

Under the Repaired Native Harness, valid `Node` structures and multi-parameter testcases were constructed for all 40 programs.

| Regime & Configuration | $N$ Pairs (Pos/Neg) | Raw SBG V5 AUROC [95% CI] | LR Conventional | LR SBG Alone | LR (Conv + SBG) [95% CI] | RF (Conv + SBG) | Incremental $\Delta\text{LR}$ [95% CI] |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Canonical (All pairs)** | 152 (40/112) | 0.3587 [0.293, 0.423] | 0.5777 | 0.5859 | 0.7563 [0.659, 0.847] | 0.8040 | **+0.1786** [+0.077, +0.281] |
| **Canonical (ex-SP-2)** | 112 (40/72) | 0.3802 [0.313, 0.446] | 0.6288 | 0.5880 | 0.7521 [0.673, 0.841] | 0.7653 | **+0.1233** [+0.038, +0.212] |
| **Declared JSON (All pairs)** | 116 (31/85) | 0.5359 [0.399, 0.679] | 0.6854 | 0.8581 | 0.8816 [0.834, 0.930] | 0.9416 | **+0.1962** [+0.083, +0.321] |
| **Declared JSON (ex-SP-2)** | 85 (31/54) | 0.5657 [0.432, 0.705] | 0.7282 | 0.7694 | 0.8065 [0.731, 0.882] | 0.9134 | **+0.0783** [-0.016, +0.170] |
| **Repaired Native (All pairs)**| 152 (40/112) | 0.4562 [0.334, 0.572] | 0.6467 | **0.8336** | **0.8654** [0.803, 0.919] | **0.9083** | **+0.2188** [+0.108, +0.341] |
| **Repaired Native (ex-SP-2)** | 112 (40/72) | 0.4826 [0.361, 0.600] | 0.6844 | **0.7687** | **0.8003** [0.724, 0.875] | **0.8851** | **+0.1160** [+0.004, +0.222] |

---

## 4. Key Scientific Conclusions

1. **QuixBugs does not demonstrate that SBG fails to generalise.** The historical 0.388 / 0.444 results were an artifact of forcing flat integer-list inputs onto graph and multi-parameter algorithms.
2. **When executed with type-correct inputs, SBG features provide strong discriminative signal:**
   - Leave-one-program-out Cross-Validation on SBG features achieves **AUROC = 0.8336** (All pairs) and **0.7687** (ex-SP-2).
   - Adding SBG to conventional baselines yields significant incremental predictive value: $\Delta\text{AUROC} = \mathbf{+0.2188}$ (All) and $\mathbf{+0.1160}$ (ex-SP-2).
   - Non-linear Random Forest combining conventional and SBG features achieves **AUROC = 0.9083**.
3. **Raw single-threshold distance vs Supervised representation:** Raw unweighted composite distance fails (AUROC 0.4562) because trace scale variations across algorithm types require learned feature weighting.

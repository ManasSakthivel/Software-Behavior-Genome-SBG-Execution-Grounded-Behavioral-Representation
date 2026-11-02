# FINAL CLAIMS AUDIT
**Branch:** `remediation/sbg-v4`  
**Commit:** `c5bc130ea0909379315a7fdc160aa777c6c04840`  
**Date:** 2026-10-30  
**Auditor:** Bob (research engineering agent)  

**Method status:** SBG V5 is the primary frozen method. SBG V6 remains experimental and is not promoted to a primary result. No V7 or further version introduced.

---

## Claims Table

| Proposed claim | Supporting experiment | Counterevidence | Confidence | Safe wording |
|---|---|---|---|---|
| **1. SBG discriminates on synthetic size-decoupled pairs above chance** | V9c val AUROC 0.751 [0.706, 0.794] (Holm p = 0.002); V10 AUROC 0.897 [0.863, 0.922] (Holm p = 0.003) | V8 (burned): confounded design (NOT DEMONSTRATED); 37% zero-score rate; 30% CHANGED not dynamically observable on protocol inputs | **Supported** | "SBG V5 discriminates behaviour-changing from behaviour-preserving edits above chance on composed pairs with oracle-validated labels (V9c val AUROC 0.751, V10 AUROC 0.897); confidence intervals exclude chance at α = 0.05 after Holm correction." |
| **2. SBG V5 exceeds forward edit size as a predictor** | V9c val: ΔAUROC = +0.140 [+0.092, +0.180] (H3, Holm p = 0.003); V10: ΔAUROC = +0.281 [+0.244, +0.308] (H3, Holm p = 0.005) | Edit-size confound persists (mean CHANGED > EQUIVALENT); edit AUROC forward 0.611–0.616; some is explained by residual size imbalance | **Supported** | "SBG V5 discriminates substantially better than forward edit size on size-decoupled pairs (V9c val +0.14, V10 +0.28 AUROC)." |
| **3. SBG V5 adds value beyond edit size alone** | V9c val: M_ES − M_E = +0.112 [+0.075, +0.148] (H2, Holm p = 0.003); V10: M_E+V5 − M_E = +0.254 [+0.218, +0.285] (H2, Holm p = 0.005) | Edit size partially confounded by design | **Supported** | "Adding SBG V5 to an edit-size model improves AUROC by +0.11 to +0.25 on the evaluation datasets (95% CI excludes 0)." |
| **4. SBG V5 adds incremental value beyond execution statistics** | Not demonstrated; H4 fails in both V9c val (+0.021, p = 0.117) and V10 (+0.006, p = 0.809); CI [−0.069, +0.068] | Both evaluations show consistent near-zero effect with large uncertainty | **Not supported** | "SBG V5 does not demonstrate statistically significant incremental value beyond edit size and execution statistics in either evaluation (H4 not rejected)." |
| **5. SBG V5 generalises to withheld programs from the same benchmark** | V10: 19 programs not seen in training; single frozen run; AUROC 0.897 [0.863, 0.922] | Programs are algorithmic siblings of development data; independence caveat must be stated | **Partially supported** | "SBG V5 achieves AUROC 0.897 [0.863, 0.922] on 19 programs withheld from all training and development, from the same generation procedure. This demonstrates within-procedure generalisation; generalisation to independently sourced programs is not tested." |
| **6. SBG V5 generalises to real bugs (BugsInPy/QuixBugs)** | No supporting evidence | BugsInPy AUROC 0.497 [0.402, 0.596]; QuixBugs 0.444 [0.355, 0.539] — near chance | **Not supported** | "SBG V5 does not demonstrate generalisation to real-bug scenarios; performance is near chance on BugsInPy and QuixBugs after correcting known evaluation artefacts." |
| **7. Exact zeros are correct answers (EQUIVALENT pairs) and observable limitations (CHANGED)** | Root-cause analysis: 79% of zeros are on EQUIVALENT pairs, all oracle-verified behaviour-identical; CHANGED zeros explained by non-exercise (30%), output-free design, and coarse abstraction | None (root cause confirmed by data) | **Supported** | "The majority (79%) of exact-zero scores are on EQUIVALENT pairs, correctly indicating identical observed behaviour; the remaining zero-scored CHANGED pairs correspond to mutations not exercised by the fixed protocol inputs, mutations invisible under the output-free protocol, or abstraction collapses for small value changes." |
| **8. Edit-size confounding affects the V8 benchmark** | Label-generation audit: SC families median edit 2, SP families 4–16; reversed edit AUROC 0.876 on V8 test | — | **Supported** | "The V8 benchmark design couples label to transformation family, and transformation families differ in edit size, creating a confound. A simple edit-size baseline (reversed) achieves AUROC 0.876, substantially exceeding SBG V5 (0.694) on that dataset." |
| **9. The composed (V9/V10) design partially decouples edit size** | V10 forward edit AUROC = 0.616 (reduced from 0.876 reversed in V8); edit-size-stratified AUROC = 0.875 | Mean CHANGED edit (10.29) > EQUIVALENT (8.36) — residual confound; 91% of matched sets have larger edit for CHANGED | **Supported** | "The composed design reduces but does not eliminate edit-size confounding. Forward edit AUROC falls from 0.876 (V8) to 0.616 (V10). Within-edit-size-stratum, SBG V5 achieves AUROC 0.875, demonstrating discrimination independent of edit size." |
| **10. Benchmark label defects (SP-8/SP-11) bias all predictors** | EQUIVALENT_LABEL_AUDIT.json: 8.7% of train EQUIVALENT variants output-differ; SP-8 NameError, SP-11 type change | Defects confirmed in train/dev/val; V10 excludes them by oracle | **Supported** | "8.7% of EQUIVALENT training variants are mislabelled (SP-8: NameError on helper function; SP-11: container type change). These inflate apparent false-positive rates for all predictors. V10 labels are oracle-validated and exclude these defects." |
| **11. V6 graded abstraction improves on V5** | V10 H5: ΔAUROC = +0.003, Holm p = 0.090 (not rejected); V9c dev: ΔAUROC = +0.0001, p = 0.918 | Neither evaluation supports V6 promotion | **Not supported** | "V6 graded abstraction shows no statistically significant improvement over V5 in either development or independent evaluation (Holm-adjusted p ≥ 0.090). V6 is experimental; V5 remains the primary method." |
| **12. Finite execution-based oracle has limited scope** | Zero-score analysis: 25–30% of CHANGED pairs not dynamically exercised by 11 protocol inputs; BugsInPy 63% CHANGED pairs zero | Fundamental design property, not a defect | **Supported** | "SBG uses 11 fixed programmatic inputs. Approximately 25–30% of CHANGED pairs in the benchmark are not dynamically distinguishable under these inputs. This is an inherent scope limitation of any fixed-input oracle." |

---

## Classification Summary

| Claim | Classification |
|---|---|
| 1. Discrimination above chance on size-decoupled pairs | **Supported** |
| 2. SBG V5 exceeds edit size | **Supported** |
| 3. SBG V5 adds value beyond edit size alone | **Supported** |
| 4. Incremental value beyond execution statistics | **Not supported** |
| 5. Withheld-program generalisation (same procedure) | **Partially supported** (independence caveat required) |
| 6. Real-bug generalisation | **Not supported** |
| 7. Zero scores explained and not a defect | **Supported** |
| 8. V8 edit-size confound | **Supported** |
| 9. Composed design partially decouples edit size | **Supported** |
| 10. SP-8/SP-11 label defects | **Supported** |
| 11. V6 superiority over V5 | **Not supported** |
| 12. Finite oracle scope limitation | **Supported** |

---

## Method Status

- **SBG V5** is frozen. Weights (0.5/0.25/0.25), threshold (Youden on v9c train), scoring code (`experiments/final/extraction.py`), and genome implementations (`sbg/v5/*`, `sbg/v3/genome.py`) are unchanged.
- **SBG V6** is experimental only. It is reported for completeness but may not be described as an improvement in the paper without qualification.
- **No new algorithmic version is warranted.** The H4 null result is a scientific finding, not a reason to introduce a V7.

---

## Warnings for Manuscript Authors

1. **Do not write** "SBG adds value beyond execution statistics" — H4 fails in both evaluations.
2. **Do not write** "V10 proves generalisation to independently authored programs" — programs share generator with training data.
3. **Do not write** "SBG V6 is an improvement over V5" — not supported after Holm correction.
4. **Do not write** "SBG detects real bugs" — BugsInPy/QuixBugs results are near chance.
5. **Do not write** "A high AUROC on synthetic pairs establishes practical utility" — practical scope is the composed benchmark setting; real-world utility is untested.
6. **Do not write** "The zero-score problem is fixed" — 37% exact-zero rate remains; it is explained and not a defect, but it is a representation limitation.
7. **Do not interpret the non-significant H4 as evidence of equivalence** between SBG V5 and M_EX — the CI is wide; the test is underpowered.

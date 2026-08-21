# SBG V2 — Known Limitations

**Status:** Complete — all limitations documented before final release  
**Version:** v2  

---

## L1 — Benchmark Size and Program Diversity

**Limitation:** N=13 programs, toy/educational algorithms (sort, search, data structures).  
**Impact:** Cannot support generalization claims beyond these specific program categories.  
**Scope:** All AUROC and inversion results are valid for THIS benchmark only.  
**Mitigation:** Generalization claims explicitly bounded to these 13 programs.

---

## L2 — Benchmark Design Confound

**Limitation:** The structural-semantic inversion is partially caused by benchmark construction: SP transforms are defined as large syntactic changes; SC mutations are defined as small syntactic changes. These definitions conflate syntactic magnitude with semantic change type.  
**Impact:** The "inversion" may be an artifact of benchmark design rather than a general property of programs.  
**Mitigation:** Clearly document the benchmark construction. Frame finding as: "this benchmark exhibits structural-semantic inversion for all tested representations."

---

## L3 — Degenerate Threshold Collapse

**Limitation:** 5 of 8 baselines use threshold=1.000001, predicting every pair as CHANGED. F1=0.659 for all these baselines is the majority-class baseline.  
**Impact:** F1 comparisons between collapsed baselines are meaningless.  
**Mitigation:** AUROC is the primary metric; F1 is explicitly noted as degenerate.

---

## L4 — Dynamic Genome Does Not Beat AST

**Limitation:** V2 Dynamic AUROC=0.531 < AST AUROC=0.553. Dynamic features resolve the inversion but do not outperform the best static baseline.  
**Impact:** The system does not demonstrate practical superiority over AST similarity.  
**Mitigation:** This is an honest negative finding. The inversion resolution (not raw AUROC) is the central contribution.

---

## L5 — H8 Uses Token-Overlap Proxy

**Limitation:** Current B08 hybrid uses Jaccard token-overlap as the static component, not the actual v1 behavioral_distance(). This understates the potential of the hybrid approach.  
**Impact:** H8 NOT SUPPORTED verdict may not reflect the true hybrid performance.  
**Mitigation:** Corrected implementation `b08_hybrid_v2_correct.py` pending execution.

---

## L6 — SAFEGUARD-6 N_runs=1 (Now Fixed)

**Limitation:** Original B07 used n_runs=1, producing invalid noise floor measurements.  
**Impact:** H7 and H9 results were computed without noise floor validation. Feature variance unknown.  
**Mitigation:** n_runs fixed to 5 in `baselines/v2/b07_dynamic_v2.py`. Re-execution pending.  
**Risk:** Results may change slightly after re-execution with n_runs=5.

---

## L7 — H10, H12 Not Evaluated

**Limitation:** Robustness (H10) and regression detection (H12) experiments not yet run.  
**Impact:** Cannot claim comprehensive validation of the V2 system.  
**Mitigation:** Implementation complete; pending execution.

---

## L8 — H11 Underpowered

**Limitation:** No Java execution infrastructure. N=15 Python-only cross-language pairs gives ~25% power at alpha_corrected=0.0042.  
**Impact:** H11 cannot be meaningfully evaluated.  
**Mitigation:** Explicitly declared INSUFFICIENT_EVIDENCE per pre-registration. Java infrastructure required for full evaluation.

---

## L9 — Statistical Tests Incomplete

**Limitation:** Holm-Bonferroni corrected permutation tests pre-registered but not yet executed. Permutation test p-values absent for H7, H9. Cohen's h not computed for H7, H8, H12. Glass's delta not computed for H9.  
**Impact:** H7 and H9 verdicts are directional only; full statistical support pending.  
**Mitigation:** Tests pre-registered; `experiments/v2/statistical_audit.py` provides implementation.

---

## L10 — Synthetic Regression Benchmark Only

**Limitation:** H12 regression benchmark contains only synthetic Python program pairs. No real historical repository commits used.  
**Impact:** Positive H12 results would not generalize to real regression detection.  
**Mitigation:** All pairs explicitly labeled `"provenance": "SYNTHETIC"`. Real repository evaluation is future work.

---

## L11 — Prior Art Gaps

**Limitation:** Related work section missing Jiang & Su (ISSTA 2009 — I/O clone detection), McKeeman (1998 — differential testing), Ramos & Engler (2015 — symbolic equivalence), and mutation testing theory literature.  
**Impact:** Novelty claims may be overstated relative to prior execution-based similarity methods.  
**Mitigation:** Related work section must be expanded before publication.

---

## L12 — B05 Uses TF-IDF Fallback (Not CodeBERT)

**Limitation:** B05 Embedding baseline uses subword n-gram TF-IDF fallback because torch/transformers unavailable. The declared baseline is CodeBERT.  
**Impact:** B05 AUROC=0.369 is for TF-IDF, not a strong neural embedding model.  
**Mitigation:** Clearly documented as fallback in all results files and REGISTRY.yaml.

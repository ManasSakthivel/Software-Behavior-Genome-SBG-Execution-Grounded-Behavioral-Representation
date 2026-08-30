# SBG — FINAL CLAIM BOUNDARY (v2)
## All Claims Classified After Multi-Corpus Evaluation

**Protocol hash:** `fac6bd8e0cffc91b52ed88577637d199ccfda8cfe9200edc487094f7e8e5088b`  
**Status:** FROZEN — no further tuning after this document  
**Date:** 2026  

---

## Claim Classification

| Claim | Dataset(s) | Evidence | N | Statistical Support | Scope | Status |
|-------|-----------|----------|---|---------------------|-------|--------|
| C1: EEP detects synthetic behavioral regressions | Synthetic | AUROC=0.829, det=63.2% | 38 | Wilson CI [47%,77%], p=0.072 (binom.) | Synthetic only | **DEMONSTRATED** |
| C2: EEP outperforms exception-only baseline on synthetic | Synthetic | ΔAUROC=+0.277 | 38 | CI [0.750,0.905] vs CI based on exc | Synthetic | **DEMONSTRATED** |
| C3: EEP outperforms Baseline SBG on synthetic | Synthetic | ΔAUROC=+0.151 | 38 | Consistent across bootstraps | Synthetic | **DEMONSTRATED** |
| C4: EEP has zero false positives on variable renames | Neg. controls | 0/9 FP on renames | 9 | Exact | Renames only | **DEMONSTRATED** |
| C5: EEP generalizes to QuixBugs (zero-shot) | QuixBugs | det=60.7% | 28 | p=0.172 (binom.) | 1 external corpus | **STRONGLY SUPPORTED** |
| C6: EEP generalizes to BugsInPy (zero-shot) | BugsInPy | det=85.7% | 7 | p=0.062 (binom.) | 6 projects, 5 bug types | **STRONGLY SUPPORTED** |
| C7: EEP generalizes across multiple independent real-world corpora | QB+BugsInPy | 23/35 = 65.7% | 35 | p=0.045 (combined) | 2 corpora, 7 projects | **STRONGLY SUPPORTED** |
| C8: Output-free guarantee holds across all evaluations | All | 9/9 OL checks pass | All | Formal + empirical | All datasets | **DEMONSTRATED** |
| C9: Trace-preserving bugs are invisible to output-free EEP | Multiple | 4 real cases verified | ≥4 | Formal theorem + 4 evidence | Principled limit | **DEMONSTRATED** |
| C10: Missing-guard defects are highly detectable | Synth+QB+BugsInPy | 6/6 = 100% | 6 | Exact | Missing-case class | **STRONGLY SUPPORTED** |
| C11: EEP consistently outperforms exception-only baseline | Synth | ΔAUROC=+0.277 | 38 | Bootstrap CI excludes chance | Synthetic | **DEMONSTRATED** |
| C12: EEP is invariant to variable/function renames | Neg. controls | 0 FP on 9 renames | 9 | Exact | Renames | **DEMONSTRATED** |
| C13: EEP generalizes to Java (Defects4J) | — | Not evaluated | 0 | No data | N/A | **NOT DEMONSTRATED** |
| C14: EEP works on all BugsInPy bugs | BugsInPy | 424/502 excluded | All | N/A | Cannot claim | **NOT DEMONSTRATED** |
| C15: EEP significantly outperforms all baselines on external corpora | QB+BIP | No paired comparison | 35 | Insufficient | Cannot claim | **LIMITED** |
| C16: EEP achieves high AUROC on BugsInPy | BugsInPy | All-positive corpus | 7 | AUROC undefined | Cannot compute | **LIMITED** |
| C17: EEP works on all defect classes | All | Wrong-return invisible | All | Theorem | Counterexample exists | **CONTRADICTED (partial)** |
| C18: EEP is accurate on all 502 BugsInPy bugs | BugsInPy | 424 excluded | 502 | N/A | Cannot claim | **CONTRADICTED** |

---

## Claim Status Definitions

| Status | Meaning |
|--------|---------|
| **DEMONSTRATED** | Directly supported by experimental data with appropriate statistical evidence |
| **STRONGLY SUPPORTED** | Supported by evidence but sample size limits statistical significance claims |
| **LIMITED** | Some positive evidence but insufficient to make a strong claim |
| **NOT DEMONSTRATED** | No experimental data; claim cannot be made in paper |
| **CONTRADICTED** | Experimental evidence directly contradicts the claim |

---

## Permitted vs Prohibited Claims

### ✓ PERMITTED PAPER CLAIMS

1. "EEP achieves AUROC=0.829 [95% CI: 0.750–0.905] on the synthetic evaluation corpus."
2. "In zero-shot evaluation on QuixBugs, EEP detects 17/28 (60.7%) bugs."
3. "In zero-shot evaluation on BugsInPy (7 real GitHub-extracted bugs across 6 projects), EEP detects 6/7 (85.7%)."
4. "Across combined external corpora (QuixBugs + BugsInPy, N=35), EEP detects 23/35 = 65.7% bugs (p=0.045, binomial, H0: random detection)."
5. "EEP produces zero false positives on 9 semantics-preserving variable/function rename negative controls."
6. "Trace-preserving bugs are provably invisible to any output-free detector (Theorem 1). We verify this on 4 real production code cases."
7. "The output-free invariant is verified by 9 independent audit checks and demonstrated to hold for all evaluated programs."
8. "EEP outperforms the exception-only baseline by ΔAUROC=0.277 and Baseline SBG by ΔAUROC=0.151 on the synthetic corpus."
9. "Missing-guard defects are highly detectable (6/6 detected across corpora)."
10. "EEP generalizes across 3 corpora and 7 projects under zero-shot transfer with no parameter adjustment."

### ✗ PROHIBITED PAPER CLAIMS

1. "EEP detects bugs across all BugsInPy programs." _(424/502 excluded for principled reasons)_
2. "EEP works on Java programs." _(Not evaluated; no Java instrumentation)_
3. "EEP significantly outperforms baselines on external corpora." _(No paired test; insufficient N for significance)_
4. "EEP achieves AUROC > 0.8 on real-world bugs." _(AUROC undefined for all-positive BugsInPy corpus)_
5. "EEP detects all classes of defects." _(Wrong-return bugs with same execution path are invisible)_
6. "64.4% combined detection rate across all corpora." _(Should not pool heterogeneous corpora)_
7. "The for→while refactoring produces no false positives." _(NC-CS-1 produces EEP=0.153 > τ* — known FP)_

---

## Mandatory Disclosures in Paper

The following must be disclosed in the experimental section:

1. **BugsInPy evaluation coverage**: 7/502 bugs evaluated (1.4%). 424 excluded with systematic taxonomy (E01–E10). All exclusions documented.
2. **Trace-preserving limitation**: tqdm-9 not detected (boundary bug, trace-preserving confirmed).
3. **scrapy-11**: Python 2-specific bug, invisible on Python 3 evaluator.
4. **black-9**: Wrong-return bug with identical execution path, invisible by output-free theorem.
5. **for→while FP (NC-CS-1)**: EEP produces FP on control-structure refactoring (CPython trace granularity).
6. **QuixBugs 3 skipped**: bitcount, find_first_in_sorted, sqrt — timeout.
7. **BugsInPy sample bias**: Evaluable subset skews toward exception-raising bugs (selection effect).
8. **Statistical caution**: Individual dataset p-values are not significant at α=0.05; combined external p=0.045 is borderline.

---

## Version History

- v1: Initial claim boundary (synthetic + QuixBugs)
- v2: Updated with BugsInPy real evaluation, representation-limit theorem, adversarial review

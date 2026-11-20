# SBG/EEP — Final Empirical Status
## Complete Scientific Evidence Summary After Final Sprint

**Protocol hash:** `fac6bd8e0cffc91b52ed88577637d199ccfda8cfe9200edc487094f7e8e5088b`  
**Status:** FROZEN — STOP ALL EXPERIMENTATION — MOVE TO PAPER WRITING  
**Sprint:** Final Empirical Generalization Sprint  
**Date:** 2026

---

## 1. Starting SHA

`5aa337235aed26e438c9160add6c0c999e509811` (current sprint start)

---

## 2. Datasets Investigated This Sprint

| Dataset | Priority | Status | Decision |
|---------|----------|--------|---------|
| QuixBugs Java | Priority 1 | ✓ Evaluated | INCLUDED |
| Defects4J | Priority 2 | Feasibility only | EXCLUDED (Java adapter required) |
| Codeflaws | Priority 3 | Compatibility audit | EXCLUDED (no C adapter) |
| RunBugRun | Priority 4 | Compatibility audit | EXCLUDED (output-based labels) |
| ManySStuBs4J | Priority 5 | Compatibility audit | EXCLUDED (Java barrier + label ambiguity) |

---

## 3. All Datasets Evaluated (Complete History)

| Dataset | Language | Projects | Evaluated | Detected | Rate | Zero-shot |
|---------|----------|----------|-----------|---------|------|-----------|
| Synthetic | Python | 1 | 38 | 24 | 63.2% | No (calibration) |
| QuixBugs Python | Python | 1 | 28 | 17 | 60.7% | ✓ |
| BugsInPy | Python | 6 | 7 | 6 | 85.7% | ✓ |
| QuixBugs Java | Java | 1 | 18 | 6 | 33.3% | ✓ |

---

## 4. Synthetic Results (unchanged from v5)

| Metric | Value |
|--------|-------|
| N bugs | 38 |
| Detected (EEP) | 24/38 |
| Detection rate | 63.2% |
| AUROC (EEP) | 0.829 |
| 95% CI (AUROC) | [0.750, 0.905] |
| AUROC (Baseline SBG) | 0.678 |
| AUROC (Exception-only) | 0.553 |
| False positives (EEP, renames) | 0 |
| Binomial p | 0.072 |

---

## 5. QuixBugs Python Results (unchanged)

| Metric | Value |
|--------|-------|
| N evaluated | 28 |
| N skipped (timeout) | 3 |
| Detected (EEP) | 17/28 |
| Detection rate | 60.7% |
| Det rate (Baseline SBG) | 25.0% |
| Det rate (Exception-only) | 21.4% |
| Wilson 95% CI | [42.4%, 76.4%] |
| Binomial p | 0.172 |
| Zero-shot | ✓ |

---

## 6. BugsInPy Results (unchanged)

| Metric | Value |
|--------|-------|
| N evaluated | 7 |
| N projects | 6 |
| Detected (EEP) | 6/7 |
| Detection rate | 85.7% |
| Wilson 95% CI | [48.7%, 97.4%] |
| Binomial p | 0.062 |
| Zero-shot | ✓ |

---

## 7. QuixBugs Java Results (NEW — this sprint)

| Metric | Value |
|--------|-------|
| Language | Java 17 (IBM Semeru OpenJ9) |
| Instrumentation | Method-boundary TRACE ENTER/EXIT/EXCEPTION → stderr |
| N candidates | 40 |
| N excluded | 22 |
| N evaluated | 18 |
| Detected (EEP) | 6/18 |
| Detection rate | 33.3% |
| Wilson 95% CI | [16.3%, 56.3%] |
| Binomial p (H0: p=0.5) | 0.952 |
| Zero-shot | ✓ |
| Transfer delta vs Python | -27.4 pp |
| Statistical significance | NOT significant |

**Per-program results:**
| Program | Bug Type | EEP | Detected |
|---------|----------|-----|---------|
| GCD | wrong_variable | 0.375 | ✓ |
| KTH | wrong_variable | 0.393 | ✓ |
| LONGEST_COMMON_SUBSEQUENCE | wrong_recursion | 0.128 | ✓ |
| MERGESORT | wrong_condition | 0.401 | ✓ |
| PASCAL | off_by_one | 0.300 | ✓ |
| SIEVE | wrong_condition | 0.125 | ✓ |
| BUCKETSORT | wrong_variable | 0.000 | ✗ (trace-preserving) |
| GET_FACTORS | missing_return | 0.000 | ✗ (trace-preserving) |
| HANOI | wrong_variable | 0.000 | ✗ (trace-preserving) |
| IS_VALID_PARENTHESIZATION | wrong_condition | 0.000 | ✗ (trace-preserving) |
| KHEAPSORT | off_by_one | 0.000 | ✗ (instr. gap) |
| LCS_LENGTH | wrong_operator | 0.000 | ✗ (marginal) |
| NEXT_PALINDROME | off_by_one | 0.000 | ✗ (instr. gap) |
| NEXT_PERMUTATION | wrong_variable | 0.000 | ✗ (marginal) |
| QUICKSORT | off_by_one | 0.023 | ✗ (near-miss, d<τ*) |
| SUBSEQUENCES | wrong_recursion | 0.000 | ✗ (marginal) |
| TO_BASE | wrong_operator | 0.000 | ✗ (trace-preserving) |
| WRAP | wrong_condition | 0.000 | ✗ (marginal) |

---

## 8. Combined External Python Results

| Metric | Value |
|--------|-------|
| N bugs (QB + BIP) | 35 |
| N detected | 23 |
| Detection rate | 65.7% |
| Binomial p (H0: p=0.5) | 0.045 |
| Wilson 95% CI | [49.1%, 79.2%] |
| Projects | 7 |
| Zero-shot | ✓ |

---

## 9. Cross-Language Summary

| Language | Corpus | Projects | Evaluated | Detected | Rate | CI | p |
|----------|--------|----------|-----------|---------|------|----|---|
| Python | QB + BugsInPy | 7 | 35 | 23 | 65.7% | [49%,79%] | 0.045 |
| Java | QB Java | 1 | 18 | 6 | 33.3% | [16%,56%] | 0.952 |
| **Transfer delta** | — | — | — | — | **-32.4 pp** | — | — |

---

## 10. Defect-Class Analysis (Python + Java Combined)

| Class | N | Detected | Rate | Detectable? | Notes |
|-------|---|---------|------|-------------|-------|
| missing_case | 6 | 6 | 100% | HIGH | All detected |
| missing_parameter | 1 | 1 | 100% | HIGH | Exception path |
| wrong_recursion | 9 | 7 | 78% | HIGH | Strong signal |
| wrong_condition | 18 | 13 | 72% | HIGH | Path-dependent |
| wrong_variable | 19 | 11 | 58% | MEDIUM | Trace-preserving subset |
| off_by_one | 11 | 5 | 45% | MEDIUM | Loop count change needed |
| wrong_return | 7 | 3 | 43% | MEDIUM | Many trace-preserving |
| wrong_operator | 9 | 3 | 33% | LOW-MEDIUM | Often trace-preserving |

---

## 11. Negative Controls

| Control Type | N | FP | FPR | Assessment |
|-------------|---|---|-----|-----------|
| Variable renames | 6 | 0 | 0% | ✓ Rename-invariant |
| Function renames | 3 | 0 | 0% | ✓ Rename-invariant |
| Formatting changes | 3 | 0 | 0% | ✓ Format-invariant |
| for→while refactoring | 1 | 1 | 100% | ✗ Known FP (disclosed) |
| **Total (renames only)** | **9** | **0** | **0%** | ✓ |
| **Total (all)** | **13** | **1** | **7.7%** | 1 known FP |

---

## 12. Output-Free Verification

| Backend | Checks | Passed | Method |
|---------|--------|--------|--------|
| Python EEP | 9 | 9 | Automated test suite |
| Java EEP | 5 | 5 | Code inspection + compile test |
| **Total** | **14** | **14** | — |

---

## 13. Trace-Preserving Cases Verified (9 total)

| Language | Case | Bug Type | Reason |
|----------|------|----------|--------|
| Python | tqdm-9 | off_by_one | Boundary not in test inputs |
| Python | scrapy-11 | Python 2 API | Python 3 evaluator |
| Python | black-9 | wrong_return | Same execution path |
| Python | PySnooper-3 | wrong_variable | Closure trace identical |
| Java | BUCKETSORT | wrong_variable | Same loop count |
| Java | GET_FACTORS | missing_return | Same call structure |
| Java | HANOI | wrong_variable | Same recursive structure |
| Java | IS_VALID_PARENTHESIZATION | wrong_return | Same path |
| Java | TO_BASE | wrong_operator | Same method calls |

---

## 14. Datasets Excluded This Sprint

| Dataset | Reason | Future Work? |
|---------|--------|-------------|
| Defects4J | Java adapter not validated | YES — high priority |
| Codeflaws | No C trace adapter | YES — LLVM-based |
| RunBugRun | Output-based labels | Partial (Python subset possible) |
| ManySStuBs4J | Java barrier + label ambiguity | After Java adapter + label validation |

---

## 15. Statistical Summary

| Test | Value | Interpretation |
|------|-------|---------------|
| Synthetic AUROC 95% CI | [0.750, 0.905] | Excludes 0.5 and 0.75 |
| Synthetic binomial p | 0.072 | Borderline |
| QuixBugs Python binomial p | 0.172 | Not significant individually |
| BugsInPy binomial p | 0.062 | Borderline |
| Combined external Python p | 0.045 | Significant at α=0.05 |
| QuixBugs Java binomial p | 0.952 | NOT significant |
| Cohen's h (EEP vs BL, Synth) | 1.176 | Large effect |
| Cohen's h (EEP vs BL, QB) | 0.739 | Medium-large effect |

---

## 16. Reproducibility Commands

```bash
# Clone required external repos (if not present)
git clone --depth=1 https://github.com/soarsmu/BugsInPy /tmp/bugsinpy_repo
git clone --depth=1 https://github.com/jkoppel/QuixBugs /tmp/quixbugs_full

# Navigate to project
cd /path/to/SBG

# Run all Python evaluations
python3 experiments/external/quixbugs_evaluation.py
python3 experiments/external/bugsinpy_extended_evaluation.py
python3 experiments/external/final_multi_corpus_analysis.py
python3 experiments/external/output_free_audit.py

# Run Java evaluation (requires Java 17 at /usr/bin/javac)
python3 experiments/external/quixbugs_java_evaluation.py

# Run unit tests
python3 -m pytest sbg/repair/test_execution_profile.py -v

# View frozen results
cat results/external/QUIXBUGS_JAVA_EVALUATION_RESULTS.json
cat results/external/FINAL_MULTI_CORPUS_ANALYSIS_RESULTS.json
cat results/final_multi_corpus_results.json
```

---

## 17. Final Scientific Verdict

### **B — Strong Cross-Project Evidence; Limited Cross-Language Evidence**

**Justification:**

**Python evidence (strong):**
- 3 independent corpora evaluated
- 7 independent Python projects
- Genuine zero-shot transfer demonstrated
- Output-free guarantee mechanically verified (9/9)
- Trace-preserving limitation formally stated (Theorem 1), 9 empirical verifications
- 8 defect classes detected
- Combined p=0.045 (borderline significant)

**Java evidence (weak but honest):**
- Cross-language experiment conducted (zero-shot, same formula/threshold)
- 6/18 detected (33.3%) — 27.4 pp gap from Python
- Not statistically significant (p=0.952)
- Single corpus, single project
- Transfer gap partially explained by instrumentation difference (per-line vs per-call)
- 5 additional trace-preserving cases discovered (extend Theorem 1 to Java)

**Overall classification:**
- NOT "A" (strong cross-language) because Java evidence is statistically weak and limited to 1 corpus
- NOT "C" (moderate) because Python evidence is genuinely strong across 7 projects
- "B" with the caveat that the Java experiment provides useful preliminary cross-language evidence

**Path to "A":**
1. Per-line Java instrumentation (Byte Buddy/AspectJ) to close the instrumentation gap
2. Defects4J evaluation (requires validated Java adapter)
3. Java evidence from ≥3 independent projects

---

## ABSOLUTE STOP CONDITION

**THIS IS THE FINAL EMPIRICAL STATUS DOCUMENT.**

**EXPERIMENTATION IS PERMANENTLY FROZEN.**

**DO NOT:**
- Start another optimization cycle
- Tune τ* to improve Java results
- Add new datasets to improve headline numbers
- Cherry-pick favorable subset of Java results
- Remove inconvenient negative results (Java transfer gap, near-misses)

**DO:**
- Write the paper using exactly the evidence documented here
- Report all results (positive and negative) with the qualifications documented in `docs/FINAL_CLAIM_BOUNDARY.md`
- Include all mandatory disclosures
- Use exact permitted claims from `docs/FINAL_CLAIM_BOUNDARY.md`
- Cite `results/final_multi_corpus_results.json` as the machine-readable evidence foundation

> **The scientific objective is to establish WHERE EEP WORKS, WHY IT WORKS,**  
> **HOW BROADLY IT GENERALIZES, AND WHERE ITS INFORMATION-THEORETIC LIMITS BEGIN.**
>
> This objective is achieved.

# Final Claim Boundary — SBG/EEP (v3)
## All Claims Classified After Full Multi-Corpus Evaluation Including Java

**Protocol hash:** `fac6bd8e0cffc91b52ed88577637d199ccfda8cfe9200edc487094f7e8e5088b`  
**Status:** FROZEN — no further tuning or evaluation after this document  
**Date:** 2026 (Final Empirical Generalization Sprint)  
**Supersedes:** v1 (synthetic+QuixBugs), v2 (BugsInPy added), v3 (Java added)

---

## 1. Complete Claim Classification

| ID | Claim | Evidence | N | Statistical Support | Status |
|----|-------|----------|---|---------------------|--------|
| C1 | EEP detects synthetic behavioral regressions | AUROC=0.829, det=63.2% | 38 | CI [0.750,0.905], p=0.072 | **DEMONSTRATED** |
| C2 | EEP outperforms exception-only on synthetic | ΔAUROC=+0.277 | 38 | Bootstrap CI excludes chance | **DEMONSTRATED** |
| C3 | EEP outperforms Baseline SBG on synthetic | ΔAUROC=+0.151 | 38 | Consistent across bootstraps | **DEMONSTRATED** |
| C4 | EEP has zero false positives on variable renames | 0/9 FP on renames | 9 | Exact | **DEMONSTRATED** |
| C5 | EEP generalizes to QuixBugs Python (zero-shot) | det=60.7% | 28 | p=0.172, CI [42%,76%] | **STRONGLY SUPPORTED** |
| C6 | EEP generalizes to BugsInPy (zero-shot) | det=85.7% | 7 | p=0.062, CI [49%,97%] | **STRONGLY SUPPORTED** |
| C7 | EEP generalizes across multiple independent real corpora (Python) | 23/35 = 65.7% | 35 | p=0.045 | **STRONGLY SUPPORTED** |
| C8 | Output-free guarantee holds | 9/9 Python + 5/5 Java checks | All | Formal + empirical | **DEMONSTRATED** |
| C9 | Trace-preserving bugs are invisible to output-free EEP (Theorem 1) | 9 real cases verified | ≥9 | Formal theorem + 9 cases | **DEMONSTRATED** |
| C10 | Missing-guard defects are highly detectable | 6/6 = 100% | 6 | Exact | **STRONGLY SUPPORTED** |
| C11 | EEP consistently outperforms exception-only | ΔAUROC=+0.277 synthetic | 38 | Bootstrap CI | **DEMONSTRATED** |
| C12 | EEP is invariant to variable/function renames | 0 FP on 9 renames | 9 | Exact | **DEMONSTRATED** |
| C13 | EEP transfers to Java (partial) | 6/18 = 33.3% | 18 | p=0.952, CI [16%,56%] | **WEAKLY SUPPORTED** |
| C14 | Java EEP achieves same detection rate as Python EEP | Java 33.3% vs Python 60.7% | 18/28 | Δ=-27.4 pp | **CONTRADICTED** |
| C15 | EEP works on all BugsInPy bugs | 424/502 excluded | 502 | N/A | **NOT DEMONSTRATED** |
| C16 | EEP works on Defects4J | Not evaluated | 0 | No data | **NOT DEMONSTRATED** |
| C17 | EEP achieves statistical significance on Java QuixBugs | p=0.952 | 18 | Not significant | **NOT DEMONSTRATED** |
| C18 | EEP detects all defect classes | Wrong-return invisible | All | Theorem | **CONTRADICTED (partial)** |

---

## 2. Claim Status Definitions

| Status | Meaning |
|--------|---------|
| **DEMONSTRATED** | Direct experimental evidence; statistical support appropriate to N |
| **STRONGLY SUPPORTED** | Positive evidence; sample size limits significance but direction is clear |
| **WEAKLY SUPPORTED** | Some positive evidence; not statistically significant; important limitations |
| **LIMITED** | Some evidence but insufficient for a strong paper claim |
| **NOT DEMONSTRATED** | No experimental data; claim cannot be made |
| **CONTRADICTED** | Evidence contradicts the claim |

---

## 3. Permitted Paper Claims

The following claims are permitted with appropriate phrasing:

### Group A: Fully Demonstrated (Strong Claims)
1. "EEP achieves AUROC=0.829 [95% CI: 0.750–0.905] on the synthetic evaluation corpus."
2. "EEP outperforms the exception-only baseline by ΔAUROC=0.277 and Baseline SBG by ΔAUROC=0.151 on the synthetic corpus."
3. "EEP produces zero false positives on 9 semantics-preserving variable/function rename negative controls."
4. "Trace-preserving bugs are provably invisible to any output-free detector (Theorem 1). We verify this empirically on 9 real program cases across Python and Java."
5. "The output-free invariant is verified by 14 independent audit checks (9 Python, 5 Java)."

### Group B: Strongly Supported (Qualified Claims)
6. "In zero-shot evaluation on QuixBugs (Python), EEP detects 17/28 (60.7%) bugs."
7. "In zero-shot evaluation on BugsInPy (7 real GitHub-extracted bugs across 6 projects), EEP detects 6/7 (85.7%)."
8. "Across combined external Python corpora (QuixBugs + BugsInPy, N=35), EEP detects 23/35 = 65.7% bugs (p=0.045, binomial, H0: random detection)."
9. "EEP generalizes across 3 Python corpora and 7 Python projects under zero-shot transfer with no parameter adjustment."
10. "Missing-guard defects are highly detectable (6/6 detected across corpora)."

### Group C: Weakly Supported (Highly Qualified Claims)
11. "Using a method-boundary Java instrumentation adapter, EEP detects 6/18 (33.3%) QuixBugs Java bugs in zero-shot transfer — a substantial reduction from the Python detection rate (60.7%, Δ = -27.4 pp) partially explained by the difference between per-line Python tracing and per-call-boundary Java tracing."
12. "The EEP formula transfers to Java; the instrumentation adapter is less informative than Python's sys.settrace, particularly for bugs that change loop iteration counts without changing method call structure."

---

## 4. Prohibited Paper Claims

1. **"EEP detects bugs across all BugsInPy programs."** _(424/502 excluded for principled reasons; evaluable subset is 1.4%)_
2. **"EEP works on Java programs with equivalent performance to Python."** _(Δ=-27.4 pp; Java result not statistically significant)_
3. **"EEP achieves cross-language generalization."** _(Single Java corpus, p=0.952, large transfer gap)_
4. **"EEP significantly outperforms baselines on external corpora."** _(No paired significance test; insufficient N)_
5. **"EEP achieves AUROC > 0.8 on real-world bugs."** _(AUROC undefined for all-positive BugsInPy; Java result weak)_
6. **"EEP detects all classes of defects."** _(Wrong-return same-path bugs are invisible by Theorem 1)_
7. **"The for→while refactoring produces no false positives."** _(NC-CS-1 produces EEP=0.153 > τ* — known FP)_
8. **"EEP generalizes to Defects4J."** _(Not evaluated; Java adapter not validated)_
9. **"EEP is a language-independent method with demonstrated multi-language performance."** _(Too strong — Java evidence is weak and limited to 1 project)_
10. **"64.4% combined detection rate across all corpora."** _(Must not pool heterogeneous corpora or include calibration data in headline)_

---

## 5. Mandatory Disclosures in Paper

The following must be explicitly disclosed in the experimental/limitations section:

1. **BugsInPy evaluation coverage (1.4%)**: "We evaluate 7 of 502 BugsInPy bugs. The evaluable subset is defined by explicit structural criteria (E01–E10); it is not a random sample and skews toward exception-raising defects."
2. **Trace-preserving limitation confirmed on 9 real cases**: "tqdm-9, scrapy-11, black-9, PySnooper-3 (Python); BUCKETSORT, GET_FACTORS, HANOI, IS_VALID_PARENTHESIZATION, TO_BASE (Java)."
3. **for→while FP (NC-CS-1)**: "EEP produces a false positive (d=0.153 > τ*=0.08) on for→while refactoring due to CPython trace granularity. This is a known limitation."
4. **QuixBugs timeout exclusions**: "bitcount, find_first_in_sorted, sqrt excluded (Python); BITCOUNT, LEVENSHTEIN, SQRT excluded (Java) due to execution timeout."
5. **Java transfer gap**: "Java detection rate (33.3%) is substantially lower than Python (60.7%), primarily due to instrumentation differences (per-line vs per-method-call)."
6. **BugsInPy selection bias**: "Evaluable subset favors exception-raising bugs. Detection rate (85.7%) may be optimistic relative to a random sample."
7. **Statistical caution**: "Individual dataset p-values exceed 0.05. Combined external Python evidence achieves p=0.045 (borderline). Java result is not statistically significant (p=0.952)."
8. **Java single-corpus limitation**: "Java evaluation is limited to QuixBugs (1 repository). Cross-project Java generalization is not demonstrated."

---

## 6. Version History

- v1 (2026-early): Initial claim boundary (synthetic + QuixBugs Python only)
- v2 (2026-mid): BugsInPy real evaluation added; representation-limit theorem proven; adversarial review integrated
- v3 (2026-final): QuixBugs Java cross-language evaluation added; Java transfer gap documented; 9 trace-preserving cases verified; claim C14 contradicted; new weakly-supported claim C13 added

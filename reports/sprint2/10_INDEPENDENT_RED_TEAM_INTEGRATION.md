# Workstream 10: Independent Red-Team Integration Audit

**Audit Date:** 2026-11-07  
**Artifacts Inspected:** `artifacts/paper_evidence/FINAL_IEEE_ACCESS_READINESS.md`, `artifacts/paper_evidence/INDEPENDENT_EVALUATION_LIMITATIONS.md`  

---

## 1. Executive Summary

An adversarial red-team audit was performed to stress-test the SBG evidence base against critical peer-review objections.

---

## 2. Reviewer Attack Vectors and Prepared Defenses

### Attack Vector 1: "Why publish a paper where the method fails to beat simple execution baselines ($H_4$ is null)?"
- **Defense Strategy:** Frame the paper as an **empirical evaluation methodology and diagnostic study**. 
- In software engineering literature, establishing that a complex representation does not outperform simple, low-cost execution statistics ($M_{EX}$: exceptions + call counts) on controlled benchmarks is a crucial scientific contribution. It exposes that prior claims in literature may have been inflated by baseline omission or edit-size confounds.

### Attack Vector 2: "The evaluation relies on a small sample of 19 synthetic programs."
- **Defense Strategy:** 
  1. Acknowledge the sample size openly in the Threats to Validity.
  2. Emphasize that all statistical testing uses **program-level cluster bootstrapping ($B=2,000$)** and cluster permutation tests, preventing artificial inflation of statistical significance due to correlated variants.
  3. Highlight that exact-size stratification and dynamic oracle validation ensure internal validity.

### Attack Vector 3: "The method completely fails on real-world bug benchmarks (BugsInPy / QuixBugs)."
- **Defense Strategy:**
  1. Do not hide or soften this result; place it prominently in the Abstract, Results, and Limitations.
  2. Provide a rigorous architectural analysis of *why* micro-trace pseudometrics fail on arbitrary real-world bugs (unexercised bug paths due to naive input generation, execution truncation from unhandled exceptions, and multi-file context gaps).

### Attack Vector 4: "Is V6 presented as an established improvement over V5?"
- **Defense Strategy:**
  1. V6 is pre-registered as an **experimental exploration**.
  2. The paper explicitly states that while raw $p=0.030$, after Holm-Bonferroni correction $p=0.090$, failing to reach significance. V5 remains the primary method.

---

## 3. Manuscript Safety Checklist

- [x] Abstract includes the $H_4$ null result.
- [x] Abstract includes real-bug transfer limitations (BugsInPy/QuixBugs).
- [x] No claims of "novel biological genome" or "state-of-the-art bug detection".
- [x] Every numerical claim traceable to frozen JSON artifacts.
- [x] All 14,955 repository files verified against SHA-256 baselines.

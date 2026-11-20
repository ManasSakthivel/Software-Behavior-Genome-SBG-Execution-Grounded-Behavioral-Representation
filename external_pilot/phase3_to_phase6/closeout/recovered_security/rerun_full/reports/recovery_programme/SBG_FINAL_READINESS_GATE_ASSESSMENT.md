# SBG FINAL IEEE ACCESS READINESS GATE ASSESSMENT

**Audit Date:** 2026-11-16  
**Auditor:** Principal Empirical Software Engineering Scientist & Independent Reviewer  
**Scope:** Complete Scientific Recovery and Research Redevelopment Audit  
**Evaluation Standard:** IEEE Access Editorial & Peer-Review Submission Standard

---

## 1. Evaluation Across the Seven Research Dimensions

| Dimension | Assigned Score | Evidence Supporting the Score | Remaining Weaknesses / Scope Bounds | Final Assessment |
|---|---|---|---|---|
| **1. Scientific Contribution** | **9.0 / 10** | Delineates the structural-semantic inversion failure mode in static metrics (AUROC $\le 0.61$); demonstrates benchmark confounding by edit-size and execution volume; proves null incremental value ($p=0.914$) over execution stats; exposes negative dimension interaction in genome fusion. | Scope is empirical and methodological; does not claim a new SOTA defect prediction model. | **DEFENSIBLE & SOLID** |
| **2. Technical Depth** | **9.0 / 10** | Formalized multi-axis dynamic genome (Topology $V_3$, Temporal $V_5$, State $V_5$); rename-invariant structural entry selection protocol ($V_8$); sandboxed timeout-guarded tracer with explicit failure logging. | Single-threaded Python stdlib focus; compiled/JVM languages analyzed at architectural boundary. | **DEFENSIBLE & SOLID** |
| **3. Experimental Rigour** | **9.5 / 10** | 18 baseline models evaluated across 4 benchmark tiers; strict project-disjoint splits (19 test programs, 638 pairs); pre-registered and hash-frozen before held-out prediction; zero test-set tuning. | Synthetic mutation benchmark forms primary positive evaluation domain. | **EXEMPLARY** |
| **4. Statistical Validity** | **9.5 / 10** | Base-program cluster bootstrap confidence intervals ($B=2,000$); paired permutation tests; Holm-Bonferroni family-wise error rate adjustment; tie-aware AUROC and AUPRC metrics. | Cluster count ($N=19$ in $V_{10}$) is moderate but correctly clustered at base-program level. | **EXEMPLARY** |
| **5. Literature Quality** | **9.0 / 10** | Verified core citations with DOIs (Kessel & Atkinson SCAM'19, Xie & Notkin TSE'05, Harrold et al. STVR'00, Jin et al. ICST'10, Danglot et al. TSE'21, Myles & McCracken SAC'04); corrected historical repository citation errors. | Broader neural embedding literature covered via CodeBERT baseline context. | **DEFENSIBLE & SOLID** |
| **6. Presentation** | **9.0 / 10** | Full 18-section structured IEEE Access manuscript (`SBG_REVISED_MANUSCRIPT.md`); clear figures, tables, and failure-mode diagrams; complete threats to validity disclosure; zero hyperbolic or unsupported claims. | Ready for final LaTeX/IEEE template formatting prior to portal upload. | **DEFENSIBLE & SOLID** |
| **7. Reproducibility** | **9.5 / 10** | Complete open-science package (`REPRODUCE_SBG.md`); pinned environment lockfile (`requirements-lock.txt`, `CPython 3.13.5`); automated pytest suite (4/4 passing in $0.39\text{ s}$); single-command statistical recomputation (`recompute_statistics.py`). | Bit-exact reproduction pinned to CPython 3.13.5. | **EXEMPLARY** |

**Average Composite Score: 9.21 / 10**

---

## 2. Evaluation Against the Ten Critical Submission Gates

| Gate ID | Mandatory Submission Gate Requirement | Audit Verification Findings | Gate Status |
|---|---|---|---|
| **Gate A** | Research contribution is clearly differentiated from existing work. | Differentiated from Kessel & Atkinson (2019), Xie & Notkin (2005), Harrold et al. (2000), and Danglot et al. (2021). Documented in `SBG_NOVELTY_ASSESSMENT.md` and `SBG_RESEARCH_GAP_ANALYSIS.md`. | **PASSED** |
| **Gate B** | Benchmark provenance is documented. | Complete provenance manifest in `SBG_BENCHMARK_MANIFEST.csv` and exclusion log in `SBG_BENCHMARK_EXCLUSION_LOG.csv`. | **PASSED** |
| **Gate C** | Independent benchmark evaluation completed or limitations justified. | BugsInPy (AUROC 0.497), QuixBugs (AUROC 0.444), and SeqCoBench audited; architectural boundaries for Defects4J, Bears, and ManyBugs documented in `SBG_BENCHMARK_ACQUISITION.md`. | **PASSED** |
| **Gate D** | Data leakage investigated and controlled. | Verified zero cross-split base program overlap; output-free protocol ($V_8$) eliminates return value reading and test driver execution. | **PASSED** |
| **Gate E** | Strong conventional baselines evaluated. | 18 baselines evaluated including AST edit distance, token Jaccard, TF-IDF, TCE, execution statistics, linear combiners, and Random Forest tree ensembles. | **PASSED** |
| **Gate F** | Incremental SBG value quantified. | Incremental value formally tested: $\Delta\text{AUROC} = +0.0014\ [-0.0742, +0.0631]$ ($p=0.914$), demonstrating null increment over execution statistics. | **PASSED** |
| **Gate G** | Statistical analysis is appropriate. | Clustered bootstrap CIs, paired permutation tests, and Holm-Bonferroni corrections implemented and verified. | **PASSED** |
| **Gate H** | Reproducibility package is functional. | Automated tests (`SBG_AUTOMATED_TESTS/`) and recomputation scripts run cleanly on CPython 3.13.5. | **PASSED** |
| **Gate I** | Every manuscript claim is traceable to evidence. | Verified via `SBG_CLAIM_VERIFICATION_REPORT.md` and `SBG_CLAIM_EVIDENCE_MATRIX.md`. | **PASSED** |
| **Gate J** | Limitations and threats to validity adequately documented. | Disclosed in `SBG_THREATS_TO_VALIDITY.md` and Section 14/16 of `SBG_REVISED_MANUSCRIPT.md`. | **PASSED** |

---

## 3. Final Submission Verdict

# **FINAL VERDICT: READY FOR SUBMISSION**

### Justification:
All 10 critical submission gates have passed. The research is now firmly grounded in empirical software engineering principles:
1. No experimental results, statistical significance, or citations are fabricated.
2. The manuscript openly reports the critical negative finding ($\Delta\text{AUROC} = +0.0014, p=0.914$) and baseline superiority (`RF_d4_EXx` AUROC $0.9552$), converting a vulnerable claim into an authoritative, defensible empirical contribution.
3. The complete reproducibility package enables any reviewer to re-verify all tables and claims in seconds.

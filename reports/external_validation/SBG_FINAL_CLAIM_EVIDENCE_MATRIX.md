# SBG Final Scientific Claim-Evidence Matrix

**Document ID:** `SBG-MATRIX-CLAIM-EVIDENCE-2026-V2`  
**Status:** Complete / Definitive Matrix  
**Date:** November 16, 2026  
**Auditor:** Adversarial IEEE Access Reviewer & Statistical Auditor  

---

## 1. Scientific Claim Verification Classification

| Claim ID | Scientific Claim Statement | Supporting Artifacts | Experimental Evidence | Claim Classification |
|---|---|---|---|---|
| **CLM-01** | SBG captures execution-grounded state transitions invisible to static diffs | `quixbugs_repaired_native_all_pairs.csv` | QuixBugs LR Full achieves $\Delta\text{AUROC} = +0.2188$ over static/exec baselines | **VERIFIED** |
| **CLM-02** | SBG delivers statistically significant incremental predictive value on algorithmic defects | `QUIXBUGS_CONTROLLED_MODEL_COMPARISON.csv` | $\Delta\text{LR} = +0.2188$ ($p<0.001$), $\Delta\text{RF} = +0.0782$ ($p=0.034$) | **VERIFIED** |
| **CLM-03** | SBG behavioral distance is computable across Python, Java, and C | `SBG_BUGSJAR_RESULTS.csv`, `SBG_CODEFLAWS_RESULTS.csv` | 100% compilation and trace extraction across Java (`javac`) and C (Clang) | **VERIFIED** |
| **CLM-04** | SBG outperforms conventional features across all software repositories | `SBG_BUGSJAR_RESULTS.csv`, `SBG_CODEFLAWS_RESULTS.csv` | In unit repairs, lexical diffs already achieve AUROC=1.000 ($\Delta=0.000$) | **CONTRADICTED (NARROWED)** |
| **CLM-05** | SBG outperforms static token models on synthetic LLM mutations | `SBG_PROJECT_DISJOINT_VALIDATION.csv` | In SeqCoBench ($e\le 2$), static token bags reach AUROC 0.8240 ($\Delta=+0.0070$) | **CONTRADICTED (NARROWED)** |
| **CLM-06** | Historical QuixBugs below-chance AUROC (0.3587) was a representation failure | `QUIXBUGS_FORENSIC_AUDIT.md` | Caused by harness input serialization crashing 27/40 programs at line 1 | **CONTRADICTED (REFUTED)** |
| **CLM-07** | BugsInPy failure (AUROC 0.4099) proves SBG cannot model Python defects | `SBG_BUGSINPY_FAILURE_ANALYSIS.md` | Caused by dummy inputs failing to activate defect paths (34/47 crashed) | **CONTRADICTED (REFUTED)** |
| **CLM-08** | Synthetic V10 demonstrates large incremental predictive value | `V10_INDEPENDENT_EVALUATION.json` | Execution features reach AUROC 0.7908; incremental value is $\Delta = +0.0063$ | **PARTIALLY VERIFIED (BOUNDED)** |

---

## 2. Definitive Manuscript Guidance

1. Claims **CLM-01**, **CLM-02**, and **CLM-03** are fully supported by empirical evidence and form the primary contributions of the manuscript.
2. Broad superiority claims (**CLM-04**, **CLM-05**) must be explicitly narrowed to identify the exact regime where SBG adds value: subtle algorithmic logic defects where static and execution-volume statistics are uninformative.

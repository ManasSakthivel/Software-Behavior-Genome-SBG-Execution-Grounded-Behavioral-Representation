# SBG REVISED RESEARCH QUESTIONS & EXPERIMENTAL HYPOTHESES

**Date:** 2026-11-16  
**Auditor/Author:** Principal Empirical Software Engineering Scientist  
**Target:** IEEE Access Pre-Submission Rigour

---

## 1. Research Question Formulation

We formulate three scientifically grounded, mutually non-redundant research questions:

### **RQ1 (Representation Fidelity & Structural Inversion):**
> *Does dynamic behavioural genome extraction capture runtime semantics that overcome the structural-semantic inversion observed in conventional static and syntactic representations?*

- **Hypothesis $H_{1}$:** Dynamic genome representations achieve an $\text{AUROC} > 0.70$ on semantics-preserving vs semantics-changing program pairs, whereas static structural representations (Token, AST, TF-IDF) perform near or below chance ($\text{AUROC} \le 0.55$).
- **Independent Variable:** Representation category (Static AST / Token / TF-IDF vs Dynamic Topology, Temporal, State, Composite SBG $V_5$).
- **Dependent Variable:** Pairwise semantic equivalence classification discrimination ($\text{AUROC}$, $\text{AUPRC}$).
- **Control Variables:** Fixed test input battery, identical program pairs, project-disjoint splits, output-free execution protocol.

---

### **RQ2 (Incremental Predictive Value beyond Progressively Stronger Baselines):**
> *Does multi-dimensional behavioural trace alignment provide statistically significant incremental predictive power when added to progressively stronger conventional baselines (code-edit size, execution statistics, and non-linear combiners)?*

- **Hypothesis $H_{2a}$ (Edit-size increment):** Adding SBG $V_5$ to static code-edit distance significantly improves AUROC ($\Delta\text{AUROC} > 0$, 95% CI excludes 0).
- **Hypothesis $H_{2b}$ (Execution-statistics increment):** Adding SBG $V_5$ to a baseline model comprising edit size and scalar execution statistics ($\text{LR(EX)}$) produces no statistically significant gain ($\Delta\text{AUROC} \approx 0$, 95% CI spans 0, $p > 0.05$).
- **Hypothesis $H_{2c}$ (Non-linear baseline superiority):** A non-linear decision tree ensemble trained strictly on execution statistics and edit size (`RF_d4_EXx`) outperforms the full composite SBG $V_5$ distance metric.
- **Independent Variable:** Feature set configuration ($\text{Edit}$, $\text{ExecStats}$, $\text{SBG } V_5$, $\text{ExecStats} + \text{SBG } V_5$, $\text{RF(ExecStats + Edit)}$).
- **Dependent Variable:** $\text{AUROC}$, paired $\Delta\text{AUROC}$, 95% cluster-bootstrap confidence interval, permutation $p$-value.
- **Control Variables:** Identical base programs, identical train/dev/val/test splits, fixed random seeds (`PYTHONHASHSEED=0`).

---

### **RQ3 (Generalization Boundaries across Benchmark Types and Real-World Defects):**
> *Under what benchmark conditions does dynamic behavioural representation maintain discriminative utility, and what are its generalization limits on independent, real-world software defects?*

- **Hypothesis $H_{3}$:** SBG demonstrates high discrimination on synthetic mutation benchmarks with controlled test harness coverage ($\text{AUROC} \ge 0.85$), but degrades to random chance ($\text{AUROC} \approx 0.50$) on real-world defect benchmarks (e.g., BugsInPy, QuixBugs) due to test harness sparsity and execution crash dominance.
- **Independent Variable:** Benchmark source and defect nature (Synthetic Transformation Benchmark $V_{10}$ vs Real-World Defect Suites: BugsInPy, QuixBugs, Defects4J).
- **Dependent Variable:** Discrimination performance ($\text{AUROC}$, $\text{AUPRC}$, zero-score fraction, crash rate).
- **Control Variables:** Output-free execution protocol, execution sandbox budget (5 runs, 5000 events, 1.0s timeout).

---

## 2. Compatibility & Alignment Attestation

All three research questions map directly onto the frozen repository artifacts:
- **RQ1** is addressed by `SBG/artifacts/phase4/` and `IEEE_ACCESS_PRE_SUBMISSION/WP_A_B_COMPARATIVE_BENCHMARK/`.
- **RQ2** is addressed by `IEEE_ACCESS_PRE_SUBMISSION/05_COMPARATIVE_EVALUATION_RESULTS.md` and `EXP-A4R-001/VERIFIED_BASELINES.json`.
- **RQ3** is addressed by `IEEE_ACCESS_PRE_SUBMISSION/WP_D_EXTERNAL_VALIDATION/` and `SBG_BENCHMARK_ACQUISITION.md`.

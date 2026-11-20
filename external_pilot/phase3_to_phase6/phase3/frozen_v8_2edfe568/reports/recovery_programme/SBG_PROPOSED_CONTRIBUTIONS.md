# SBG PROPOSED SCIENTIFIC CONTRIBUTIONS

**Date:** 2026-11-16  
**Auditor/Author:** Principal Empirical Software Engineering Scientist  
**Standard:** IEEE Access Defensible Contribution Framework

---

## 1. Primary Scientific Contributions

The revised SBG research manuscript delivers three defensible contributions to empirical software engineering and dynamic program analysis:

### Contribution 1 (Empirical Discovery & Inversion Diagnosis):
> **Empirical Characterization of the Structural-Semantic Inversion & Confounding in Program Equivalence Benchmarks.**  
> We empirically demonstrate that static code representations (AST, tokens, TF-IDF, compiler equivalence) fail systematically at semantic equivalence discrimination ($\text{AUROC} \le 0.55$) because valid refactorings induce larger syntactic changes than defect-inducing mutations. Furthermore, we expose and quantify an edit-size and execution-volume confound in benchmark construction where trivial predictors reach deceptive AUROCs ($>0.87$) if not rigorously controlled.

### Contribution 2 (Multi-Dimensional Genome Formulation & Ablation Insights):
> **Formal Design, Implementation, and Component Ablation of a Dynamic Behavioral Genome.**  
> We design and implement an output-free, rename-invariant dynamic instrumentation architecture that captures call topology ($V_3$), temporal event sequence alignment ($V_5\text{ temporal}$), and local variable state transition entropy ($V_5\text{ state}$). Through extensive component ablation on 19 base programs (638 pairs), we show that local state transition entropy alone ($\text{AUROC } 0.9171$) outperforms multi-dimensional fusion ($\text{AUROC } 0.8968$), demonstrating that naive feature concatenation across behavioral axes introduces discriminative noise.

### Contribution 3 (Rigorous Baseline Evaluation & Incremental Value Boundary):
> **Definitive Incremental Value Evaluation and Real-World Generalization Boundaries.**  
> Under a preregistered, frozen evaluation protocol, we compare SBG against seven competitor baseline families (Value Spectra, Path Spectra, Dynamic Birthmarks, AST Edit Distance, Linear Combiners, Decision Tree Ensembles, and Independent Output Differencing). We prove that while SBG strongly outperforms static edit size ($+0.281$), it provides zero statistically significant incremental predictive value beyond scalar execution counters and edit size ($\Delta\text{AUROC} = +0.0014$, $p=0.914$). Finally, we delineate the practical boundary of dynamic trace alignment, showing why it struggles on sparse real-world bug test suites (BugsInPy $\text{AUROC } 0.497$, QuixBugs $\text{AUROC } 0.444$).

---

## 2. Explicit Boundary: What SBG Does NOT Claim

To ensure absolute scientific integrity and defensibility before peer reviewers:
1. We **do not** claim that SBG establishes a new state-of-the-art model for commercial defect prediction.
2. We **do not** claim that SBG replaces machine learning tree ensembles trained on execution counters (`RF_d4_EXx` achieves AUROC 0.9552).
3. We **do not** claim cross-language portability between Python and Java as a proven result without large-scale multi-project multilingual evaluation.
4. We **do not** conceal the null incremental value finding; rather, we treat it as an essential empirical finding that guides future program representation research.

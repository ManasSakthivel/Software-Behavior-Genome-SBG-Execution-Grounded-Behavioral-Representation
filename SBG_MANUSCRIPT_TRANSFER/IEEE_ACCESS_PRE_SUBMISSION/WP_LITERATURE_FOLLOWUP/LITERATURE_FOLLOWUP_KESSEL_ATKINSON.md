# LITERATURE FOLLOWUP: Kessel & Atkinson (2019) vs. SBG

**Investigation Date:** 2026-11-14  
**Investigator:** WP-LITERATURE-FOLLOWUP  
**Target Work:** Marcus Kessel & Colin Atkinson, *"On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence"*, 19th IEEE International Working Conference on Source Code Analysis and Manipulation (SCAM 2019), pp. 193–203.

---

## 1. Verified Bibliographic Metadata & DOI Verification

| Attribute | Verified Value | Status / Evidence Source |
|---|---|---|
| **Title** | *On the Efficacy of Dynamic Behavior Comparison for Judging Functional Equivalence* | Verified (Crossref, DBLP `conf/scam/Kessel019a`, S2 `dcc79b26...`) |
| **Authors** | Marcus Kessel, Colin Atkinson | Verified (University of Mannheim, Software Engineering Group) |
| **Venue** | 2019 19th IEEE International Working Conference on Source Code Analysis and Manipulation (SCAM 2019) | Verified |
| **Dates / Location** | September 30 – October 1, 2019, Cleveland, Ohio, USA | Verified (IEEE Xplore) |
| **Pages** | pp. 193–203 | Verified (Crossref, IEEE Xplore) |
| **DOI** | `10.1109/SCAM.2019.00030` | **Verified Correct** (Resolves to IEEE Xplore: `https://doi.org/10.1109/SCAM.2019.00030`) |
| **Repository Error / DOI Collision** | `10.1109/SCAM.2019.00019` was cited in some early repo notes. | **Identified Correction:** `10.1109/SCAM.2019.00019` is Nicolas Harrand et al., *"The Strengths and Behavioral Quirks of Java Bytecode Decompilers"*. The correct DOI for Kessel & Atkinson is `10.1109/SCAM.2019.00030`. |
| **Access Level** | **ABSTRACT-ONLY** (Primary paper); **FULL-TEXT-READ** for author's PhD thesis (2023) and related CC-BY / Open Access publications | IEEE Xplore closed/paywalled; Unpaywall `is_oa=false`. Full context obtained from Kessel's 2023 PhD Dissertation (*LASSO – an observatorium...*, MADOC 64107, 342 pp.), JSS 2024, and FSE 2026. |

---

## 2. Textual Claims Supported by Evidence vs. Unsupported Repo Statements

### A. Supported by Direct Evidence (Abstract + Author's 2023 PhD Thesis)
1. **Core Problem Studied:** Behavior sampling (first proposed by Podgurski & Pierce in 1992) for judging whether software implementations are functionally equivalent by observing output responses to shared test stimuli.
2. **Prior Art Finding Challenged:** Podgurski & Pierce's 1992 study suggested that $k=4$ randomly generated tests achieved $\approx 85\%$ accuracy in recognizing non-equivalence.
3. **K&A 2019 Empirical Finding:** In a much larger empirical study on Java classes/methods, at least **$k \ge 39$ randomly generated tests** are necessary to reach an $85\%$ recognition rate for non-equivalence, but significantly fewer tests are needed when using coverage-based / goal-driven test generation heuristics (e.g. EvoSuite).
4. **Underlying Platform:** The LASSO observatorium, which executes stimulus sequences against candidate software components and records serialized response values into a Stimulus-Response Matrix (SRM).
5. **Decision Criterion:** Strict functional equivalence is judged based on identical serialized return values / observable outputs across all sampled inputs ($S_1 \dots S_x$). For graded similarity (thesis §11.2), string distances over output logs are calculated.

### B. Repo Statements That Were Unsubstantiated or Inaccurate
* *Repo Claim:* "Kessel & Atkinson do not report AUROC or graded distance metrics."  
  *Evidence Check:* **Unverified from SCAM 2019 primary text** (abstract reports % recognition vs test budget). Thesis §11.2 does discuss distance matrices over outputs, but SCAM 2019 was focused on the test count threshold for binary equivalence detection.
* *Repo Claim:* "SBG is the first to compare runtime behaviors of independent implementations."  
  *Evidence Check:* **CONTRADICTED**. Kessel & Atkinson (and Podgurski & Pierce 1992) explicitly compare distinct, independently developed implementations of matching interfaces from open-source repositories using dynamic behavior sampling.

---

## 3. Technical Comparison: Kessel & Atkinson vs. SBG

| Dimension | Kessel & Atkinson (2019) / LASSO Framework | SBG (Software Behavioral Genome) |
|---|---|---|
| **Target Language** | Java (classes/methods harvested from Maven Central / GitHub) | Python (composed variants and standalone benchmark functions) |
| **Observation Mechanism** | **Output-Reading:** Serialized return values / stdout responses to common test stimuli (Stimulus-Response Matrix). | **Output-Free / Trace-Based:** Execution trace events (call frequency, call order bigrams, exception sets, abstracted variable state transitions). Return values intentionally ignored in V5 distance. |
| **Input Generation** | Automated unit test generation (Randoop random testing vs. EvoSuite coverage-driven heuristics). | Fixed synthetic canonical battery (11 inputs per type signature). |
| **Equivalence Task** | Functional equivalence / non-equivalence detection across heterogeneous candidate implementations. | CHANGED vs. EQUIVALENT pairwise classification between program versions / mutants. |
| **Decision Rule / Metric** | Binary output equality across tests (or percentage of distinguishing tests); string edit distance on output logs. | Normalized composite multi-dimensional distance $d(P_A, P_B) \in [0, 1]$ evaluated via AUROC and thresholded Youden $J$. |
| **Sensitivity to Internal Execution Paths** | **Black-Box:** Blind to internal execution paths if two different algorithms produce the same output on all sampled inputs. | **White-Box Trace:** Sensitive to internal call sequences and state transformations even when outputs are identical. |

---

## 4. Methodological Implications for the SBG Benchmark

1. **Label-Tautology Distinction:** Kessel & Atkinson's approach relies on output observation. On the SBG benchmark, where ground-truth labels are defined by output differences on the protocol's 11 inputs, an output-reading comparator is **tautological** (it recovers the ground-truth label by definition). SBG must position itself as an *internal execution-trace representation* that operates without reading outputs.
2. **Fair Baseline Construction:** Any Kessel-style comparator ported to the SBG benchmark must be evaluated either on an *independent input battery* (e.g., 40 independent inputs generated separately) or explicitly documented as an *oracle-ceiling baseline* rather than a fair blind competitor.

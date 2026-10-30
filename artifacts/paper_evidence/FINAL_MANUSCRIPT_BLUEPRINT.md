# Final manuscript blueprint (FINAL SPRINT, Part 6D)

Status: outline and claim control for the drafting agent. It is not a draft paper. Every number is traceable to
`CLAIM_TO_EVIDENCE_MATRIX.md`. V10 = 19 held-out programs, same author and generation procedure as development.

## 1. Proposed title (no unsupported claims)

**"How Much Does a Trace-Derived Behavioural Representation Add? A Size-Aware, Oracle-Validated Evaluation of Behaviour-Change Detection in Python Programs"**

(Alternative: "Edit Size, Execution Statistics, and Behavioural Change: A Controlled Evaluation of Trace-Based Program Comparison".)
Do not use: "novel", "framework", "genome" in the title as an implied biological/algorithmic breakthrough, "detecting bugs".

## 2. Problem statement (one paragraph)

Deciding whether a source change alters what a program does is routinely approximated by the size of the textual edit,
yet synthetic evaluation sets in which labels are tied to transformation families can be solved by edit size alone: on
our first benchmark an edit-size-only predictor reached AUROC 0.876 (reversed). We ask how much of the signal in a
trace-derived behavioural distance survives once the edit-size confound is removed, and how much is explained by
cheaper execution statistics computed from the same traces. We construct size-aware, dynamic-oracle-validated
evaluation sets and evaluate a structured, rename-invariant, output-free trace representation (SBG) with preregistered,
multiplicity-corrected tests.

## 3. Contribution bullets (3–5)

Exactly as in `FINAL_NOVELTY_POSITION.md` §6 (size-aware evaluation design; the SBG representation; evidence beyond edit size;
the strong-baseline negative result; the characterised failure profile).

## 4. Abstract — permitted claims

1. Edit size alone can solve a transformation-family benchmark (reversed-edit AUROC 0.876); a composed pairing with oracle-validated labels reduces forward edit-size AUROC to 0.616.
2. On 19 held-out programs (638 pairs; same author and procedure as development) SBG V5 reaches AUROC 0.897 [0.863, 0.922], +0.254 over edit size (Holm-corrected), and 0.875 with edit size exactly matched.
3. **Adding SBG to edit size plus execution statistics gives no statistically established gain** (+0.006, 95 % CI [−0.069, +0.068]; second dataset +0.021 [−0.005, +0.048]); with in-distribution refit execution statistics alone reach 0.885 (exploratory).
4. SBG cannot detect value-only changes (SC-6: 73.9 % invisible) and does not transfer to real-bug corpora (AUROC ≈ 0.4–0.5).

The abstract must contain the null (item 3) and the limitation (item 4). It must not contain: "outperforms execution statistics", "detects bugs", "generalises", "first", "novel framework", COBOL.

## 5. Section outline

1. **Introduction** — motivation (edit-size proxies), research questions RQ1–RQ4, contributions.
2. **Related work** — behaviour sampling & equivalence by testing (Podgurski & Pierce; Jiang & Su; Kessel & Atkinson), differential/behavioural regression testing (Evans & Savoia; Jin et al.; Person et al.), DCI (Danglot et al.), mutation validity (Just et al.; Ojdanić et al.), benchmark validity (Krinke & Ragkhitwetsagul; Yu et al.), learned execution representations (TRACED), LLM equivalence (EquiBench). State plainly: dynamic comparison is not new. **Blocker: read Kessel & Atkinson full text first.**
3. **Representation** — tracer, abstract value domain, rename-invariant function indices, V3/temporal/state components, V5 weights (0.50/0.25/0.25, fixed); output-free guarantee (SAFEGUARD-2).
4. **Evaluation design** — SP/SC transformation families; dynamic-oracle label validation (equivalence on protocol inputs); composed pairing; edit-size diagnosis (V8); splits (v9c train/val, V10) and what "held-out" means; baselines (edit, static AST/token, each execution statistic, learned `M_E`, `M_X`, `M_EX`); preregistered hypotheses H1–H6; statistics (program-clustered paired bootstrap, Holm).
5. **Results** — RQ1 vs edit size (H2, H3, stratified); RQ2 vs edit+execution statistics (H4 null, prominent); RQ3 V6 vs V5 (H5); components.
6. **Analysis** — exploratory (labelled): family-level concordance; LOPO refit; redundancy; case studies (Cases 1–4 incl. failure); review-effort curves.
7. **Discussion** — what the representation encodes; why the increment is small (overlap + combiner transfer + wide CI); proposed use case (triage of transformations) **as proposed**; relation to output-based differential testing.
8. **Threats to validity** — §8 below.
9. **Limitations and future work** — §9.
10. **Conclusion.**

## 6. Figures and tables

| ID | Content | Source | Status |
|---|---|---|---|
| Table 1 | Benchmarks and splits (programs, pairs, matched sets, mean edit CHANGED vs EQUIVALENT) | `V10_INDEPENDENT_EVALUATION.json`, `V9_VAL_EVALUATION.json` | frozen |
| Table 2 | AUROC [CI] for edit, `M_X`, `M_EX`, SBG V5/V6, `M_E+V5`, `M_EX+V5` | same | frozen |
| Table 3 | Pre-declared deltas H2–H6 with Holm | same | frozen |
| Fig. 1 | Forest plot of paired deltas (H2, H3, H4, H5; LOPO increment) | + `INCREMENTAL_CONTRIBUTION_ANALYSIS_lopo.json` | frozen + exploratory (marked) |
| Fig. 2 | Edit-size confound: V8 reversed-edit vs composed V10 forward-edit AUROC; edit distribution by label | `DIAGNOSTIC_EDIT_SIZE.json`, V10 | frozen |
| Table 4 | Exact-edit-stratified AUROC and window sweep | `INCREMENTAL_CONTRIBUTION_ANALYSIS_main.json` | exploratory |
| Table 5 | Family-level concordance (SBG vs `M_EX` vs edit) incl. SC-6, SP-2, SP-8 losses | same | exploratory |
| Table 6 | Case summary (Cases 1–4, including 3 and 4a) | `REPRESENTATION_CASE_STUDIES.md` | qualitative |
| Fig. 3 | State-transition multiset diff for Case 1 and Case 2 | `REPRESENTATION_CASES_traces.json` | qualitative |
| Fig. 4 | Review fraction vs recall (SBG, edit, `M_EX`) | `PRACTICAL_SIGNIFICANCE_ANALYSIS.json` | exploratory, prevalence 50 % |
| Table 7 | Component AUROCs (V9c-val, V10) | frozen evaluations | frozen |
| Table 8 | Real-bug transfer (BugsInPy, QuixBugs; all and excl. SP-2) | `EXTERNAL_RESCORE_V8.json` | frozen |

## 7. Where to place the null and COBOL

* **Null (H4):** Abstract (one sentence), Results §5 (own subsection, own row in Table 3, CI shown), Discussion (why small), Conclusion.
  Never only in limitations.
* **COBOL:** not in the main paper; one sentence in Limitations/Future work ("the implementation is Python-specific; a locally available COBOL corpus contained Db2 precompiler test snippets and could not be used"). No appendix.

## 8. Threats to validity

* **Construct:** labels = equivalence on 11 synthesised inputs, not semantic equivalence; SC mutations may not resemble real faults (Just et al.; BugsInPy/QuixBugs null).
* **Internal:** edit size not fully removed (92 % of V10 sets have the larger edit in the CHANGED variant); combiner trained on v9c train and applied to V10 does not transfer; LOPO refit mitigates but is exploratory.
* **External:** V10 shares author and generator with development; 19 programs; Python only; algorithmic programs from one corpus.
* **Statistical:** H4 CIs leave increments ≲ 0.05–0.07 open; many exploratory comparisons uncorrected; H5 raw CI excludes 0 but Holm does not reject.
* **Conclusion validity of the null:** a null is not equivalence.
* **Tooling:** `sys.settrace`, CPython 3.13 sensitivity (documented in `docs/current/PYTHON_VERSIONS.md`).

## 9. Limitations and future work (classified)

* Limitations: as §8, plus the output-free blind spot (SC-6 73.9 %), SP-2/SP-8 false-negative/false-positive families, no output-based differential-testing baseline, no real-world version pairs.
* Future (optional): independently authored programs; human- or LLM-generated refactorings with oracle labels; leave-one-component-out ablation; comparison with output-based differential testing; another language with an executable corpus and regression suites.

## 10. Pre-submission checklist — numbers and claims to re-verify

| # | Item | Expected | Check against |
|---|---|---|---|
| 1 | V9c-val SBG V5 AUROC | 0.751 [0.706, 0.794] | `V9_VAL_EVALUATION.json` |
| 2 | V10 SBG V5 AUROC | 0.897 [0.863, 0.922] | `V10_INDEPENDENT_EVALUATION.json` |
| 3 | V10 composition | 638 pairs, 319 sets, 19 programs | same |
| 4 | Edit AUROC (V10 forward) | 0.616 | same |
| 5 | V8 reversed-edit AUROC | 0.876 | `V8_TEST_EVALUATION.json` |
| 6 | H2 | +0.254 [+0.218, +0.285], Holm p = 0.005 | V10 |
| 7 | H3 | +0.281 [+0.244, +0.308] | V10 |
| 8 | H4 V10 / V9c-val | +0.006 [−0.069, +0.068], Holm 1.0 / +0.021 [−0.005, +0.048], p = 0.117 | both |
| 9 | H5 | +0.0029, raw 0.030, Holm 0.090 (not rejected) | V10 |
| 10 | Stratified AUROC | 0.875 (edit 0.500) | V10 |
| 11 | `M_EX` / `M_X` / `M_EX+V5` | 0.791 / 0.793 / 0.797 | V10 |
| 12 | LOPO `M_EX` / `M_EX+V5` / SBG | 0.885 / 0.895 / 0.897 | `_lopo.json` |
| 13 | SC-6 zero rate | 73.9 % (17/23) | V10 |
| 14 | BugsInPy / QuixBugs | 0.416 → 0.497; 0.384 → 0.444 (all → excl. SP-2) | `EXTERNAL_RESCORE_V8.json` |
| 15 | Component AUROCs | V9c-val 0.762 / 0.751 / 0.740 / 0.619; V10 state 0.917 | frozen |
| 16 | Kessel & Atkinson DOI | 10.1109/SCAM.2019.00030; full text read | doi.org |
| 17 | EquiBench venue | verify or cite arXiv:2502.12466 | arXiv |
| 18 | "V10 is held-out, same author/procedure" wording everywhere | – | all sections |
| 19 | No sentence uses first / novel / unique / real bugs / beyond execution statistics / V6 better / COBOL | – | text search |
| 20 | Frozen hashes unchanged | `EXPERIMENT_MANIFEST_V4.json` | `consistency_check.py` C9 |
